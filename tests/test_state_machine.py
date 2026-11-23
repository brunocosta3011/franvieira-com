import shutil
import tempfile
import unittest
from pathlib import Path

from harness.core.state_machine import (
    HarnessStateMachine,
    HarnessState,
    InvalidStateTransitionError,
)


class TestHarnessStateMachine(unittest.TestCase):
    def setUp(self):
        self.temp_dir = Path(tempfile.mkdtemp())
        self.change_id = "test-change-01"

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_initial_state_and_persistence(self):
        sm = HarnessStateMachine(self.change_id, project_root=self.temp_dir)
        self.assertEqual(sm.get_state(), HarnessState.DRAFT)

        # Recarrega do disco
        sm2 = HarnessStateMachine(self.change_id, project_root=self.temp_dir)
        self.assertEqual(sm2.get_state(), HarnessState.DRAFT)

    def test_valid_lifecycle_transitions(self):
        sm = HarnessStateMachine(self.change_id, project_root=self.temp_dir)
        sequence = [
            HarnessState.SPEC_PLANNED,
            HarnessState.SPEC_APPROVED,
            HarnessState.RED_REQUIRED,
            HarnessState.RED_RECORDED,
            HarnessState.IMPLEMENTING,
            HarnessState.GREEN,
            HarnessState.REFACTORED,
            HarnessState.VERIFIED,
            HarnessState.REVIEWED,
            HarnessState.READY_TO_ARCHIVE,
            HarnessState.ARCHIVED,
        ]

        for target in sequence:
            sm.transition(target, actor="tester", reason="TDD sequence")
            self.assertEqual(sm.get_state(), target)

        history = sm.get_history()
        # Initial event + 11 transitions = 12 events
        self.assertEqual(len(history), 12)
        self.assertEqual(history[-1]["to_state"], HarnessState.ARCHIVED.value)

    def test_invalid_transition_raises_error(self):
        sm = HarnessStateMachine(self.change_id, project_root=self.temp_dir)
        # De DRAFT direto para GREEN não é permitido
        with self.assertRaises(InvalidStateTransitionError):
            sm.transition(HarnessState.GREEN)


if __name__ == "__main__":
    unittest.main()
