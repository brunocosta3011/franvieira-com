"""
Context Pack determinístico para Harness v2.3
Monta bundles de contexto seguros com SHA-256, denylist estrita e controle de budget.
"""
from dataclasses import dataclass, field
import fnmatch
import hashlib
from pathlib import Path
from typing import Any, Dict, List, Optional, Set


DEFAULT_DENYLIST: List[str] = [
    ".env*",
    "*.env",
    "*.pem",
    "*.key",
    "*.pkcs12",
    "*.pfx",
    "id_rsa*",
    "id_ed25519*",
    "*credential*",
    "*secret*",
    "*.token",
    ".git/*",
    ".harness/leases/*",
    ".harness/state/*",
    ".harness/events/*",
    "__pycache__/*",
    "*.pyc",
    "node_modules/*",
]


class BudgetExceededError(Exception):
    """Lançada quando o tamanho do Context Pack ultrapassa o orçamento de tokens."""
    pass


@dataclass
class PackedFile:
    relative_path: str
    sha256: str
    size_bytes: int
    estimated_tokens: int
    content: str


@dataclass
class ContextPack:
    pack_id: str
    change_id: str
    sha256: str
    total_tokens: int
    max_budget: int
    files: List[PackedFile] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def get_file(self, path: str) -> Optional[PackedFile]:
        for f in self.files:
            if f.relative_path == path:
                return f
        return None

    def export_summary(self) -> Dict[str, Any]:
        return {
            "pack_id": self.pack_id,
            "change_id": self.change_id,
            "sha256": self.sha256,
            "total_tokens": self.total_tokens,
            "max_budget": self.max_budget,
            "files_count": len(self.files),
            "files": [
                {
                    "path": f.relative_path,
                    "sha256": f.sha256,
                    "estimated_tokens": f.estimated_tokens,
                }
                for f in self.files
            ],
            "metadata": self.metadata,
        }


class ContextPackBuilder:
    def __init__(
        self,
        project_root: Optional[str | Path] = None,
        max_token_budget: int = 64000,
        denylist: Optional[List[str]] = None,
    ):
        self.root = Path(project_root) if project_root else Path.cwd()
        self.max_token_budget = max_token_budget
        self.denylist = list(denylist) if denylist is not None else list(DEFAULT_DENYLIST)
        self.included_paths: Set[str] = set()

    def is_denied(self, rel_path: str) -> bool:
        norm_path = rel_path.replace("\\", "/")
        filename = Path(norm_path).name

        for pattern in self.denylist:
            pattern = pattern.replace("\\", "/")
            if fnmatch.fnmatch(norm_path, pattern):
                return True
            if fnmatch.fnmatch(filename, pattern):
                return True
            if pattern.endswith("/*") and norm_path.startswith(pattern[:-2]):
                return True
        return False

    def estimate_tokens(self, text: str) -> int:
        # Heurística canônica padrão da indústria: ~4 caracteres por token
        return max(1, len(text) // 4)

    def add_file(self, file_path: str | Path) -> bool:
        p = Path(file_path)
        if not p.is_absolute():
            p = self.root / p
        if not p.is_file():
            return False

        try:
            rel = p.relative_to(self.root).as_posix()
        except ValueError:
            rel = p.as_posix()

        if self.is_denied(rel):
            return False

        self.included_paths.add(rel)
        return True

    def add_directory(self, dir_path: str | Path, pattern: str = "*") -> int:
        d = Path(dir_path)
        if not d.is_absolute():
            d = self.root / d
        if not d.is_dir():
            return 0

        added = 0
        for item in sorted(d.rglob(pattern)):
            if item.is_file():
                if self.add_file(item):
                    added += 1
        return added

    def build(self, change_id: str, metadata: Optional[Dict[str, Any]] = None) -> ContextPack:
        packed_files: List[PackedFile] = []
        total_tokens = 0
        hasher = hashlib.sha256()

        # Ordenação determinística para garantir hash reprodutível
        sorted_paths = sorted(self.included_paths)

        for rel in sorted_paths:
            full_path = self.root / rel
            if not full_path.is_file():
                continue

            try:
                content = full_path.read_text(encoding="utf-8")
            except UnicodeDecodeError:
                # Arquivo binário não suportado em context pack texto
                continue

            tokens = self.estimate_tokens(content)
            total_tokens += tokens
            if total_tokens > self.max_token_budget:
                raise BudgetExceededError(
                    f"Orçamento de tokens ({self.max_token_budget}) excedido ao empacotar '{rel}'. "
                    f"Tokens acumulados: {total_tokens}"
                )

            file_hash = hashlib.sha256(content.encode("utf-8")).hexdigest()
            # Alimenta o hash geral de forma ordenada
            hasher.update(f"{rel}:{file_hash}\n".encode("utf-8"))

            packed_files.append(
                PackedFile(
                    relative_path=rel,
                    sha256=file_hash,
                    size_bytes=len(content.encode("utf-8")),
                    estimated_tokens=tokens,
                    content=content,
                )
            )

        pack_hash = hasher.hexdigest()
        pack_id = f"cp-{change_id}-{pack_hash[:12]}"

        return ContextPack(
            pack_id=pack_id,
            change_id=change_id,
            sha256=pack_hash,
            total_tokens=total_tokens,
            max_budget=self.max_token_budget,
            files=packed_files,
            metadata=metadata or {},
        )
