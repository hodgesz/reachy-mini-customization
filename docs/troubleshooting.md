# Troubleshooting and storage

## SDK 1.13.0 playback timing

An intermittent `time value is out of range [0,1]` from `goto_target`
can come from the daemon's `Backend.play_move`: it reads wall-clock time
twice, once to check the move duration and again to evaluate the move.
A scheduling delay between these reads can evaluate beyond the duration.
System-clock adjustments can also affect this loop.

`scripts/repair_sdk_113_timing.py` checks the exact known implementation
and replaces its playback clock with a single monotonic sample per loop.
It preserves the existing interpolation, Stop handling, and motor behavior.
It does not loosen trajectory bounds or change the dance's poses.

Copy the script to the robot, stop apps, and run it there:

```sh
/venvs/mini_daemon/bin/python repair_sdk_113_timing.py
/venvs/mini_daemon/bin/python repair_sdk_113_timing.py --apply
sudo systemctl restart reachy-mini-daemon.service
```

The script refuses unsupported SDK versions or unfamiliar code and makes
a backup before writing. Backups are stored on the robot under
`~/.local/share/reachy-mini-customization/backups/`. To undo, stop apps,
restore the reported original backup to the reported SDK file, and restart
the daemon. A future official SDK update may replace the repair; check
the installed implementation again rather than applying it blindly.

The regression test deliberately advances a fake clock across the duration
between the old loop's two reads. It reproduces the original error and
checks playback completion and cancellation after repair, without hardware.

## Failed Greetings update and low disk space

The October 2026 Greetings update pulled large vision dependencies,
including NVIDIA packages, and failed with `No space left on device`.
The updater had already removed the old Greetings package. Repeatedly
retrying the same installation can fill the disk again.

Use `df -h /` on the robot to check space and inspect the complete app-update
job log for the actual failure. `Using Python ... environment at ...` is
normal package-manager output even if Control displays it in red.

Rebuildable package download caches can be cleared without uninstalling apps:

```sh
/opt/uv/uv cache clean
/venvs/apps_venv/bin/python -m pip cache purge
df -h /
```

Run cleanup after installations finish. Keep app configuration and model/source
files unless you have identified them as disposable. Shared app environments
retain dependencies after an app is removed; deleting packages by size alone
can break other apps.

Hello and Hand Tracker were removed from this robot at the owner's request;
Greetings was left uninstalled. Hello's source and Finder launcher remain
available in the repository. To update Auburn without reinstalling Hello:

```sh
.venv/bin/python scripts/install_robot_apps.py --host ROBOT_IP --apps auburn_celebration
```

## Red Light Green Light plays sounds without moving

The original game starts sending movement commands without enabling motors.
After a session leaves Reachy in torque-off standby, the app can keep counting
and playing audio while the head remains down. The game deliberately uses a
lowered pose for counting, then should raise its head to scan players; remaining
limp throughout is a startup omission.

`scripts/repair_red_light_startup.py` adds motor enable followed by a slow,
2.5-second movement to upright before the first game round. SDK 1.13 pins motor
targets to the measured pose before enabling torque. The repair honors a Stop
request before movement, preserves the game's existing poses, and never disables
torque abruptly. Copy it to the robot, stop apps, then run:

```sh
/venvs/apps_venv/bin/python repair_red_light_startup.py --apply
```

It checks for an active app, saves the original file in the same robot backup
directory as the timing repair, and takes effect on the next game Start. No
daemon restart is needed. An official app update can replace this local repair.
Restore the reported backup while the game is stopped to undo it. Fake-hardware
tests cover startup from standby and Stop before or during initialization.

## Conversation and connection messages

The old Conversation app 0.1.0 reads `get_status()["simulation_enabled"]`,
but the current SDK returns a status model. Update from the official source
to use the current API; app settings and dependencies can differ between
versions.

Central signaling `connected -> reconnecting` messages describe the cloud
media connection. They do not by themselves indicate a motor fault.
Check whether the relay reconnects and whether local camera/media still work.
Local Auburn movement and audio do not depend on the cloud relay.
Control can label an app stopped through another client as "stopped
unexpectedly"; consult the process exit code and traceback before treating
that message as a crash.
