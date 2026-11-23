import shutil
import tempfile
import unittest
from pathlib import Path

from harness.core.validator import validate_change


class TestOpenSpecValidator(unittest.TestCase):
    def setUp(self):
        self.temp_dir = Path(tempfile.mkdtemp())
        self.change_dir = self.temp_dir / "openspec" / "changes" / "ch-01-test"
        self.change_dir.mkdir(parents=True, exist_ok=True)

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def _create_valid_artifacts(self):
        # 1. proposal.md
        (self.change_dir / "proposal.md").write_text(
            """# Proposta
## Contexto
Contexto do projeto.
## Problema
Descrição do problema.
## Escopo
Escopo definido.
## Fora de Escopo
Fora de escopo.
## Riscos
Riscos mapeados.
## Critérios de Aceite
Critérios aceitos.
""",
            encoding="utf-8",
        )

        # 2. specs/
        specs_dir = self.change_dir / "specs"
        specs_dir.mkdir(exist_ok=True)
        (specs_dir / "feature.md").write_text(
            """# Especificação BDD
Given o sistema inicializado
When uma ação ocorre
Then o resultado é esperado
""",
            encoding="utf-8",
        )

        # 3. test-plan.md
        (self.change_dir / "test-plan.md").write_text(
            """# Plano de Testes
## Mapeamento Requisito -> Teste
- Req 1 -> test_req_1
## Evidência de Teste RED
- Status: RED (AssertionError esperado)
""",
            encoding="utf-8",
        )

        # 4. tasks.md
        (self.change_dir / "tasks.md").write_text(
            """# Tarefas
- [ ] Task 1: Criar testes (1h)
- [ ] Task 2: Implementar funcionalidade (1.5h)
""",
            encoding="utf-8",
        )

    def test_valid_change(self):
        self._create_valid_artifacts()
        res = validate_change(self.change_dir, project_root=self.temp_dir)
        self.assertTrue(res.is_valid, msg=f"Deveria ser válido: {res.errors}")
        self.assertEqual(len(res.errors), 0)

    def test_missing_proposal_sections(self):
        self._create_valid_artifacts()
        (self.change_dir / "proposal.md").write_text("# Incompleto\n## Contexto\nSó isso.", encoding="utf-8")
        res = validate_change(self.change_dir, project_root=self.temp_dir)
        self.assertFalse(res.is_valid)
        self.assertTrue(any("Seção obrigatória ausente 'Problema'" in e for e in res.errors))

    def test_missing_bdd_in_specs(self):
        self._create_valid_artifacts()
        (self.change_dir / "specs" / "feature.md").write_text("# Especificação sem BDD\nTexto livre.", encoding="utf-8")
        res = validate_change(self.change_dir, project_root=self.temp_dir)
        self.assertFalse(res.is_valid)
        self.assertTrue(any("cenários BDD válidos" in e for e in res.errors))

    def test_task_exceeding_duration_limit(self):
        self._create_valid_artifacts()
        (self.change_dir / "tasks.md").write_text(
            """# Tarefas
- [ ] Task 1: Criar tudo de uma vez (4h)
""",
            encoding="utf-8",
        )
        res = validate_change(self.change_dir, project_root=self.temp_dir)
        self.assertFalse(res.is_valid)
        self.assertTrue(any("excedendo teto de 2h" in e for e in res.errors))


if __name__ == "__main__":
    unittest.main()
