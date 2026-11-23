import shutil
import tempfile
import unittest
from pathlib import Path

from harness.core.validator import validate_change
from harness.core.state_machine import HarnessStateMachine, HarnessState
from harness.core.lease import WorkspaceLeaseManager, LeaseType
from harness.core.context_pack import ContextPackBuilder
from harness.core.execution_pack import ExecutionPackManager
from harness.core.gates import GateRunner, ArchiveGuard


class TestE2EDogfooding(unittest.TestCase):
    def setUp(self):
        self.temp_dir = Path(tempfile.mkdtemp())
        self.change_id = "h0-00-test-bootstrap"
        self.change_dir = self.temp_dir / "openspec" / "changes" / self.change_id
        self.change_dir.mkdir(parents=True, exist_ok=True)

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_full_lifecycle_e2e(self):
        # 1. Criação dos artefatos OpenSpec canônicos
        (self.change_dir / "proposal.md").write_text(
            """# Proposta de Bootstrap
## Contexto
Estruturação da governança do repositório.
## Problema
Falta de esteira com enforcement SDD/TDD.
## Escopo
Instalação completa do Harness v2.3.
## Fora de Escopo
Alterações de layout na landing page neste momento.
## Riscos
Resistência na adoção do ciclo RED antes de GREEN.
## Critérios de Aceite
100% dos testes passando e gates H0, T1, T2 em verde.
""",
            encoding="utf-8",
        )

        specs_dir = self.change_dir / "specs"
        specs_dir.mkdir(exist_ok=True)
        (specs_dir / "bootstrap_spec.md").write_text(
            """# Especificação BDD
Given o repositório configurado
When o Harness v2.3 é inicializado
Then todos os gates de governança são ativados
""",
            encoding="utf-8",
        )

        # test-plan.md inicial com teste RED registrado
        (self.change_dir / "test-plan.md").write_text(
            """# Plano de Testes
## Mapeamento Requisito -> Teste
- Req Bootstrap -> tests/test_bootstrap.py
## Evidência de Teste RED
- Status: RED
- Detalhes: AssertionError: expected Harness to be installed. Falha comprovada antes do código.
""",
            encoding="utf-8",
        )

        (self.change_dir / "tasks.md").write_text(
            """# Tarefas
- [x] Task 1: Configurar schemas OpenSpec (1h)
- [x] Task 2: Implementar Core Engine e Adapters (1.5h)
- [x] Task 3: Criar suite de testes TDD (1h)
""",
            encoding="utf-8",
        )

        # 2. Gate H0: Validação de Schema
        val_res = validate_change(self.change_dir, project_root=self.temp_dir)
        self.assertTrue(val_res.is_valid, msg=f"Erros na validação: {val_res.errors}")

        # 3. Gerenciamento de Concorrência (Lease)
        lease_mgr = WorkspaceLeaseManager(project_root=self.temp_dir)
        lease = lease_mgr.acquire(self.change_id, agent_id="agent-bootstrap", lease_type=LeaseType.WRITE)
        self.assertEqual(lease.lease_type, LeaseType.WRITE)

        # 4. Context Pack & Execution Pack
        cp_builder = ContextPackBuilder(project_root=self.temp_dir)
        cp_builder.add_directory(self.change_dir)
        context_pack = cp_builder.build(self.change_id)
        self.assertTrue(len(context_pack.sha256) == 64)

        ep_mgr = ExecutionPackManager(project_root=self.temp_dir)
        exec_pack = ep_mgr.create_pack(
            change_id=self.change_id,
            role="implementer",
            target_tasks=["Configurar schemas", "Implementar Core"],
            context_pack_id=context_pack.pack_id,
            base_state=HarnessState.DRAFT.value,
            base_hash=context_pack.sha256,
        )
        self.assertEqual(exec_pack.version, 1)

        # 5. Máquina de Estados: Ciclo SDD/TDD
        sm = HarnessStateMachine(self.change_id, project_root=self.temp_dir)
        self.assertEqual(sm.get_state(), HarnessState.DRAFT)

        sm.transition(HarnessState.SPEC_PLANNED, actor="agent-bootstrap", reason="Specs elaboradas")
        sm.transition(HarnessState.SPEC_APPROVED, actor="agent-bootstrap", reason="Specs aprovadas")
        sm.transition(HarnessState.RED_REQUIRED, actor="agent-bootstrap", reason="Iniciando ciclo TDD")

        # Verifica evidência de teste RED
        gate_runner = GateRunner(project_root=self.temp_dir)
        t1_res = gate_runner.run_t1(self.change_id)
        self.assertTrue(t1_res.passed, msg=f"T1 falhou: {t1_res.message}")

        sm.transition(HarnessState.RED_RECORDED, actor="agent-bootstrap", reason="Teste RED gravado")
        sm.transition(HarnessState.IMPLEMENTING, actor="agent-bootstrap", reason="Iniciando código")

        # Simula teste funcional do sistema em tests/
        tests_dir = self.temp_dir / "tests"
        tests_dir.mkdir(exist_ok=True)
        (tests_dir / "test_bootstrap.py").write_text(
            """import unittest
class TestBootstrap(unittest.TestCase):
    def test_harness_installed(self):
        self.assertTrue(True)
""",
            encoding="utf-8",
        )

        # Executa suite com sucesso
        t2_res = gate_runner.run_t2()
        self.assertTrue(t2_res.passed, msg=f"T2 falhou: {t2_res.message}")

        sm.transition(HarnessState.GREEN, actor="agent-bootstrap", reason="Suite 100% verde")
        sm.transition(HarnessState.REFACTORED, actor="agent-bootstrap", reason="Refatoração limpa")
        sm.transition(HarnessState.VERIFIED, actor="agent-bootstrap", reason="Verificação estática OK")
        sm.transition(HarnessState.REVIEWED, actor="agent-bootstrap", reason="Revisão concluída")
        sm.transition(HarnessState.READY_TO_ARCHIVE, actor="agent-bootstrap", reason="Pronto para arquivar")

        # 6. ArchiveGuard: Verificação final de bloqueio e emissão de ResultBundle assinado
        archive_guard = ArchiveGuard(project_root=self.temp_dir)
        bundle = archive_guard.assert_ready_to_archive(self.change_id)
        self.assertTrue(bundle.overall_passed)

        sm.transition(HarnessState.ARCHIVED, actor="agent-bootstrap", reason="Arquivado com sucesso")
        self.assertEqual(sm.get_state(), HarnessState.ARCHIVED)

        # 7. Libera Lease
        lease_mgr.release(lease, reason="Change concluída e arquivada")
        self.assertEqual(len(lease_mgr._read_active_leases(self.change_id)), 0)


if __name__ == "__main__":
    unittest.main()
