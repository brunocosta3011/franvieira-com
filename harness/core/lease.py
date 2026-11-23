"""
Workspace Lease Manager para Harness v2.3
Bloqueio de escrita exclusivo (WRITE), leases compartilhados (READ) e log de handoffs.
"""
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
import json
from pathlib import Path
import time
from typing import Any, Dict, Iterator, List, Optional


class LeaseType(str, Enum):
    WRITE = "WRITE"
    READ = "READ"


class LeaseAcquisitionError(Exception):
    """Lançada quando não é possível adquirir o lease devido a conflito de concorrência."""
    pass


@dataclass
class LeaseRecord:
    lease_id: str
    change_id: str
    agent_id: str
    lease_type: LeaseType
    acquired_at: str
    metadata: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "lease_id": self.lease_id,
            "change_id": self.change_id,
            "agent_id": self.agent_id,
            "lease_type": self.lease_type.value,
            "acquired_at": self.acquired_at,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "LeaseRecord":
        return cls(
            lease_id=data["lease_id"],
            change_id=data["change_id"],
            agent_id=data["agent_id"],
            lease_type=LeaseType(data["lease_type"]),
            acquired_at=data["acquired_at"],
            metadata=data.get("metadata", {}),
        )


class WorkspaceLeaseManager:
    def __init__(self, project_root: Optional[str | Path] = None):
        self.root = Path(project_root) if project_root else Path.cwd()
        self.leases_dir = self.root / ".harness" / "leases"
        self.handoffs_dir = self.root / ".harness" / "handoffs"
        self.leases_dir.mkdir(parents=True, exist_ok=True)
        self.handoffs_dir.mkdir(parents=True, exist_ok=True)

    def _lock_file(self, change_id: str) -> Path:
        return self.leases_dir / f"{change_id}.leases.json"

    def _handoff_file(self, change_id: str) -> Path:
        return self.handoffs_dir / f"{change_id}.jsonl"

    def _read_active_leases(self, change_id: str) -> List[LeaseRecord]:
        lf = self._lock_file(change_id)
        if not lf.exists():
            return []
        try:
            items = json.loads(lf.read_text(encoding="utf-8"))
            return [LeaseRecord.from_dict(it) for it in items]
        except Exception:
            return []

    def _write_active_leases(self, change_id: str, leases: List[LeaseRecord]) -> None:
        lf = self._lock_file(change_id)
        if not leases:
            if lf.exists():
                lf.unlink()
            return
        data = [it.to_dict() for it in leases]
        lf.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")

    def acquire(
        self,
        change_id: str,
        agent_id: str,
        lease_type: LeaseType = LeaseType.WRITE,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> LeaseRecord:
        active = self._read_active_leases(change_id)

        # Regra de concorrência estrita:
        if lease_type == LeaseType.WRITE:
            if active:
                holders = ", ".join(f"{l.agent_id} ({l.lease_type.value})" for l in active)
                raise LeaseAcquisitionError(
                    f"Falha ao adquirir lease WRITE para change '{change_id}'. "
                    f"Já existem leases ativos: {holders}"
                )
        else:  # READ
            write_leases = [l for l in active if l.lease_type == LeaseType.WRITE]
            if write_leases:
                holders = ", ".join(f"{l.agent_id}" for l in write_leases)
                raise LeaseAcquisitionError(
                    f"Falha ao adquirir lease READ para change '{change_id}'. "
                    f"Existe lease WRITE exclusivo ativo: {holders}"
                )

        now = datetime.now(timezone.utc).isoformat()
        lease_id = f"lease-{change_id}-{int(time.time()*1000)}"
        record = LeaseRecord(
            lease_id=lease_id,
            change_id=change_id,
            agent_id=agent_id,
            lease_type=lease_type,
            acquired_at=now,
            metadata=metadata or {},
        )

        active.append(record)
        self._write_active_leases(change_id, active)
        return record

    def release(
        self,
        record: LeaseRecord,
        handoff_to: Optional[str] = None,
        reason: str = "Release completed",
    ) -> None:
        active = self._read_active_leases(record.change_id)
        active = [l for l in active if l.lease_id != record.lease_id]
        self._write_active_leases(record.change_id, active)

        # Registra handoff / release
        hf = self._handoff_file(record.change_id)
        handoff_entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "change_id": record.change_id,
            "lease_id": record.lease_id,
            "from_agent": record.agent_id,
            "to_agent": handoff_to,
            "lease_type": record.lease_type.value,
            "reason": reason,
        }
        with open(hf, "a", encoding="utf-8") as f:
            f.write(json.dumps(handoff_entry, ensure_ascii=False) + "\n")

    @contextmanager
    def lease_context(
        self,
        change_id: str,
        agent_id: str,
        lease_type: LeaseType = LeaseType.WRITE,
        handoff_to: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Iterator[LeaseRecord]:
        record = self.acquire(change_id, agent_id, lease_type, metadata)
        try:
            yield record
        finally:
            self.release(record, handoff_to=handoff_to)

    def get_handoff_history(self, change_id: str) -> List[Dict[str, Any]]:
        hf = self._handoff_file(change_id)
        if not hf.exists():
            return []
        entries = []
        with open(hf, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    entries.append(json.loads(line))
        return entries
