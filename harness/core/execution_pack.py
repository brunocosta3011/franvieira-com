"""
Execution Pack para Harness v2.3
Versionamento de pacotes de execução, restrição de paths por papel e detecção de obsolescência.
"""
from dataclasses import dataclass, field
from datetime import datetime, timezone
import fnmatch
import json
from pathlib import Path
from typing import Any, Dict, List, Optional


class StalePackError(Exception):
    """Lançada quando um Execution Pack se torna obsoleto perante o estado atual."""
    pass


ROLE_ALLOWED_PATHS: Dict[str, List[str]] = {
    "spec_writer": [
        "openspec/changes/*",
        "openspec/schemas/*",
        "openspec/project.yaml",
    ],
    "test_engineer": [
        "tests/*",
        "openspec/changes/*",
        "openspec/project.yaml",
    ],
    "implementer": [
        "harness/*",
        "scripts/*",
        "tests/*",
        "openspec/changes/*",
        "openspec/archive/*",
        "*.html",
        "*.js",
        "*.css",
        "*.json",
        "*.md",
        "assets/*",
        "temas/*",
        "comunidade-aplique/*",
        "linktree/*",
        "secagem-profissional/*",
        "docs/*",
    ],
    "reviewer": [
        "openspec/changes/*",
        "openspec/archive/*",
        "tests/*",
        "*.md",
    ],
    "universal": [
        "*",
    ],
}


@dataclass
class ExecutionPack:
    pack_id: str
    change_id: str
    version: int
    role: str
    target_tasks: List[str]
    allowed_paths: List[str]
    context_pack_id: str
    base_state: str
    base_hash: str
    created_at: str
    metadata: Dict[str, Any] = field(default_factory=dict)

    def is_path_allowed(self, path: str) -> bool:
        norm_path = path.replace("\\", "/").lstrip("./")
        for pattern in self.allowed_paths:
            pattern = pattern.replace("\\", "/").lstrip("./")
            if fnmatch.fnmatch(norm_path, pattern):
                return True
            if pattern.endswith("/*"):
                base_dir = pattern[:-2]
                if norm_path == base_dir or norm_path.startswith(base_dir + "/"):
                    return True
        return False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "pack_id": self.pack_id,
            "change_id": self.change_id,
            "version": self.version,
            "role": self.role,
            "target_tasks": self.target_tasks,
            "allowed_paths": self.allowed_paths,
            "context_pack_id": self.context_pack_id,
            "base_state": self.base_state,
            "base_hash": self.base_hash,
            "created_at": self.created_at,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ExecutionPack":
        return cls(**data)


class ExecutionPackManager:
    def __init__(self, project_root: Optional[str | Path] = None):
        self.root = Path(project_root) if project_root else Path.cwd()
        self.packs_dir = self.root / ".harness" / "packs"
        self.packs_dir.mkdir(parents=True, exist_ok=True)

    def create_pack(
        self,
        change_id: str,
        role: str,
        target_tasks: List[str],
        context_pack_id: str,
        base_state: str,
        base_hash: str,
        custom_allowed_paths: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> ExecutionPack:
        allowed = (
            list(custom_allowed_paths)
            if custom_allowed_paths is not None
            else list(ROLE_ALLOWED_PATHS.get(role, ROLE_ALLOWED_PATHS["universal"]))
        )

        # Encontra próxima versão
        existing = list(self.packs_dir.glob(f"{change_id}_v*.json"))
        version = len(existing) + 1
        pack_id = f"ep-{change_id}-v{version}"
        created_at = datetime.now(timezone.utc).isoformat()

        pack = ExecutionPack(
            pack_id=pack_id,
            change_id=change_id,
            version=version,
            role=role,
            target_tasks=target_tasks,
            allowed_paths=allowed,
            context_pack_id=context_pack_id,
            base_state=base_state,
            base_hash=base_hash,
            created_at=created_at,
            metadata=metadata or {},
        )

        pack_file = self.packs_dir / f"{change_id}_v{version}.json"
        pack_file.write_text(json.dumps(pack.to_dict(), indent=2, ensure_ascii=False), encoding="utf-8")
        return pack

    def get_latest_pack(self, change_id: str) -> Optional[ExecutionPack]:
        existing = sorted(self.packs_dir.glob(f"{change_id}_v*.json"))
        if not existing:
            return None
        latest = existing[-1]
        data = json.loads(latest.read_text(encoding="utf-8"))
        return ExecutionPack.from_dict(data)

    def check_freshness(
        self,
        pack: ExecutionPack,
        current_state: str,
        current_hash: Optional[str] = None,
    ) -> None:
        """
        Verifica se o pacote é válido em relação ao estado atual da change.
        """
        if pack.base_state != current_state:
            raise StalePackError(
                f"Execution Pack '{pack.pack_id}' está obsoleto! "
                f"Base state: {pack.base_state}, Estado atual: {current_state}."
            )

        if current_hash is not None and pack.base_hash and pack.base_hash != current_hash:
            raise StalePackError(
                f"Execution Pack '{pack.pack_id}' está obsoleto! "
                f"Hash base ({pack.base_hash[:8]}) diverge do hash atual ({current_hash[:8]})."
            )

        latest = self.get_latest_pack(pack.change_id)
        if latest and latest.version > pack.version:
            raise StalePackError(
                f"Execution Pack '{pack.pack_id}' foi superado pela versão v{latest.version}."
            )
