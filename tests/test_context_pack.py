import shutil
import tempfile
import unittest
from pathlib import Path

from harness.core.context_pack import ContextPackBuilder, BudgetExceededError


class TestContextPack(unittest.TestCase):
    def setUp(self):
        self.temp_dir = Path(tempfile.mkdtemp())
        self.src_dir = self.temp_dir / "src"
        self.src_dir.mkdir(parents=True, exist_ok=True)

        (self.src_dir / "app.py").write_text("print('hello world')", encoding="utf-8")
        (self.src_dir / "utils.py").write_text("def add(a, b): return a + b", encoding="utf-8")
        (self.temp_dir / ".env.local").write_text("SECRET=12345", encoding="utf-8")
        (self.temp_dir / "server.key").write_text("PRIVATE KEY DATA", encoding="utf-8")

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_deterministic_hash(self):
        builder1 = ContextPackBuilder(project_root=self.temp_dir)
        builder1.add_file("src/app.py")
        builder1.add_file("src/utils.py")
        pack1 = builder1.build("ch-01")

        builder2 = ContextPackBuilder(project_root=self.temp_dir)
        builder2.add_file("src/utils.py")
        builder2.add_file("src/app.py")
        pack2 = builder2.build("ch-01")

        self.assertEqual(pack1.sha256, pack2.sha256)
        self.assertEqual(pack1.total_tokens, pack2.total_tokens)
        self.assertEqual(len(pack1.files), 2)

    def test_denylist_rejection(self):
        builder = ContextPackBuilder(project_root=self.temp_dir)
        # Tenta adicionar arquivos sensíveis
        added_env = builder.add_file(".env.local")
        added_key = builder.add_file("server.key")

        self.assertFalse(added_env)
        self.assertFalse(added_key)

        pack = builder.build("ch-01")
        self.assertEqual(len(pack.files), 0)

    def test_budget_exceeded(self):
        # Limite intencionalmente minúsculo (2 tokens para um arquivo de ~5 tokens)
        builder = ContextPackBuilder(project_root=self.temp_dir, max_token_budget=2)
        builder.add_file("src/app.py")
        with self.assertRaises(BudgetExceededError):
            builder.build("ch-01")


if __name__ == "__main__":
    unittest.main()
