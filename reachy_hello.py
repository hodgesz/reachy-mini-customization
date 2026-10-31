#!/usr/bin/env python3
"""A gentle Reachy Mini greeting. Uses only Python's standard library.

Run: python3 reachy_hello.py
Preview without connecting or moving: python3 reachy_hello.py --dry-run
Custom network address: python3 reachy_hello.py --host 192.168.1.58
"""

import argparse
import json
import math
import sys
import time
import urllib.error
import urllib.request


def radians(degrees):
    return math.radians(degrees)


def pose(pitch=0, roll=0, yaw=0, z_mm=0):
    return dict(x=0, y=0, z=z_mm / 1000, roll=radians(roll), pitch=radians(pitch), yaw=radians(yaw))


# Edit the angles (degrees) or durations (seconds) to personalize the greeting.
# Each antenna pair is [right, left]. All head coordinates use the robot frame.
GESTURE = [
    dict(name='Settle at neutral', pitch=0, antennas=[-10, 10], duration=2.5),
    dict(name='Hello nod', pitch=7, antennas=[-18, 18], duration=1.0),
    dict(name='Look up', pitch=-4, antennas=[-8, 8], duration=1.0),
    dict(name='Wiggle right', pitch=0, antennas=[-24, 8], duration=0.8),
    dict(name='Wiggle left', pitch=0, antennas=[-8, 24], duration=0.8),
    dict(name='Wiggle right again', pitch=0, antennas=[-24, 8], duration=0.8),
    dict(name='Wiggle left again', pitch=0, antennas=[-8, 24], duration=0.8),
    dict(name='Return to neutral', pitch=0, antennas=[-10, 10], duration=1.2),
]


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
        if self.api('/api/apps/current-app-status') is not None:
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
        steps = GESTURE if steps is None else steps
        for step in steps:
            if any(abs(step.get(axis, 0)) > 15 for axis in ('pitch', 'roll', 'yaw')):
                raise ValueError('Keep greeting and celebration head angles within 15 degrees.')
            if not -5 <= step.get('z_mm', 0) <= 8:
                raise ValueError('Keep head height offsets between -5 and 8 mm.')
            if len(step['antennas']) != 2 or any(abs(a) > 40 for a in step['antennas']):
                raise ValueError('Keep greeting and celebration antenna angles within 40 degrees.')
            if not 0.7 <= step['duration'] <= 5:
                raise ValueError('Use motion durations between 0.7 and 5 seconds.')
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


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--host', default='reachy-mini.local', help='Robot hostname or IP, without port')
    parser.add_argument('--dry-run', action='store_true', help='Show the gesture without contacting the robot')
    args = parser.parse_args()
    if any(char in args.host for char in '/:@?#'):
        parser.error('--host must be a hostname or IPv4 address, without a URL scheme or port')
    if args.dry_run:
        print(json.dumps(GESTURE, indent=2))
        return
    print('Keep Reachy on a clear, stable surface while it moves.', flush=True)
    Robot(args.host).play()


if __name__ == '__main__':
    try:
        main()
    except (urllib.error.URLError, TimeoutError, RuntimeError, KeyError, ValueError) as error:
        print('Greeting stopped: ' + str(error), file=sys.stderr)
        sys.exit(1)
    except KeyboardInterrupt:
        print('\nGreeting interrupted; any already dispatched short movement may finish.', file=sys.stderr)
        sys.exit(130)
