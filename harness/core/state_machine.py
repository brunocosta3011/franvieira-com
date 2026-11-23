"""
Harness State Machine v2.3
Ciclo canônico de governança SDD/TDD do ecossistema Fran Vieira.
"""
from datetime import datetime, timezone
from enum import Enum
import json
from pathlib import Path
from typing import Any, Dict, List, Optional


class HarnessState(str, Enum):
    DRAFT = "DRAFT"
    SPEC_PLANNED = "SPEC_PLANNED"
    SPEC_APPROVED = "SPEC_APPROVED"
    RED_REQUIRED = "RED_REQUIRED"
    RED_RECORDED = "RED_RECORDED"
    IMPLEMENTING = "IMPLEMENTING"
    GREEN = "GREEN"
    REFACTORED = "REFACTORED"
    VERIFIED = "VERIFIED"
    REVIEWED = "REVIEWED"
    READY_TO_ARCHIVE = "READY_TO_ARCHIVE"
    ARCHIVED = "ARCHIVED"


ALLOWED_TRANSITIONS: Dict[HarnessState, List[HarnessState]] = {
    HarnessState.DRAFT: [HarnessState.SPEC_PLANNED],
    HarnessState.SPEC_PLANNED: [HarnessState.SPEC_APPROVED, HarnessState.DRAFT],
    HarnessState.SPEC_APPROVED: [HarnessState.RED_REQUIRED, HarnessState.SPEC_PLANNED],
    HarnessState.RED_REQUIRED: [HarnessState.RED_RECORDED, HarnessState.SPEC_APPROVED],
    HarnessState.RED_RECORDED: [HarnessState.IMPLEMENTING, HarnessState.RED_REQUIRED],
    HarnessState.IMPLEMENTING: [HarnessState.GREEN, HarnessState.RED_RECORDED],
    HarnessState.GREEN: [HarnessState.REFACTORED, HarnessState.VERIFIED, HarnessState.IMPLEMENTING],
    HarnessState.REFACTORED: [HarnessState.VERIFIED, HarnessState.GREEN, HarnessState.IMPLEMENTING],
    HarnessState.VERIFIED: [HarnessState.REVIEWED, HarnessState.IMPLEMENTING],
    HarnessState.REVIEWED: [HarnessState.READY_TO_ARCHIVE, HarnessState.IMPLEMENTING],
    HarnessState.READY_TO_ARCHIVE: [HarnessState.ARCHIVED, HarnessState.REVIEWED],
    HarnessState.ARCHIVED: [],
}


class InvalidStateTransitionError(Exception):
    """Lançada quando uma transição não é permitida pela máquina de estados."""
    pass


class HarnessStateMachine:
    def __init__(self, change_id: str, project_root: Optional[str | Path] = None):
        self.change_id = change_id
        self.root = Path(project_root) if project_root else Path.cwd()
        self.state_dir = self.root / ".harness" / "state"
        self.events_dir = self.root / ".harness" / "events"
        self.state_file = self.state_dir / f"{change_id}.json"
        self.events_file = self.events_dir / f"{change_id}.jsonl"

        self._ensure_dirs()
        self._load_or_init()

    def _ensure_dirs(self) -> None:
        self.state_dir.mkdir(parents=True, exist_ok=True)
        self.events_dir.mkdir(parents=True, exist_ok=True)

    def _load_or_init(self) -> None:
        if self.state_file.exists():
            try:
                data = json.loads(self.state_file.read_text(encoding="utf-8"))
                self.current_state = HarnessState(data["state"])
                self.created_at = data.get("created_at")
                self.updated_at = data.get("updated_at")
                self.metadata = data.get("metadata", {})
                return
            except Exception:
                pass

        now = datetime.now(timezone.utc).isoformat()
        self.current_state = HarnessState.DRAFT
        self.created_at = now
        self.updated_at = now
        self.metadata = {}
        self._save_state()
        self._log_event(
            from_state=None,
            to_state=self.current_state.value,
            actor="system",
            reason="Initial state creation",
            metadata={},
        )

    def _save_state(self) -> None:
        payload = {
            "change_id": self.change_id,
            "state": self.current_state.value,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "metadata": self.metadata,
        }
        self.state_file.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")

    def _log_event(
        self,
        from_state: Optional[str],
        to_state: str,
        actor: str,
        reason: str,
        metadata: Dict[str, Any],
    ) -> Dict[str, Any]:
        event = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "change_id": self.change_id,
            "from_state": from_state,
            "to_state": to_state,
            "actor": actor,
            "reason": reason,
            "metadata": metadata or {},
        }
        with open(self.events_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(event, ensure_ascii=False) + "\n")
        return event

    def get_state(self) -> HarnessState:
        return self.current_state

    def can_transition_to(self, target_state: HarnessState) -> bool:
        allowed = ALLOWED_TRANSITIONS.get(self.current_state, [])
        return target_state in allowed

    def transition(
        self,
        target_state: HarnessState | str,
        actor: str = "agent",
        reason: str = "",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> HarnessState:
        if isinstance(target_state, str):
            target_state = HarnessState(target_state)

        if not self.can_transition_to(target_state):
            allowed = [s.value for s in ALLOWED_TRANSITIONS.get(self.current_state, [])]
            raise InvalidStateTransitionError(
                f"Transição inválida para change '{self.change_id}': "
                f"{self.current_state.value} -> {target_state.value}. "
                f"Transições permitidas a partir de {self.current_state.value}: {allowed}"
            )

        from_state = self.current_state.value
        self.current_state = target_state
        self.updated_at = datetime.now(timezone.utc).isoformat()
        if metadata:
            self.metadata.update(metadata)

        self._save_state()
        self._log_event(
            from_state=from_state,
            to_state=target_state.value,
            actor=actor,
            reason=reason,
            metadata=metadata or {},
        )
        return self.current_state

    def get_history(self) -> List[Dict[str, Any]]:
        if not self.events_file.exists():
            return []
        events = []
        with open(self.events_file, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    events.append(json.loads(line))
        return events
