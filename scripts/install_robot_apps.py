#!/usr/bin/env python3
"""Build and install selected local apps over SSH, without storing credentials.

Requires Python 3.11+, build, setuptools, wheel, ssh and scp. Run from a
terminal so SSH can request your existing robot password or key if needed.
Does not start a routine, change startup apps, or publish to an app store.
"""
import argparse
import json
from pathlib import Path
import re
import shlex
import subprocess
import sys
import tempfile
import urllib.request


PROJECTS = [('.', 'reachy-mini-customization'), ('apps/hello', 'hello'),
            ('apps/auburn_celebration', 'auburn_celebration')]
ACTIVE_STATES = {'starting', 'running', 'stopping'}


def api(host, path):
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    with opener.open('http://' + host + ':8000' + path, timeout=20) as response:
        return json.load(response)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--host', default='reachy-mini.local', help='Robot hostname or IPv4 address')
    parser.add_argument('--user', default='pollen', help='Existing robot SSH account')
    parser.add_argument('--known-hosts', type=Path, help='Optional existing SSH host-key file')
    parser.add_argument('--apps', nargs='+', choices=['hello', 'auburn_celebration'],
                        default=['hello', 'auburn_celebration'],
                        help='Apps to install (default: both); omitted apps are left alone')
    args = parser.parse_args()
    if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9.-]*', args.host):
        parser.error('--host must be a hostname or IPv4 address without a scheme or port')
    if not re.fullmatch(r'[A-Za-z_][A-Za-z0-9_-]*', args.user):
        parser.error('--user must be an SSH account name')
    repo = Path(__file__).resolve().parents[1]
    current = api(args.host, '/api/apps/current-app-status')
    if current and current.get('state') in ACTIVE_STATES:
        raise RuntimeError('Stop the active Reachy app before installing custom apps.')
    status = api(args.host, '/api/daemon/status')
    sdk_version = status['version']
    if not re.fullmatch(r'\d+\.\d+\.\d+', sdk_version):
        raise RuntimeError('Expected a stable robot SDK version before installing.')
    if tuple(int(part) for part in sdk_version.split('.')[:2]) < (1, 13):
        raise RuntimeError('Update Reachy to version 1.13 or later first.')
    dist = repo / 'dist'
    dist.mkdir(exist_ok=True)
    wheels = []
    expected = set(args.apps)
    projects = [project for project in PROJECTS
                if project[0] == '.' or project[1] in expected]
    for relative_path, name in projects:
        output = dist / name
        output.mkdir(exist_ok=True)
        subprocess.run([sys.executable, '-m', 'build', '--wheel', '--no-isolation',
                        '--outdir', str(output), str(repo / relative_path)], check=True)
        candidates = sorted(output.glob('*.whl'), key=lambda path: path.stat().st_mtime)
        if not candidates:
            raise RuntimeError('No wheel was built for ' + name)
        wheels.append(candidates[-1])
    # A short-lived SSH control socket avoids repeated password prompts.
    # It neither adds keys nor changes the robot's SSH authentication settings.
    with tempfile.TemporaryDirectory(prefix='reachy-app-', dir='/tmp') as temp:
        options = ['-o', 'ControlMaster=auto', '-o', 'ControlPersist=120',
                   '-o', 'ControlPath=' + str(Path(temp) / 'ssh'),
                   '-o', 'ConnectTimeout=10']
        if args.known_hosts:
            options += ['-o', 'UserKnownHostsFile=' + str(args.known_hosts.resolve())]
        target = args.user + '@' + args.host
        ssh = ['ssh', *options, target]
        remote_dir = None
        try:
            print('Connecting to Reachy over SSH; enter its existing password if requested.', flush=True)
            result = subprocess.run(ssh + ['mktemp -d /tmp/reachy-customizations.XXXXXX'],
                                    capture_output=True, text=True, check=True)
            remote_dir = result.stdout.strip()
            if not re.fullmatch(r'/tmp/reachy-customizations\.[A-Za-z0-9]+', remote_dir):
                remote_dir = None
                raise RuntimeError('SSH did not return the expected temporary staging directory.')
            subprocess.run(['scp', *options, *map(str, wheels),
                            target + ':' + remote_dir + '/'], check=True)
            python = '/venvs/apps_venv/bin/python'
            # Match the managed app SDK to the daemon rather than upgrading it
            # independently. Installed robot dependencies are otherwise preserved.
            check_version = 'import importlib.metadata as m; print(m.version("reachy-mini"))'
            result = subprocess.run(ssh + [shlex.join([python, '-c', check_version])],
                                    capture_output=True, text=True, check=True)
            if result.stdout.strip() != sdk_version:
                print('Synchronizing apps SDK to daemon ' + sdk_version, flush=True)
                subprocess.run(ssh + [shlex.join([python, '-m', 'pip', 'install',
                                                'reachy-mini==' + sdk_version])], check=True)
            remote_wheels = [remote_dir + '/' + wheel.name for wheel in wheels]
            command = shlex.join([python, '-m', 'pip', 'install', '--no-deps',
                                  '--force-reinstall', *remote_wheels])
            subprocess.run(ssh + [command], check=True)
            verify = 'expected = ' + repr(expected) + '\n' + '''from importlib.metadata import entry_points
from reachy_mini import ReachyMiniApp
found = {ep.name: ep.load() for ep in entry_points(group="reachy_mini_apps") if ep.name in expected}
assert found.keys() == expected, "Missing app entry point"
assert all(issubclass(cls, ReachyMiniApp) for cls in found.values())
print("Verified app imports without moving hardware: " + ", ".join(sorted(found)))
'''
            subprocess.run(ssh + [shlex.join([python, '-c', verify])], check=True)
            installed = api(args.host, '/api/apps/list-available/installed')
            if not expected <= {app['name'] for app in installed}:
                raise RuntimeError('Selected apps imported but were not discovered by the daemon.')
            print('Installed: ' + ', '.join(sorted(expected)) +
                  '. Reconnect Reachy Mini Control to refresh its list.', flush=True)
        finally:
            if remote_dir:
                cleanup = 'import shutil; shutil.rmtree(' + repr(remote_dir) + ')'
                subprocess.run(ssh + [shlex.join([python if 'python' in locals() else 'python3', '-c', cleanup])],
                               check=False)
            subprocess.run(['ssh', *options, '-O', 'exit', target],
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False)


if __name__ == '__main__':
    try:
        main()
    except (OSError, ValueError, RuntimeError, subprocess.CalledProcessError) as error:
        print('Install stopped: ' + str(error), file=sys.stderr)
        if isinstance(error, subprocess.CalledProcessError) and error.stderr:
            print(error.stderr, file=sys.stderr)
        raise SystemExit(1)
