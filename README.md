# Reachy Mini Customization

Personal movements and customizations for a Reachy Mini Wireless.

## Run a routine on macOS

1. Power on Reachy and connect your Mac to the same local network.
2. Stop other robot apps and leave Reachy Mini Control on its home screen.
3. Put Reachy on a clear, stable surface.
4. In Finder, double-click **Reachy Hello.command** or **Auburn Celebration.command**.

Keep the launchers and Python files together. Python 3 is required; no additional packages need installing. The routines communicate directly with the robot's local REST API and finish holding a neutral pose.

## Run from a terminal

```sh
cd ~/VsCodeProjects/reachy-mini-customization
python3 reachy_hello.py
python3 auburn_celebration.py
```

Run one routine at a time. To preview without connecting to or moving the robot:

```sh
python3 reachy_hello.py --dry-run
python3 auburn_celebration.py --dry-run
```

If the default hostname `reachy-mini.local` does not resolve, use the IP shown in Reachy Mini Control:

```sh
python3 reachy_hello.py --host ROBOT_IP
python3 auburn_celebration.py --host ROBOT_IP
```

Replace `ROBOT_IP` with the robot's current IPv4 address. Addresses can change when a router assigns a new lease.

## Included routines

| Routine | Behavior |
| --- | --- |
| Hello | A gentle nod and two alternating antenna wiggles. |
| Auburn celebration | Looks toward the stands, lifts into a touchdown pose, sways through “War Eagle,” and finishes with victory bobs. About 16 seconds including pauses. |

`reachy_hello.py` contains the shared `Robot` client and hello sequence. `auburn_celebration.py` imports that client and defines its own sequence. Both use only Python's standard library.

Edit `GESTURE` or `DANCE` to adjust timing and expression. Sequence angles are in degrees, optional `z_mm` is in millimeters, and durations are in seconds. The shared client converts these values to the API's units and applies conservative bounds for these routines: head angles within 15°, antenna angles within 40°, height offsets from −5 to 8 mm, and movements lasting at least 0.7 seconds. These are project limits, not the robot's maximum hardware limits.

## Robot setup and troubleshooting

- Reachy Mini Control v0.9.37 and robot software v1.13.0 were verified working on October 31, 2026. Both routines were physically tested before that update on robot software v1.2.3.
- If the desktop app still shows an old version after an update completed, disconnect and reconnect. In our setup, this cleared a stale “Robot update required” page even though the robot was already current.
- The routines refuse to start if another robot app or movement is active. On older robot software, they prime motor targets with the current position before enabling motors to avoid a sudden jump.
- Ctrl+C stops the script from sending further movements. A short movement already sent to the robot may finish. Keep the robot's physical power switch accessible.
- Routine errors appear in Terminal. The scripts leave the robot holding its last commanded pose rather than abruptly disabling torque.

Keep machine-specific addresses, credentials, recordings, logs, and session notes out of commits. Use ignored `agents.local.md` for local setup notes.

## References

- [Reachy Mini setup](https://pollen-robotics.com/reachy-mini/getting-started/)
- [Official SDK and API documentation](https://huggingface.co/docs/reachy_mini/index)
- [Official source code](https://github.com/pollen-robotics/reachy_mini)
