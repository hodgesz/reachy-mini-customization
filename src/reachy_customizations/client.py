"""Dependency-free LAN REST client for Mac command launchers."""
import json
import math
import time
import urllib.request

from .motions import HELLO, validate_motion

def radians(degrees):
    return math.radians(degrees)

def pose(pitch=0, roll=0, yaw=0, z_mm=0):
    return dict(x=0, y=0, z=z_mm / 1000, roll=radians(roll), pitch=radians(pitch), yaw=radians(yaw))

class Robot:
    def __init__(self, host):
        self.base = 'http://' + host.rstrip('/') + ':8000'
        self.http = urllib.request.build_opener(urllib.request.ProxyHandler({}))

    def api(self, path, payload=None, post=False):
        data = json.dumps(payload).encode() if payload is not None else (b'' if post else None)
        request = urllib.request.Request(
            self.base + path, data=data, headers={'Content-Type': 'application/json'}
        )
        with self.http.open(request, timeout=12) as response:
            return json.load(response)

    def wait_idle(self, timeout=15):
        deadline = time.monotonic() + timeout
        while self.api('/api/move/running'):
            if time.monotonic() > deadline:
                raise RuntimeError('The robot did not finish its movement in time.')
            time.sleep(0.2)

    def prepare(self):
        current = self.api('/api/apps/current-app-status')
        if current and current.get('state') in ('starting', 'running', 'stopping'):
            raise RuntimeError('Stop the currently running Reachy app before playing this greeting.')
        status = self.api('/api/daemon/status')
        if status.get('error'):
            raise RuntimeError('Robot controller error: ' + str(status['error']))
        if status['state'] != 'running':
            self.api('/api/daemon/start?wake_up=false', post=True)
            deadline = time.monotonic() + 25
            while True:
                status = self.api('/api/daemon/status')
                if status.get('error') or status['state'] == 'error':
                    raise RuntimeError('Robot controller failed to initialize: ' + str(status.get('error')))
                if status['state'] == 'running':
                    break
                if time.monotonic() > deadline:
                    raise RuntimeError('Robot controller initialization timed out.')
                time.sleep(0.5)
        if self.api('/api/move/running'):
            raise RuntimeError('Another movement is running. Wait for it to finish.')
        state = self.api('/api/state/full')
        mode = state['control_mode']
        if mode == 'disabled':
            # Older firmware does not pin targets before enabling torque.
            # Seed every target with the present position to avoid a sudden jump.
            self.api('/api/move/set_target', {
                'target_head_pose': state['head_pose'],
                'target_antennas': state['antennas_position'],
                'target_body_yaw': state['body_yaw'],
            })
            time.sleep(0.2)
            self.api('/api/motors/set_mode/enabled', post=True)
            time.sleep(0.2)
        elif mode != 'enabled':
            raise RuntimeError('Unsupported motor mode for this greeting: ' + str(mode))
        return self.api('/api/state/full')

    def play(self, steps=None, label='Greeting'):
        steps = HELLO if steps is None else steps
        validate_motion(steps)
        print('Before:', json.dumps(self.prepare()), flush=True)
        for step in steps:
            print(step['name'], flush=True)
            self.api('/api/move/goto', {
                'head_pose': pose(step.get('pitch', 0), step.get('roll', 0), step.get('yaw', 0), step.get('z_mm', 0)),
                'antennas': [radians(a) for a in step['antennas']],
                'body_yaw': 0,
                'duration': step['duration'],
                'interpolation': 'minjerk',
            })
            time.sleep(step['duration'] + 0.15)
            self.wait_idle()
            status = self.api('/api/daemon/status')
            backend = status.get('backend_status') or {}
            if status.get('error') or backend.get('error'):
                raise RuntimeError('Robot reported an error: ' + str(status.get('error') or backend.get('error')))
            print('Position:', json.dumps(self.api('/api/state/full')), flush=True)
        print(label + ' complete; Reachy is holding neutral.', flush=True)

    def play_auburn_with_music(self):
        import threading
        from .music import RESTMusicPlayer, perform_auburn
        player = RESTMusicPlayer(self)
        self.prepare()

        def move(step):
            self.api('/api/move/goto', {
                'head_pose': pose(step.get('pitch', 0), step.get('roll', 0),
                                  step.get('yaw', 0), step.get('z_mm', 0)),
                'antennas': [radians(angle) for angle in step['antennas']],
                'body_yaw': 0, 'duration': step['duration'], 'interpolation': 'minjerk',
            })
            time.sleep(step['duration'])
            self.wait_idle()

        return perform_auburn(move, threading.Event(), player)
