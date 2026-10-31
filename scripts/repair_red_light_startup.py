#!/usr/bin/env python3
"""Repair the known Red Light Green Light startup omission on the robot.

Default is check-only. --apply requires no active app and saves an original
backup. The next app Start uses the fix; no daemon restart is needed.
"""
import argparse
import ast
import hashlib
import json
import os
from pathlib import Path
import shutil
import urllib.request

ANCHOR = '        people_detector = PeopleDetector(model_path=pose_landmarker_path, max_poses=3)\n'
STARTUP = '''
        # Local compatibility repair: apps can start from torque-off standby.
        if stop_event.is_set():
            return
        reachy_mini.enable_motors()
        if stop_event.is_set():
            return
        reachy_mini.goto_target(
            head=np.eye(4), antennas=[0.0, 0.0], body_yaw=0.0, duration=2.5
        )
        if stop_event.is_set():
            return
'''


def repair_source(source):
    if source.count(ANCHOR + STARTUP) == 1:
        return source
    if source.count(ANCHOR) != 1 or 'reachy_mini.enable_motors(' in source:
        raise ValueError('Unrecognized game startup; no changes made.')
    tree = ast.parse(source)
    classes = [node for node in tree.body if isinstance(node, ast.ClassDef)
               and node.name == 'RedLightGreenLightApp']
    if len(classes) != 1:
        raise ValueError('Expected the known Red Light Green Light app.')
    repaired = source.replace(ANCHOR, ANCHOR + STARTUP)
    compile(repaired, '<repaired game>', 'exec')
    return repaired


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--apply', action='store_true')
    parser.add_argument('--site-packages', type=Path,
                        default=Path('/venvs/apps_venv/lib/python3.12/site-packages'))
    args = parser.parse_args()
    target = args.site_packages / 'red_light_green_light/main.py'
    source = target.read_text()
    repaired = repair_source(source)
    if repaired == source:
        print('Game startup repair is already present.')
        return
    if not args.apply:
        print('Missing motor-enable startup found. Stop apps, then use --apply.')
        return
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    with opener.open('http://127.0.0.1:8000/api/apps/current-app-status', timeout=10) as r:
        current = json.load(r)
    if current and current.get('state') in {'running', 'starting', 'stopping'}:
        raise RuntimeError('Stop the active app before applying the repair.')
    backup_dir = Path.home() / '.local/share/reachy-mini-customization/backups'
    backup_dir.mkdir(parents=True, exist_ok=True)
    backup_dir.chmod(0o700)
    digest = hashlib.sha256(source.encode()).hexdigest()[:16]
    backup = backup_dir / ('red-light-main-' + digest + '.py')
    if not backup.exists():
        shutil.copy2(target, backup)
    temporary = target.with_suffix('.py.repair-tmp')
    try:
        temporary.write_text(repaired)
        shutil.copymode(target, temporary)
        os.replace(temporary, target)
    finally:
        temporary.unlink(missing_ok=True)
    print('Repaired game startup. Original backup:', backup)
    print('The next app Start will enable motors and rise gently before counting.')


if __name__ == '__main__':
    main()
