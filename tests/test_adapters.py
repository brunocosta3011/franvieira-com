import shutil
import tempfile
import unittest
from pathlib import Path

from harness.adapters.base import AgentCapabilities
from harness.adapters.fake import FakeAgentAdapter
from harness.adapters.interactive import InteractiveAgentAdapter, ScopeViolationError
from harness.adapters.claude_cli import ClaudeCodeCLIAdapter, sanitize_secrets
from harness.core.context_pack import ContextPack, PackedFile
from harness.core.execution_pack import ExecutionPack
from harness.core.registry import AdapterRegistry


class TestAdapters(unittest.TestCase):
    def setUp(self):
        self.temp_dir = Path(tempfile.mkdtemp())
        self.context_pack = ContextPack(
            pack_id="cp-test",
            change_id="ch-01",
            sha256="abc123456789",
            total_tokens=100,
            max_budget=1000,
            files=[
                PackedFile(
                    relative_path="src/main.py",
                    sha256="123",
                    size_bytes=50,
                    estimated_tokens=12,
                    content="print('ok')",
                )
            ],
        )
        self.exec_pack = ExecutionPack(
            pack_id="ep-test-v1",
            change_id="ch-01",
            version=1,
            role="test_engineer",
            target_tasks=["Criar teste RED"],
            allowed_paths=["tests/*", "openspec/changes/*"],
            context_pack_id="cp-test",
            base_state="RED_REQUIRED",
            base_hash="hash123",
            created_at="2026-11-23T00:00:00Z",
        )

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_fake_adapter(self):
        adapter = FakeAgentAdapter(
            project_root=self.temp_dir,
            files_to_modify=["tests/test_fake.py"],
        )
        bundle = adapter.execute(self.exec_pack, self.context_pack)
        self.assertEqual(bundle.exit_code, 0)
        self.assertEqual(bundle.files_modified, ["tests/test_fake.py"])
        self.assertTrue((self.temp_dir / "tests" / "test_fake.py").exists())

    def test_interactive_adapter_scope_validation(self):
        adapter = InteractiveAgentAdapter(project_root=self.temp_dir)
        # Gera instruções
        instr_file = adapter.generate_instructions(self.exec_pack, self.context_pack)
        self.assertTrue(instr_file.exists())

        # Validação com arquivos dentro do escopo permitido
        adapter.validate_scope(self.exec_pack, ["tests/test_feature.py"])

        # Validação com arquivo fora do escopo permitido (ex: arquivo core/harness alterado por test_engineer)
        with self.assertRaises(ScopeViolationError):
            adapter.validate_scope(self.exec_pack, ["harness/core/validator.py"])

    def test_claude_cli_secret_sanitization(self):
        raw_text = "Erro na conexão: api_key='sk-1234567890abcdef1234567890abcdef12345678' e Bearer secret_token_value_abc"
        sanitized = sanitize_secrets(raw_text)
        self.assertNotIn("sk-1234567890abcdef1234567890abcdef12345678", sanitized)
        self.assertIn("[REDACTED_SECRET]", sanitized)

    def test_adapter_registry(self):
        registry = AdapterRegistry(project_root=self.temp_dir)
        registry.register("fake", FakeAgentAdapter)
        adapter = registry.get_adapter("fake")
        self.assertIsInstance(adapter, FakeAgentAdapter)

        run = registry.start_run("ch-01", "fake")
        self.assertEqual(run.status, "RUNNING")
        finished = registry.finish_run(run.run_id, exit_code=0)
        self.assertEqual(finished.status, "COMPLETED")
        self.assertEqual(finished.exit_code, 0)


if __name__ == "__main__":
    unittest.main()
