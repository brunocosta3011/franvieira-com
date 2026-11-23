"""
Interactive Agent Adapter para Antigravity IDE no Harness v2.3
Gera instruções operacionais e valida escopo estrito de diff contra allowed_paths.
"""
from pathlib import Path
import subprocess
from typing import Any, Dict, List, Optional

from harness.adapters.base import AgentCapabilities, BaseAgentAdapter, CollectionBundle
from harness.core.context_pack import ContextPack
from harness.core.execution_pack import ExecutionPack


class ScopeViolationError(Exception):
    """Lançada quando modificações violam os allowed_paths do Execution Pack."""
    pass


class InteractiveAgentAdapter(BaseAgentAdapter):
    def __init__(self, project_root: Optional[str | Path] = None):
        super().__init__(project_root)
        self.instructions_dir = self.root / ".harness" / "instructions"
        self.instructions_dir.mkdir(parents=True, exist_ok=True)

    def get_capabilities(self) -> AgentCapabilities:
        return AgentCapabilities(
            interactive=True,
            headless=False,
            supports_streaming=True,
            supports_tools=True,
            supports_subagents=True,
        )

    def generate_instructions(self, execution_pack: ExecutionPack, context_pack: ContextPack) -> Path:
        """
        Gera o artefato INSTRUCTIONS.md para guiar o agente interativo na IDE.
        """
        instr_file = self.instructions_dir / f"{execution_pack.pack_id}.md"

        tasks_md = "\n".join(f"- [ ] {t}" for t in execution_pack.target_tasks)
        allowed_md = "\n".join(f"- `{p}`" for p in execution_pack.allowed_paths)
        files_md = "\n".join(f"- `{f.relative_path}` ({f.estimated_tokens} tokens)" for f in context_pack.files)

        content = f"""# Instruções Operacionais Harness v2.3 - Antigravity IDE

## Pacote de Execução: `{execution_pack.pack_id}`
- **Change ID:** `{execution_pack.change_id}`
- **Papel Alocado:** `{execution_pack.role}`
- **Context Pack SHA-256:** `{context_pack.sha256[:16]}...`
- **Estado Base:** `{execution_pack.base_state}`

---

## ⚠️ Regras Estritas de Governança SDD/TDD
1. **Ciclo TDD:** Nunca crie código de produção sem antes registrar e executar um teste em estado **RED** (comprovando falha esperada).
2. **Escopo Restrito:** Apenas arquivos dentro dos `allowed_paths` podem ser modificados. Qualquer alteração externa abortará a execução por violação de escopo.
3. **Lease Ativo:** Assegure que o lease do workspace esteja em vigor durante toda a sessão.

---

## 🎯 Tarefas Alvo Desta Etapa
{tasks_md}

---

## 🔒 Caminhos Permitidos (Allowed Paths)
{allowed_md}

---

## 📦 Arquivos Empacotados no Context Pack
{files_md}
"""
        instr_file.write_text(content, encoding="utf-8")
        return instr_file

    def get_modified_files(self) -> List[str]:
        """Obtém arquivos modificados e não rastreados no git."""
        try:
            res = subprocess.run(
                ["git", "status", "--porcelain"],
                cwd=str(self.root),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                check=True,
            )
            files = []
            for line in res.stdout.splitlines():
                line = line.strip()
                if line:
                    # status tem 2 caracteres, depois espaço, depois path
                    parts = line.split(maxsplit=1)
                    if len(parts) == 2:
                        files.append(parts[1].strip())
            return files
        except Exception:
            return []

    def validate_scope(self, execution_pack: ExecutionPack, modified_files: List[str]) -> None:
        """
        Valida se todos os arquivos modificados estão autorizados no Execution Pack.
        """
        violations = []
        for file_path in modified_files:
            # Ignora arquivos de controle interno do próprio harness em .harness/
            norm = file_path.replace("\\", "/").lstrip("./")
            if norm.startswith(".harness/"):
                continue
            if not execution_pack.is_path_allowed(norm):
                violations.append(norm)

        if violations:
            raise ScopeViolationError(
                f"Violação de escopo detectada para o papel '{execution_pack.role}'! "
                f"Arquivos não autorizados alterados:\n" + "\n".join(f"  - {v}" for v in violations)
            )

    def execute(
        self,
        execution_pack: ExecutionPack,
        context_pack: ContextPack,
        timeout_seconds: int = 300,
    ) -> CollectionBundle:
        """
        Execução interativa: gera INSTRUCTIONS.md e valida escopo das modificações atuais.
        """
        instr_path = self.generate_instructions(execution_pack, context_pack)
        modified = self.get_modified_files()
        self.validate_scope(execution_pack, modified)

        return CollectionBundle(
            run_id=f"interactive-{execution_pack.pack_id}",
            adapter_name="interactive",
            exit_code=0,
            files_modified=modified,
            stdout=f"Instruções geradas em {instr_path.relative_to(self.root)}. Escopo validado com sucesso.",
            stderr="",
            metadata={"instructions_file": str(instr_path)},
        )
