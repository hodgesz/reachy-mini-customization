#!/usr/bin/env python3
"""Check or repair the Reachy Mini 1.13.0 playback clock race on the robot.

This changes the installed daemon SDK, not choreography. A daemon restart is
required after --apply. Run only while apps are stopped. Updates may replace
the fix; recheck the installed version before applying it again.
"""
import argparse
import ast
import hashlib
import os
from pathlib import Path
import shutil


OLD_LOOP = '''                while time.time() - t0 < move.duration:
                    if self._stop_move_requested or ('''
NEW_LOOP = '''                while True:
                    # Sample once on a clock unaffected by system-time updates.
                    t = time.monotonic() - t0
                    if t >= move.duration:
                        break
                    if self._stop_move_requested or ('''


def repair_source(source):
    """Patch only the known 1.13 playback method; reject unfamiliar source."""
    tree = ast.parse(source)
    matches = [node for node in ast.walk(tree)
               if isinstance(node, ast.AsyncFunctionDef) and node.name == 'play_move']
    if len(matches) != 1:
        raise ValueError('Expected exactly one play_move method; no changes made.')
    node = matches[0]
    lines = source.splitlines(keepends=True)
    method = ''.join(lines[node.lineno - 1:node.end_lineno])
    if NEW_LOOP in method and 'time.time()' not in method:
        return source
    expected = [OLD_LOOP, '            t0 = time.time()',
                '                    t = time.time() - t0\n',
                '                    elapsed = time.time() - t0 - t']
    if any(method.count(fragment) != 1 for fragment in expected):
        raise ValueError('Unrecognized playback implementation; no changes made.')
    repaired = method.replace('t0 = time.time()', 't0 = time.monotonic()')
    repaired = repaired.replace(OLD_LOOP, NEW_LOOP)
    repaired = repaired.replace('                    t = time.time() - t0\n', '')
    repaired = repaired.replace('elapsed = time.time() - t0 - t',
                                'elapsed = time.monotonic() - t0 - t')
    if 'time.time()' in repaired:
        raise ValueError('Unexpected wall-clock use; no changes made.')
    lines[node.lineno - 1:node.end_lineno] = [repaired]
    result = ''.join(lines)
    compile(result, '<repaired SDK>', 'exec')
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--apply', action='store_true', help='write fix and backup')
    parser.add_argument('--sdk-root', type=Path,
                        default=Path('/venvs/mini_daemon/lib/python3.12/site-packages'))
    parser.add_argument('--backup-dir', type=Path,
                        default=Path.home() / '.local/share/reachy-mini-customization/backups')
    args = parser.parse_args()
    from importlib.metadata import Distribution
    # Old image builds can leave an egg-info record beside the active wheel.
    # Check the current wheel's metadata, then verify its exact method below.
    metadata = args.sdk_root / 'reachy_mini-1.13.0.dist-info'
    if not metadata.is_dir() or Distribution.at(metadata).version != '1.13.0':
        parser.error('This repair supports only the known SDK 1.13.0 implementation.')
    target = args.sdk_root / 'reachy_mini/daemon/backend/abstract.py'
    source = target.read_text()
    repaired = repair_source(source)
    if repaired == source:
        print('Playback clock repair is already present.')
        return
    if not args.apply:
        print('SDK 1.13.0 playback race found. Use --apply while apps are stopped.')
        return
    digest = hashlib.sha256(source.encode()).hexdigest()[:16]
    args.backup_dir.mkdir(parents=True, exist_ok=True)
    backup = args.backup_dir / ('abstract-' + digest + '.py')
    if not backup.exists():
        shutil.copy2(target, backup)
    temporary = target.with_suffix('.py.repair-tmp')
    try:
        temporary.write_text(repaired)
        shutil.copymode(target, temporary)
        os.replace(temporary, target)
    finally:
        temporary.unlink(missing_ok=True)
    print('Repaired:', target)
    print('Original backup:', backup)
    print('Restart reachy-mini-daemon.service while the robot is idle.')


if __name__ == '__main__':
    main()
