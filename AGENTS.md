# Project guidance

This repository holds personal Reachy Mini Wireless routines. Keep simple movements local, dependency-free, and easy to run from Finder or a terminal.

- Read `README.md` and ignored `agents.local.md` when present for setup context.
- Prefer connected tools for third-party services. Use another access method only when the connector cannot perform the requested action, and explain that limitation.
- Preview changes with `python3 reachy_hello.py --dry-run` and `python3 auburn_celebration.py --dry-run`. Check launchers with `zsh -n`. These checks must not contact or move the robot.
- Do not run physical routines as an incidental code check. Physical tests require an active user request covering robot movement and a clear, stable surface.
- Reuse `Robot` from `reachy_hello.py`; keep launchers and imported modules adjacent unless updating all affected paths together.
- Preserve smooth interpolation, conservative motion limits, current-pose target priming before enabling motors on older firmware, and a neutral finish.
- Avoid automatic disabling of torque on errors: the head can fall under gravity.
- Keep credentials, machine-specific network details, private logs, recordings, and session notes out of Git.
- Do not publish to an app store, add cloud accounts, enable automatic game triggers, or change robot startup behavior unless requested.
