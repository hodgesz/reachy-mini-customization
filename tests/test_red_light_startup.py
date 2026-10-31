"""Test a vendor game's startup prelude with fake hardware and no imports."""
import ast
import importlib.util
from pathlib import Path
import threading
from types import SimpleNamespace
import unittest

path = Path(__file__).resolve().parents[1] / 'scripts/repair_red_light_startup.py'
spec = importlib.util.spec_from_file_location('game_repair', path)
repair = importlib.util.module_from_spec(spec)
spec.loader.exec_module(repair)

FIXTURE = '''class RedLightGreenLightApp:
    def run(self, reachy_mini, stop_event):
        pose_landmarker_path = "fake-model"
        people_detector = PeopleDetector(model_path=pose_landmarker_path, max_poses=3)
        def sequence():
            pass
        while not stop_event.is_set():
            sequence()
'''


def run_startup(source, stopped=False, stop_on_enable=False):
    method = next(node for node in ast.walk(ast.parse(source))
                  if isinstance(node, ast.FunctionDef) and node.name == 'run')
    method.body = method.body[:next(i for i, node in enumerate(method.body)
                                   if isinstance(node, ast.FunctionDef))]
    for arg in method.args.args:
        arg.annotation = None
    method.returns = None
    namespace = {'np': SimpleNamespace(eye=lambda _: 'neutral'),
                 'PeopleDetector': lambda **_: object(),
                 'files': lambda _: SimpleNamespace(joinpath=lambda _: 'fake-model'),
                 'red_light_green_light': object()}
    exec(compile(ast.Module(body=[method], type_ignores=[]), '<game startup>', 'exec'), namespace)
    event = threading.Event()
    if stopped:
        event.set()
    calls = []
    def enable():
        calls.append(('enable', {}))
        if stop_on_enable:
            event.set()
    fake = SimpleNamespace(enable_motors=enable,
                           goto_target=lambda **kw: calls.append(('move', kw)))
    namespace['run'](None, fake, event)
    return calls


class GameStartupTests(unittest.TestCase):
    def test_standby_motors_enabled_before_slow_upright_pose(self):
        self.assertEqual(run_startup(FIXTURE), [])
        calls = run_startup(repair.repair_source(FIXTURE))
        self.assertEqual([call[0] for call in calls], ['enable', 'move'])
        self.assertEqual(calls[1][1], dict(head='neutral', antennas=[0.0, 0.0],
                                        body_yaw=0.0, duration=2.5))

    def test_stopped_startup_does_not_enable_or_move(self):
        self.assertEqual(run_startup(repair.repair_source(FIXTURE), stopped=True), [])

    def test_stop_after_enable_does_not_move_or_drop_torque(self):
        self.assertEqual(run_startup(repair.repair_source(FIXTURE), stop_on_enable=True),
                         [('enable', {})])

    def test_idempotence_and_unrecognized_source(self):
        fixed = repair.repair_source(FIXTURE)
        self.assertEqual(fixed, repair.repair_source(fixed))
        with self.assertRaises(ValueError):
            repair.repair_source(FIXTURE.replace('max_poses=3', 'max_poses=4'))


if __name__ == '__main__':
    unittest.main()
