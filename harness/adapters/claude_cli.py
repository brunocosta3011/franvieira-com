"""
Claude Code CLI Adapter para Harness v2.3
Execuções headless com discovery de binário, controle de timeout e sanitização estrita de segredos.
"""
import os
from pathlib import Path
import re
import shutil
import subprocess
from typing import Any, Dict, List, Optional

from harness.adapters.base import AgentCapabilities, BaseAgentAdapter, CollectionBundle
from harness.core.context_pack import ContextPack
from harness.core.execution_pack import ExecutionPack


SECRET_PATTERNS = [
    re.compile(r"-----BEGIN [A-Z ]+ PRIVATE KEY-----[\s\S]*?-----END [A-Z ]+ PRIVATE KEY-----"),
    re.compile(r"(?i)(api[_-]?key|secret|token|password|passwd|auth)\s*[:=]\s*['\"][A-Za-z0-9_\-\.]{8,}['\"]"),
    re.compile(r"ghp_[A-Za-z0-9]{36}"),
    re.compile(r"sk-[A-Za-z0-9]{48}"),
    re.compile(r"xox[baprs]-[A-Za-z0-9\-]+"),
    re.compile(r"Bearer\s+[A-Za-z0-9\-\._~\+\/]+=*"),
]


def sanitize_secrets(text: str) -> str:
    """Substitui padrões de segredos e credenciais por [REDACTED_SECRET]."""
    sanitized = text
    for pattern in SECRET_PATTERNS:
        sanitized = pattern.sub("[REDACTED_SECRET]", sanitized)
    return sanitized


class ClaudeCodeCLIAdapter(BaseAgentAdapter):
    def __init__(
        self,
        project_root: Optional[str | Path] = None,
        cli_path: Optional[str] = None,
    ):
        super().__init__(project_root)
        self.cli_path = cli_path or os.environ.get("CLAUDE_CLI_PATH") or shutil.which("claude")

    def get_capabilities(self) -> AgentCapabilities:
        return AgentCapabilities(
            interactive=False,
            headless=True,
            supports_streaming=True,
            supports_tools=True,
            supports_subagents=False,
        )

    def is_available(self) -> bool:
        return bool(self.cli_path and (Path(self.cli_path).exists() or shutil.which(self.cli_path)))

    def execute(
        self,
        execution_pack: ExecutionPack,
        context_pack: ContextPack,
        timeout_seconds: int = 300,
    ) -> CollectionBundle:
        run_id = f"claude-cli-{execution_pack.pack_id}"

        if not self.is_available():
            # Retorna bundle indicando indisponibilidade do binário no ambiente
            return CollectionBundle(
                run_id=run_id,
                adapter_name="claude_cli",
                exit_code=127,
                files_modified=[],
                stdout="",
                stderr="Claude Code CLI binary não encontrado no PATH nem em CLAUDE_CLI_PATH.",
                metadata={"available": False},
            )

        prompt_text = (
            f"Execute as tarefas: {', '.join(execution_pack.target_tasks)}. "
            f"Allowed paths: {execution_pack.allowed_paths}. "
            f"Context Pack SHA256: {context_pack.sha256}."
        )

        cmd = [self.cli_path, "-p", prompt_text]

        try:
            res = subprocess.run(
                cmd,
                cwd=str(self.root),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=timeout_seconds,
            )
            exit_code = res.returncode
            stdout = sanitize_secrets(res.stdout)
            stderr = sanitize_secrets(res.stderr)
        except subprocess.TimeoutExpired as e:
            exit_code = 124
            stdout = sanitize_secrets(e.stdout or "" if isinstance(e.stdout, str) else "")
            stderr = f"Execution timed out after {timeout_seconds} seconds."
        except Exception as e:
            exit_code = 1
            stdout = ""
            stderr = sanitize_secrets(str(e))

        return CollectionBundle(
            run_id=run_id,
            adapter_name="claude_cli",
            exit_code=exit_code,
            files_modified=[],
            stdout=stdout,
            stderr=stderr,
            metadata={"cli_path": self.cli_path, "timeout_seconds": timeout_seconds},
        )
