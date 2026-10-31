"""Verify the managed app adapter without opening a connection or moving hardware."""
from copy import deepcopy
import threading
import unittest

from reachy_customizations.motions import ROUTINES
from reachy_customizations.sdk_runner import run_sequence


class FakeEvent:
    def __init__(self):
        self.stopped = False

    def is_set(self):
        return self.stopped

    def wait(self, timeout):
        return self.stopped


class FakeMini:
    def __init__(self, event=None):
        self.enabled = 0
        self.moves = []
        self.event = event

    def enable_motors(self):
        self.enabled += 1

    def goto_target(self, **kwargs):
        self.moves.append(kwargs)
        if self.event and len(self.moves) == 2:
            self.event.stopped = True


class RuntimeTests(unittest.TestCase):
    def test_both_app_sequences_convert_units_and_finish_at_neutral(self):
        for routine, steps in ROUTINES.items():
            with self.subTest(routine=routine):
                mini = FakeMini()
                self.assertTrue(run_sequence(mini, FakeEvent(), routine, lambda **kw: kw, music=False))
                self.assertEqual(len(mini.moves), len(steps))
                self.assertAlmostEqual(mini.moves[0]['antennas'][0], -0.1745329252)
                final = mini.moves[-1]
                self.assertEqual(final['head']['pitch'], 0)
                self.assertEqual(final['head']['z'], 0)
                self.assertEqual(final['body_yaw'], 0)
                self.assertTrue(final['head']['degrees'])
                self.assertTrue(final['head']['mm'])

    def test_stop_before_start_does_not_enable_motors(self):
        event = threading.Event()
        event.set()
        mini = FakeMini()
        self.assertFalse(run_sequence(mini, event, 'hello', lambda **kw: kw))
        self.assertEqual(mini.enabled, 0)
        self.assertEqual(mini.moves, [])

    def test_desktop_stop_returns_to_neutral_without_disabling_torque(self):
        event = FakeEvent()
        mini = FakeMini(event)
        self.assertFalse(run_sequence(mini, event, 'auburn', lambda **kw: kw, music=False))
        self.assertEqual(len(mini.moves), 3)
        self.assertEqual(mini.moves[-1]['duration'], 2.0)
        self.assertEqual(mini.moves[-1]['head'], {'degrees': True, 'mm': True})

    def test_invalid_late_pose_is_rejected_before_any_movement(self):
        original = ROUTINES['hello']
        invalid = deepcopy(original)
        invalid[-1]['roll'] = 90
        ROUTINES['hello'] = invalid
        try:
            mini = FakeMini()
            with self.assertRaises(ValueError):
                run_sequence(mini, FakeEvent(), 'hello', lambda **kw: kw)
            self.assertEqual(mini.enabled, 0)
            self.assertEqual(mini.moves, [])
        finally:
            ROUTINES['hello'] = original


if __name__ == '__main__':
    unittest.main()
