"""
Adapters de Executores para Harness v2.3
"""
from harness.adapters.base import AgentCapabilities, BaseAgentAdapter, CollectionBundle
from harness.adapters.fake import FakeAgentAdapter
from harness.adapters.interactive import InteractiveAgentAdapter, ScopeViolationError
from harness.adapters.claude_cli import ClaudeCodeCLIAdapter, sanitize_secrets

__all__ = [
    "AgentCapabilities",
    "BaseAgentAdapter",
    "CollectionBundle",
    "FakeAgentAdapter",
    "InteractiveAgentAdapter",
    "ScopeViolationError",
    "ClaudeCodeCLIAdapter",
    "sanitize_secrets",
]
