"""
Adapter Registry para Harness v2.3
Registro central agnóstico de executores e alocação dinâmica de adapters.
"""
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Type


@dataclass
class ExecutionRun:
    run_id: str
    change_id: str
    adapter_name: str
    status: str
    started_at: str
    finished_at: Optional[str] = None
    exit_code: Optional[int] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class AdapterRegistry:
    def __init__(self, project_root: Optional[str | Path] = None):
        self.root = Path(project_root) if project_root else Path.cwd()
        self._adapters: Dict[str, Any] = {}
        self._runs: Dict[str, ExecutionRun] = {}

    def register(self, name: str, adapter_instance_or_class: Any) -> None:
        self._adapters[name] = adapter_instance_or_class

    def get_adapter(self, name: str) -> Any:
        if name not in self._adapters:
            raise KeyError(
                f"Adapter '{name}' não registrado. Disponíveis: {list(self._adapters.keys())}"
            )
        target = self._adapters[name]
        if isinstance(target, type):
            return target(project_root=self.root)
        return target

    def list_adapters(self) -> List[str]:
        return list(self._adapters.keys())

    def start_run(self, change_id: str, adapter_name: str, metadata: Optional[Dict[str, Any]] = None) -> ExecutionRun:
        import time
        run_id = f"run-{change_id}-{int(time.time()*1000)}"
        run = ExecutionRun(
            run_id=run_id,
            change_id=change_id,
            adapter_name=adapter_name,
            status="RUNNING",
            started_at=datetime.now(timezone.utc).isoformat(),
            metadata=metadata or {},
        )
        self._runs[run_id] = run
        return run

    def finish_run(self, run_id: str, exit_code: int, status: str = "COMPLETED") -> ExecutionRun:
        if run_id not in self._runs:
            raise KeyError(f"Run ID '{run_id}' não encontrado.")
        run = self._runs[run_id]
        run.finished_at = datetime.now(timezone.utc).isoformat()
        run.exit_code = exit_code
        run.status = status
        return run

    def get_run(self, run_id: str) -> Optional[ExecutionRun]:
        return self._runs.get(run_id)
