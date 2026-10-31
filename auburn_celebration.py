#!/usr/bin/env python3
"""War Eagle! A gentle, on-demand Auburn football celebration for Reachy Mini.

Run: python3 auburn_celebration.py
Preview: python3 auburn_celebration.py --dry-run
Keep reachy_hello.py in this same folder; no packages need installing.
"""

import argparse
import json
import sys
import urllib.error

from reachy_hello import Robot


# Angles are degrees, z_mm is millimeters, durations are seconds.
# Body stays facing forward; all movement is head and antennas.
DANCE = [
    dict(name='Get ready', pitch=0, antennas=[-10, 10], duration=2.5),
    dict(name='Check the left stands', pitch=-3, roll=-5, yaw=12, antennas=[-28, 12], duration=1.0),
    dict(name='Check the right stands', pitch=-3, roll=5, yaw=-12, antennas=[-12, 28], duration=1.2),
    dict(name='Touchdown! Proud head lift', pitch=-7, z_mm=5, antennas=[-8, 8], duration=1.0),
    dict(name='War — sway left', roll=-7, yaw=8, z_mm=2, antennas=[-30, 10], duration=0.8),
    dict(name='Eagle — sway right', roll=7, yaw=-8, z_mm=5, antennas=[-10, 30], duration=0.8),
    dict(name='Cheer left', roll=-7, yaw=8, z_mm=2, antennas=[-30, 10], duration=0.8),
    dict(name='Cheer right', roll=7, yaw=-8, z_mm=5, antennas=[-10, 30], duration=0.8),
    dict(name='Victory bob down', pitch=6, z_mm=0, antennas=[-22, 22], duration=0.8),
    dict(name='Victory bob up', pitch=-6, z_mm=5, antennas=[-8, 8], duration=0.8),
    dict(name='One more victory bob', pitch=6, z_mm=0, antennas=[-22, 22], duration=0.8),
    dict(name='War Eagle finale', pitch=-7, z_mm=5, antennas=[-8, 8], duration=1.0),
    dict(name='Return to neutral', pitch=0, antennas=[-10, 10], duration=1.5),
]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--host', default='reachy-mini.local', help='Robot hostname or IP, without port')
    parser.add_argument('--dry-run', action='store_true', help='Preview without contacting the robot')
    args = parser.parse_args()
    if any(char in args.host for char in '/:@?#'):
        parser.error('--host must be a hostname or IPv4 address, without a URL scheme or port')
    if args.dry_run:
        print(json.dumps(DANCE, indent=2))
        return
    print('War Eagle! Keep Reachy on a clear, stable surface.', flush=True)
    Robot(args.host).play(DANCE, label='Auburn celebration')


if __name__ == '__main__':
    try:
        main()
    except (urllib.error.URLError, TimeoutError, RuntimeError, KeyError, ValueError) as error:
        print('Celebration stopped: ' + str(error), file=sys.stderr)
        sys.exit(1)
    except KeyboardInterrupt:
        print('\nCelebration interrupted; any already dispatched short movement may finish.', file=sys.stderr)
        sys.exit(130)
