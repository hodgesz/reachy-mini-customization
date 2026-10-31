"""Shared full-recording Auburn schedule and audio playback adapters."""
from copy import deepcopy
import json
from pathlib import Path
import time
import urllib.request
import uuid

from .motions import AUBURN, validate_motion

ASSETS = Path(__file__).resolve().parent / 'assets'
TRACK = json.loads((ASSETS / 'war_eagle_1955.json').read_text())
SOUND_FILE = ASSETS / 'war_eagle_1955.mp3'


def auburn_timeline():
    """Repeat bounded cheer poses on a fixed timeline, then end at neutral."""
    duration = TRACK['duration_seconds']
    beat = 60.0 / TRACK['movement_tempo_bpm']
    finale_duration = 2.0
    end_cheering = duration - finale_duration
    timeline = []
    cursor = 0.0
    pattern = AUBURN[1:-1]
    index = 0
    while cursor < end_cheering - 1e-6:
        pose = deepcopy(pattern[index % len(pattern)])
        desired = beat * (3 if pose['duration'] >= 1.1 else 2)
        remaining = end_cheering - cursor
        if remaining < 0.7 and timeline:
            timeline[-1]['duration'] += remaining
            cursor = end_cheering
            break
        length = min(desired, remaining)
        pose.update(at=cursor, duration=length)
        timeline.append(pose)
        cursor += length
        index += 1
    finale = deepcopy(AUBURN[-1])
    finale.update(at=end_cheering, duration=finale_duration)
    timeline.append(finale)
    validate_motion(timeline)
    return timeline


def perform_auburn(move, stop_event, player, clock=time.monotonic):
    """Use one song-start clock; RPC overhead does not accumulate per pose."""
    timeline = auburn_timeline()
    if stop_event.is_set():
        return False
    completed = False
    moved = False
    started = False
    try:
        # Raise gently from standby before playing the recording.
        moved = True
        move(deepcopy(AUBURN[0]))
        if stop_event.is_set():
            return False
        started = True
        player.start()
        epoch = clock()
        print('Playing full War Eagle recording (about 2 minutes 27 seconds).', flush=True)
        for scheduled in timeline:
            if stop_event.wait(max(0.0, epoch + scheduled['at'] - clock())):
                return False
            remaining = epoch + scheduled['at'] + scheduled['duration'] - clock()
            # If a slow network call missed a beat, skip that cue instead of
            # compressing it into an abrupt movement or delaying the whole song.
            if remaining < 0.7 and scheduled is not timeline[-1]:
                continue
            pose = dict(scheduled)
            pose['duration'] = max(0.7, min(scheduled['duration'], remaining))
            move(pose)
        if stop_event.wait(max(0.0, epoch + TRACK['duration_seconds'] - clock())):
            return False
        completed = True
        return True
    finally:
        try:
            if started:
                player.stop()
        finally:
            if moved and not completed:
                neutral = deepcopy(AUBURN[-1])
                neutral['duration'] = 2.0
                move(neutral)
            print('Auburn celebration ' + ('complete.' if completed else 'stopped.'), flush=True)


class SDKMusicPlayer:
    def __init__(self, media):
        if not SOUND_FILE.is_file():
            raise FileNotFoundError('The bundled War Eagle recording is missing.')
        if media.audio is None:
            raise RuntimeError('Auburn music requires an initialized robot audio backend.')
        self.media = media

    def start(self):
        self.media.play_sound(str(SOUND_FILE))

    def stop(self):
        self.media.stop_playing()


class RESTMusicPlayer:
    def __init__(self, robot):
        self.robot = robot
        boundary = 'reachy-' + uuid.uuid4().hex
        content = SOUND_FILE.read_bytes()
        header = ('--' + boundary + '\r\nContent-Disposition: form-data; name="file"; '
                  'filename="war_eagle_1955.mp3"\r\nContent-Type: audio/mpeg\r\n\r\n').encode()
        body = header + content + ('\r\n--' + boundary + '--\r\n').encode()
        request = urllib.request.Request(
            robot.base + '/api/media/sounds/upload', data=body,
            headers={'Content-Type': 'multipart/form-data; boundary=' + boundary},
        )
        with robot.http.open(request, timeout=60) as response:
            self.remote_path = json.load(response)['path']

    def start(self):
        self.robot.api('/api/media/play_sound', {'file': self.remote_path})

    def stop(self):
        self.robot.api('/api/media/stop_sound', post=True)
