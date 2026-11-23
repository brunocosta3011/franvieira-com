"""
OpenSpec Schema Validator para Harness v2.3
Valida artefatos obrigatórios do schema platform-sdd-tdd.
"""
from dataclasses import dataclass, field
from pathlib import Path
import re
from typing import List, Optional
import yaml


@dataclass
class ValidationResult:
    change_id: str
    is_valid: bool
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)

    @property
    def summary(self) -> str:
        status = "PASSED" if self.is_valid else "FAILED"
        msg = f"[{status}] OpenSpec Validation for '{self.change_id}'\n"
        if self.errors:
            msg += "Errors:\n" + "\n".join(f"  - {e}" for e in self.errors) + "\n"
        if self.warnings:
            msg += "Warnings:\n" + "\n".join(f"  - {w}" for w in self.warnings) + "\n"
        return msg


def _has_section(content: str, section_name: str) -> bool:
    # Procura por headers Markdown (# Section, ## Section, etc.) ou seções destacadas
    pattern = rf"(?im)^#+\s+.*{re.escape(section_name)}.*$|\*\*.*{re.escape(section_name)}.*\*\*"
    return bool(re.search(pattern, content))


def validate_change(
    change_dir_or_id: str | Path,
    project_root: Optional[str | Path] = None,
) -> ValidationResult:
    """
    Valida uma change contra o schema platform-sdd-tdd.
    """
    root = Path(project_root) if project_root else Path.cwd()
    target_path = Path(change_dir_or_id)

    if not target_path.is_absolute():
        # Tenta resolver relativo a openspec/changes, openspec/archive ou root
        candidates = [
            root / "openspec" / "changes" / target_path,
            root / "openspec" / "archive" / target_path,
            root / target_path,
        ]
        found = False
        for cand in candidates:
            if cand.exists() and cand.is_dir():
                target_path = cand
                found = True
                break
        if not found:
            # Fallback para o primeiro caminho esperado
            target_path = candidates[0]

    change_id = target_path.name
    errors: List[str] = []
    warnings: List[str] = []

    if not target_path.exists() or not target_path.is_dir():
        return ValidationResult(
            change_id=change_id,
            is_valid=False,
            errors=[f"Diretório da change não encontrado: {target_path}"],
        )

    # 1. Validar proposal.md
    proposal_file = target_path / "proposal.md"
    if not proposal_file.is_file():
        errors.append("Artefato obrigatório ausente: proposal.md")
    else:
        try:
            content = proposal_file.read_text(encoding="utf-8")
            required_sections = [
                "Contexto",
                "Problema",
                "Escopo",
                "Fora de Escopo",
                "Riscos",
                "Critérios de Aceite",
            ]
            for sec in required_sections:
                if not _has_section(content, sec):
                    errors.append(f"proposal.md: Seção obrigatória ausente '{sec}'")
        except Exception as e:
            errors.append(f"Erro ao ler proposal.md: {e}")

    # 2. Validar specs/ (cenários BDD Given/When/Then)
    specs_dir = target_path / "specs"
    if not specs_dir.is_dir():
        errors.append("Diretório obrigatório de especificações ausente: specs/")
    else:
        spec_files = list(specs_dir.glob("*.md")) + list(specs_dir.glob("*.feature"))
        if not spec_files:
            errors.append("specs/: Nenhum arquivo de especificação (.md ou .feature) encontrado")
        else:
            has_bdd_keywords = False
            bdd_given = re.compile(r"(Given|Dado)", re.IGNORECASE)
            bdd_when = re.compile(r"(When|Quando)", re.IGNORECASE)
            bdd_then = re.compile(r"(Then|Então)", re.IGNORECASE)

            for sfile in spec_files:
                try:
                    scontent = sfile.read_text(encoding="utf-8")
                    if (
                        bdd_given.search(scontent)
                        and bdd_when.search(scontent)
                        and bdd_then.search(scontent)
                    ):
                        has_bdd_keywords = True
                        break
                except Exception as e:
                    warnings.append(f"Não foi possível ler {sfile.name}: {e}")

            if not has_bdd_keywords:
                errors.append(
                    "specs/: Nenhuma especificação com cenários BDD válidos (Given/When/Then ou Dado/Quando/Então) encontrada"
                )

    # 3. Validar test-plan.md
    test_plan_file = target_path / "test-plan.md"
    if not test_plan_file.is_file():
        errors.append("Artefato obrigatório ausente: test-plan.md")
    else:
        try:
            tp_content = test_plan_file.read_text(encoding="utf-8")
            if not _has_section(tp_content, "Mapeamento Requisito"):
                errors.append(
                    "test-plan.md: Seção obrigatória ausente 'Mapeamento Requisito -> Teste'"
                )
            if not _has_section(tp_content, "Evidência de Teste RED") and not _has_section(
                tp_content, "Teste RED"
            ):
                errors.append("test-plan.md: Seção obrigatória ausente 'Evidência de Teste RED'")
        except Exception as e:
            errors.append(f"Erro ao ler test-plan.md: {e}")

    # 4. Validar tasks.md
    tasks_file = target_path / "tasks.md"
    if not tasks_file.is_file():
        errors.append("Artefato obrigatório ausente: tasks.md")
    else:
        try:
            tasks_content = tasks_file.read_text(encoding="utf-8")
            if not _has_section(tasks_content, "Tarefas"):
                errors.append("tasks.md: Seção obrigatória ausente 'Tarefas'")

            # Procura por checkboxes de tarefas
            task_items = re.findall(r"\[[ xX]\]\s*([^\n]+)", tasks_content)
            if not task_items:
                errors.append("tasks.md: Nenhuma tarefa declarada no padrão '[ ] Tarefa'")
            else:
                # Checa limite de duração de cada tarefa <= 2h
                duration_pattern = re.compile(r"(\d+(\.\d+)?)\s*(?:h|horas|hrs)", re.IGNORECASE)
                for item in task_items:
                    dur_match = duration_pattern.search(item)
                    if dur_match:
                        dur = float(dur_match.group(1))
                        if dur > 2.0:
                            errors.append(
                                f"tasks.md: Tarefa com estimativa excedendo teto de 2h: '{item.strip()}' ({dur}h)"
                            )
        except Exception as e:
            errors.append(f"Erro ao ler tasks.md: {e}")

    # 5. design.md (opcional / condicional)
    design_file = target_path / "design.md"
    if design_file.exists():
        if not design_file.is_file():
            errors.append("design.md deve ser um arquivo Markdown")
        elif design_file.stat().st_size == 0:
            warnings.append("design.md está vazio")

    is_valid = len(errors) == 0
    return ValidationResult(
        change_id=change_id,
        is_valid=is_valid,
        errors=errors,
        warnings=warnings,
    )
