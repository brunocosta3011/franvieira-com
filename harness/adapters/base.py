"""
Interface Abstrata de Adapters para Harness v2.3
Define o contrato universal para qualquer executor de agentes (IDE ou CLI headless).
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

from harness.core.context_pack import ContextPack
from harness.core.execution_pack import ExecutionPack


@dataclass
class AgentCapabilities:
    interactive: bool = False
    headless: bool = True
    supports_streaming: bool = False
    supports_tools: bool = True
    supports_subagents: bool = False


@dataclass
class CollectionBundle:
    run_id: str
    adapter_name: str
    exit_code: int
    files_modified: List[str]
    stdout: str
    stderr: str
    metadata: Dict[str, Any] = field(default_factory=dict)


class BaseAgentAdapter(ABC):
    def __init__(self, project_root: Optional[str | Path] = None):
        self.root = Path(project_root) if project_root else Path.cwd()

    @abstractmethod
    def get_capabilities(self) -> AgentCapabilities:
        """Retorna as capacidades suportadas por este adapter."""
        pass

    @abstractmethod
    def execute(
        self,
        execution_pack: ExecutionPack,
        context_pack: ContextPack,
        timeout_seconds: int = 300,
    ) -> CollectionBundle:
        """Executa o pacote com o contexto determinado e retorna o bundle coletado."""
        pass
