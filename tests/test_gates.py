import shutil
import tempfile
import unittest
from pathlib import Path

from harness.core.gates import (
    GateRunner,
    QualityGate,
    ArchiveGuard,
    ArchiveBlockedError,
)


class TestQualityGates(unittest.TestCase):
    def setUp(self):
        self.temp_dir = Path(tempfile.mkdtemp())
        self.change_dir = self.temp_dir / "openspec" / "changes" / "ch-gates-01"
        self.change_dir.mkdir(parents=True, exist_ok=True)
        self.runner = GateRunner(project_root=self.temp_dir)
        self.guard = ArchiveGuard(project_root=self.temp_dir)

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def _setup_valid_openspec(self, with_red_evidence: bool = True):
        # 1. proposal.md
        (self.change_dir / "proposal.md").write_text(
            """# Proposta
## Contexto
Contexto.
## Problema
Problema.
## Escopo
Escopo.
## Fora de Escopo
Fora de escopo.
## Riscos
Riscos.
## Critérios de Aceite
Critérios.
""",
            encoding="utf-8",
        )

        # 2. specs/
        specs_dir = self.change_dir / "specs"
        specs_dir.mkdir(exist_ok=True)
        (specs_dir / "spec.md").write_text(
            """Given setup\nWhen action\nThen result\n""",
            encoding="utf-8",
        )

        # 3. test-plan.md
        red_text = "- Status: RED (AssertionError: expected False to be True)" if with_red_evidence else "- Status: Pending"
        (self.change_dir / "test-plan.md").write_text(
            f"""# Plano de Testes
## Mapeamento Requisito -> Teste
- Req -> test_1
## Evidência de Teste RED
{red_text}
""",
            encoding="utf-8",
        )

        # 4. tasks.md
        (self.change_dir / "tasks.md").write_text(
            """# Tarefas
- [ ] Task 1 (1h)
""",
            encoding="utf-8",
        )

    def test_h0_gate_passes_for_valid_change(self):
        self._setup_valid_openspec(with_red_evidence=True)
        res = self.runner.run_h0("ch-gates-01")
        self.assertTrue(res.passed)

    def test_t1_gate_requires_red_evidence(self):
        self._setup_valid_openspec(with_red_evidence=False)
        res = self.runner.run_t1("ch-gates-01")
        self.assertFalse(res.passed)

        self._setup_valid_openspec(with_red_evidence=True)
        res2 = self.runner.run_t1("ch-gates-01")
        self.assertTrue(res2.passed)

    def test_archive_guard_blocks_without_red_or_green(self):
        self._setup_valid_openspec(with_red_evidence=False)
        with self.assertRaises(ArchiveBlockedError):
            self.guard.assert_ready_to_archive("ch-gates-01")

    def test_archive_guard_passes_when_all_gates_met(self):
        self._setup_valid_openspec(with_red_evidence=True)
        # Cria um diretório de testes simples que passa para T2
        tests_dir = self.temp_dir / "tests"
        tests_dir.mkdir(exist_ok=True)
        (tests_dir / "test_dummy.py").write_text(
            "import unittest\nclass DummyTest(unittest.TestCase):\n    def test_ok(self): self.assertTrue(True)\n",
            encoding="utf-8",
        )

        bundle = self.guard.assert_ready_to_archive("ch-gates-01")
        self.assertTrue(bundle.overall_passed)
        self.assertTrue(len(bundle.sha256) == 64)


if __name__ == "__main__":
    unittest.main()
