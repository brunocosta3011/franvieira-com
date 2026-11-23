import shutil
import tempfile
import unittest
from pathlib import Path

from harness.core.execution_pack import ExecutionPackManager, StalePackError


class TestExecutionPack(unittest.TestCase):
    def setUp(self):
        self.temp_dir = Path(tempfile.mkdtemp())
        self.manager = ExecutionPackManager(project_root=self.temp_dir)

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_create_pack_and_path_permissions(self):
        pack = self.manager.create_pack(
            change_id="ch-01",
            role="test_engineer",
            target_tasks=["Escrever teste RED"],
            context_pack_id="cp-01",
            base_state="RED_REQUIRED",
            base_hash="hash123",
        )

        self.assertEqual(pack.version, 1)
        self.assertTrue(pack.is_path_allowed("tests/test_feature.py"))
        self.assertTrue(pack.is_path_allowed("openspec/changes/ch-01/test-plan.md"))
        self.assertFalse(pack.is_path_allowed("harness/core/validator.py"))

    def test_stale_pack_detection_on_state_change(self):
        pack = self.manager.create_pack(
            change_id="ch-01",
            role="implementer",
            target_tasks=["Implementar código"],
            context_pack_id="cp-01",
            base_state="IMPLEMENTING",
            base_hash="hash123",
        )

        # Estado atual ainda é IMPLEMENTING -> OK
        self.manager.check_freshness(pack, current_state="IMPLEMENTING", current_hash="hash123")

        # Estado avançou para GREEN -> StalePackError
        with self.assertRaises(StalePackError):
            self.manager.check_freshness(pack, current_state="GREEN", current_hash="hash123")

    def test_stale_pack_detection_on_new_version(self):
        pack_v1 = self.manager.create_pack(
            change_id="ch-01",
            role="implementer",
            target_tasks=["Task 1"],
            context_pack_id="cp-01",
            base_state="IMPLEMENTING",
            base_hash="hash123",
        )

        # Cria v2
        self.manager.create_pack(
            change_id="ch-01",
            role="implementer",
            target_tasks=["Task 2"],
            context_pack_id="cp-01",
            base_state="IMPLEMENTING",
            base_hash="hash123",
        )

        with self.assertRaises(StalePackError):
            self.manager.check_freshness(pack_v1, current_state="IMPLEMENTING", current_hash="hash123")


if __name__ == "__main__":
    unittest.main()
