"""Test full-song timing and audio cleanup without playing sound or moving hardware."""
import hashlib
import unittest

from reachy_customizations.motions import validate_motion
from reachy_customizations.music import SOUND_FILE, TRACK, auburn_timeline, perform_auburn


class Clock:
    now = 0.0

    def read(self):
        return self.now


class Event:
    def __init__(self, clock):
        self.clock = clock
        self.stopped = False

    def is_set(self):
        return self.stopped

    def wait(self, duration):
        self.clock.now += duration
        return self.stopped


class Player:
    def __init__(self, clock):
        self.clock = clock
        self.started_at = None
        self.stopped_at = None

    def start(self):
        self.started_at = self.clock.now

    def stop(self):
        self.stopped_at = self.clock.now


class MusicTests(unittest.TestCase):
    def test_exact_source_asset_and_bounded_full_recording_timeline(self):
        self.assertEqual(hashlib.sha256(SOUND_FILE.read_bytes()).hexdigest(), TRACK['sha256'])
        steps = auburn_timeline()
        validate_motion(steps)
        self.assertAlmostEqual(steps[-1]['at'] + steps[-1]['duration'], TRACK['duration_seconds'])
        self.assertGreater(len(steps), 100)
        self.assertEqual(steps[-1]['pitch'], 0)

    def test_rpc_overhead_does_not_accumulate_over_full_song(self):
        clock = Clock()
        event = Event(clock)
        player = Player(clock)
        moves = []

        def move(step):
            moves.append(step)
            clock.now += step['duration'] + 0.08

        self.assertTrue(perform_auburn(move, event, player, clock.read))
        self.assertIsNotNone(player.stopped_at)
        elapsed = player.stopped_at - player.started_at
        self.assertLess(abs(elapsed - TRACK['duration_seconds']), 0.2)
        self.assertEqual(moves[-1]['pitch'], 0)

    def test_stop_ends_music_and_returns_neutral(self):
        clock = Clock()
        event = Event(clock)
        player = Player(clock)
        moves = []

        def move(step):
            moves.append(step)
            clock.now += step['duration']
            if len(moves) == 2:
                event.stopped = True

        self.assertFalse(perform_auburn(move, event, player, clock.read))
        self.assertIsNotNone(player.stopped_at)
        self.assertEqual(moves[-1]['name'], 'Return to neutral')
        self.assertEqual(moves[-1]['duration'], 2.0)

    def test_stop_before_start_does_not_play_audio(self):
        clock = Clock()
        event = Event(clock)
        event.stopped = True
        player = Player(clock)
        moves = []
        self.assertFalse(perform_auburn(moves.append, event, player, clock.read))
        self.assertEqual(moves, [])
        self.assertIsNone(player.started_at)


if __name__ == '__main__':
    unittest.main()
