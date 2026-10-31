# Project guidance

Personal Reachy Mini Wireless routines. Keep movement definitions shared, local, and easy to launch.

- Read `README.md` and ignored `agents.local.md` for setup context.
- Prefer connected tools for third-party services. Explain capability limitations before using another access method.
- `commands/` contains Finder launchers. `src/reachy_customizations/` holds shared choreography, the REST CLI, and the SDK app adapter. `apps/` contains independently installable Reachy Mini Control entries. `scripts/` contains deployment tooling.
- Preview without hardware: `PYTHONPATH=src python3 -m reachy_customizations hello --dry-run` and the same command with `auburn`. Check launchers with `zsh -n commands/*.command`.
- Test adapter safety and Stop behavior with `PYTHONPATH=src python3 -m unittest discover -s tests`. Tests must never contact or move a robot.
- Physical tests require an active user request covering movement and a clear, stable surface. Installation and discovery checks should not start the routines incidentally.
- Keep choreography in `motions.py`. Both launch methods must use it; do not duplicate sequences in app packages.
- Preserve smooth interpolation, conservative limits, safe motor enable, and a neutral finish. Do not drop torque abruptly on errors.
- Local robot apps use SDK 1.13+ and must honor desktop Stop. They play once per Start; do not add loops or automatic startup without a request.
- Keep credentials, local IPs, private logs, recordings, and session notes out of commits.
- Do not publish to an app store, add cloud accounts, or enable automatic game triggers unless requested.
