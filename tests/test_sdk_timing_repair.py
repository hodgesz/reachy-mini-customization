"""Exercise the real SDK playback method without importing or moving hardware."""
import ast
import asyncio
import importlib.util
from pathlib import Path
from types import SimpleNamespace
import unittest

REPAIR_FILE = Path(__file__).resolve().parents[1] / 'scripts/repair_sdk_113_timing.py'
spec = importlib.util.spec_from_file_location('repair', REPAIR_FILE)
repair = importlib.util.module_from_spec(spec)
spec.loader.exec_module(repair)

# The clock reads around evaluate() are the bug. Other behavior remains real
# when --sdk-source is supplied by the robot validation command in the docs.
FIXTURE = '''class Backend:
    async def play_move(self, move):
        try:
            t0 = time.time()
            try:
                while time.time() - t0 < move.duration:
                    if self._stop_move_requested or (
                        False
                    ):
                        break
                    t = time.time() - t0
                    move.evaluate(t)
                    elapsed = time.time() - t0 - t
                    await asyncio.sleep(max(0.001, 0.01 - elapsed))
            finally:
                pass
        finally:
            self._end_move()
'''


def simulate(source, cancel=False):
    method = next(node for node in ast.walk(ast.parse(source))
                  if isinstance(node, ast.AsyncFunctionDef) and node.name == 'play_move')
    method.decorator_list = []
    # Remove annotations so vendor dependencies are not imported in this test.
    method.returns = None
    for arg in method.args.args + method.args.kwonlyargs:
        arg.annotation = None
    clock_values = iter([0.0, 0.999999, 1.000001, 1.02])
    clock = lambda: next(clock_values)
    async def sleep(_):
        pass
    namespace = {'time': SimpleNamespace(time=clock, monotonic=clock),
                 'asyncio': SimpleNamespace(sleep=sleep)}
    exec(compile(ast.Module(body=[method], type_ignores=[]), '<SDK playback>', 'exec'), namespace)
    evaluated = []
    def evaluate(t):
        if not 0 <= t <= 1:
            raise ValueError('time value is out of range [0,1]')
        evaluated.append(t)
        return None, None, None
    ended = []
    backend = SimpleNamespace(_stop_move_requested=cancel, _active_move_depth=2,
                              _try_start_move=lambda: True,
                              _end_move=lambda: ended.append(True),
                              logger=SimpleNamespace(info=lambda *_: None))
    move = SimpleNamespace(duration=1.0, sound_path=None, evaluate=evaluate)
    asyncio.run(namespace['play_move'](backend, move))
    return evaluated, ended


class PlaybackRepairTests(unittest.TestCase):
    def test_reproduces_boundary_crash_and_repairs_it(self):
        with self.assertRaisesRegex(ValueError, 'out of range'):
            simulate(FIXTURE)
        evaluated, ended = simulate(repair.repair_source(FIXTURE))
        self.assertEqual(evaluated, [0.999999])
        self.assertEqual(ended, [True])

    def test_cancellation_and_idempotence(self):
        fixed = repair.repair_source(FIXTURE)
        self.assertEqual(fixed, repair.repair_source(fixed))
        evaluated, ended = simulate(fixed, cancel=True)
        self.assertEqual(evaluated, [])
        self.assertEqual(ended, [True])

    def test_unrecognized_source_refused(self):
        with self.assertRaises(ValueError):
            repair.repair_source(FIXTURE.replace('t0 = time.time()', 't0 = custom_clock()'))


if __name__ == '__main__':
    unittest.main()
