"""Run a shared routine over the local REST API, or print a motion preview."""
import argparse
import json
import sys
import urllib.error

from .client import Robot
from .motions import LABELS, ROUTINES, validate_motion


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('routine', choices=ROUTINES)
    parser.add_argument('--host', default='reachy-mini.local', help='Robot hostname or IPv4 address')
    parser.add_argument('--dry-run', action='store_true', help='Preview without connecting to or moving Reachy')
    parser.add_argument('--no-music', action='store_true', help='Use the original short silent Auburn routine')
    args = parser.parse_args(argv)
    if any(char in args.host for char in '/:@?#'):
        parser.error('--host must be a hostname or IPv4 address without a scheme or port')
    steps = ROUTINES[args.routine]
    validate_motion(steps)
    if args.dry_run:
        if args.routine == 'auburn' and not args.no_music:
            from .music import TRACK, auburn_timeline
            print(json.dumps({'music': TRACK, 'settle_duration': 2.5,
                              'steps': auburn_timeline()}, indent=2))
        else:
            print(json.dumps(steps, indent=2))
        return 0
    try:
        print('Keep Reachy on a clear, stable surface.', flush=True)
        robot = Robot(args.host)
        if args.routine == 'auburn' and not args.no_music:
            robot.play_auburn_with_music()
        else:
            robot.play(steps, label=LABELS[args.routine])
    except (urllib.error.URLError, TimeoutError, RuntimeError, KeyError, ValueError) as error:
        print('Routine stopped: ' + str(error), file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        print('\nInterrupted; a short movement already sent may finish.', file=sys.stderr)
        return 130
    return 0


def hello_main():
    return main(['hello', *sys.argv[1:]])


def auburn_main():
    return main(['auburn', *sys.argv[1:]])
