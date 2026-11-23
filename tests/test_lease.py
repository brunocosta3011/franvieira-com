import shutil
import tempfile
import unittest
from pathlib import Path

from harness.core.lease import WorkspaceLeaseManager, LeaseType, LeaseAcquisitionError


class TestWorkspaceLease(unittest.TestCase):
    def setUp(self):
        self.temp_dir = Path(tempfile.mkdtemp())
        self.lm = WorkspaceLeaseManager(project_root=self.temp_dir)
        self.change_id = "ch-lease-01"

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_exclusive_write_lease(self):
        # Primeiro agente adquire WRITE
        rec1 = self.lm.acquire(self.change_id, agent_id="agent-1", lease_type=LeaseType.WRITE)
        self.assertEqual(rec1.lease_type, LeaseType.WRITE)

        # Segundo agente tenta adquirir WRITE -> Falha
        with self.assertRaises(LeaseAcquisitionError):
            self.lm.acquire(self.change_id, agent_id="agent-2", lease_type=LeaseType.WRITE)

        # Terceiro agente tenta adquirir READ -> Falha
        with self.assertRaises(LeaseAcquisitionError):
            self.lm.acquire(self.change_id, agent_id="agent-3", lease_type=LeaseType.READ)

        # Primeiro agente libera o lease
        self.lm.release(rec1, handoff_to="agent-2")

        # Agora agente 2 consegue adquirir WRITE
        rec2 = self.lm.acquire(self.change_id, agent_id="agent-2", lease_type=LeaseType.WRITE)
        self.assertEqual(rec2.agent_id, "agent-2")
        self.lm.release(rec2)

        # Verifica histórico de handoff
        history = self.lm.get_handoff_history(self.change_id)
        self.assertEqual(len(history), 2)
        self.assertEqual(history[0]["from_agent"], "agent-1")
        self.assertEqual(history[0]["to_agent"], "agent-2")

    def test_concurrent_read_leases(self):
        rec1 = self.lm.acquire(self.change_id, agent_id="reader-1", lease_type=LeaseType.READ)
        rec2 = self.lm.acquire(self.change_id, agent_id="reader-2", lease_type=LeaseType.READ)

        self.assertEqual(rec1.lease_type, LeaseType.READ)
        self.assertEqual(rec2.lease_type, LeaseType.READ)

        # Tentativa de adquirir WRITE com READs ativos deve falhar
        with self.assertRaises(LeaseAcquisitionError):
            self.lm.acquire(self.change_id, agent_id="writer-1", lease_type=LeaseType.WRITE)

        self.lm.release(rec1)
        self.lm.release(rec2)

    def test_lease_context_manager(self):
        with self.lm.lease_context(self.change_id, agent_id="ctx-agent", lease_type=LeaseType.WRITE) as rec:
            self.assertEqual(rec.agent_id, "ctx-agent")
            # Tentar outro WRITE dentro do context deve falhar
            with self.assertRaises(LeaseAcquisitionError):
                self.lm.acquire(self.change_id, agent_id="other-agent", lease_type=LeaseType.WRITE)

        # Fora do context, lease deve ter sido liberado
        rec_after = self.lm.acquire(self.change_id, agent_id="other-agent", lease_type=LeaseType.WRITE)
        self.lm.release(rec_after)


if __name__ == "__main__":
    unittest.main()
