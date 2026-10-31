# Reachy Mini Customization

Personal Hello and Auburn football celebration routines for Reachy Mini Wireless. Run them from Reachy Mini Control or from the Mac launchers.

## Run from Reachy Mini Control

Once installed on the robot, the Applications list contains two entries:

- **hello** — a gentle nod and two alternating antenna wiggles.
- **auburn_celebration** — plays the complete 1955 “War Eagle” recording through Reachy's speaker while dancing with head lifts, antenna cheers, sways, and victory bobs. About 2 minutes 27 seconds of music, plus a short settling movement.

Click **Start** on either card to play it once. **Stop** ends the Auburn music and interrupts the sequence after a short current movement, returning smoothly toward neutral. The daemon then handles its normal idle behavior. These entries run on the robot; the Mac command files are not needed to play them. No Hugging Face sign-in or public app-store publication is required.

Keep Reachy on a clear, stable surface. Only one app can control it at a time.

## Run from Finder

Open `commands/` and double-click **Reachy Hello.command** or **Auburn Celebration.command**. Keep the repository folders together. The launchers find `src/` relative to their own location, so they work regardless of the current terminal directory.

These LAN launchers need Python 3.9+ and your Mac on the same Wi-Fi as Reachy. No extra Python packages are required. Stop any other robot app and leave Reachy Mini Control on its home screen before using a launcher.

## Repository layout

```text
commands/                   Mac double-click launchers
src/reachy_customizations/   Shared movements, REST CLI, SDK adapter
apps/hello/                 Hello desktop app package
apps/auburn_celebration/     Auburn desktop app package
scripts/                    Private local installation tooling
tests/                      Checks that do not move hardware
pyproject.toml              Shared Python package metadata
```

## Terminal use and previews

```sh
cd ~/VsCodeProjects/reachy-mini-customization
PYTHONPATH=src python3 -m reachy_customizations hello
PYTHONPATH=src python3 -m reachy_customizations auburn
```

Preview without connecting to or moving Reachy:

```sh
PYTHONPATH=src python3 -m reachy_customizations hello --dry-run
PYTHONPATH=src python3 -m reachy_customizations auburn --dry-run
```

The default address is `reachy-mini.local`. Override it with `--host ROBOT_IP` using the IP shown in Reachy Mini Control. The Finder launchers also forward these arguments when called from a terminal.

The Auburn command plays the full bundled song on the **robot's speaker**, including when launched from Finder. It uploads the MP3 to the robot's temporary sounds directory, then starts the music and scheduled dance together. Playback works without an Internet connection. Add `--no-music` for the original short, silent celebration; `--dry-run` prints the full music timeline without uploading or playing anything.

## Install or update the desktop entries

Use Python 3.11+ with `build`, `setuptools`, and `wheel` installed in a virtual environment. The robot must already run Reachy Mini 1.13+.

```sh
python3.12 -m venv .venv
.venv/bin/python -m pip install build setuptools wheel
.venv/bin/python scripts/install_robot_apps.py --host ROBOT_IP
```

The installer builds three wheels: the common library and one for each app. It transfers them over SSH into a temporary directory, installs them in the robot's managed apps environment, verifies both entry points, and removes the temporary files. Run it in a terminal so SSH can request your existing robot password or key. No credentials are saved. It does not start a routine, publish code to an app store, or change the startup app.

The app API in Reachy 1.13 only accepts Hugging Face Spaces for installation. Local private packages therefore use SSH for installation, while the supported app API discovers and launches them afterward.

After installation, reconnect Reachy Mini Control if its Applications list has not refreshed. Keep the app package versions and their shared-library dependency versions in sync when releasing changes. Run the installer again to deploy a new package version; GitHub pushes alone do not update robot code.

## Customize and verify

Edit `HELLO` or `AUBURN` in `src/reachy_customizations/motions.py`. Both desktop apps and Finder launchers read these same definitions. The musical Auburn performance uses the cheer poses as a repeating pattern across a fixed song-start timeline, with a neutral finish. Sequence angles are degrees, `z_mm` is millimeters, and durations are seconds.

Project limits are deliberately modest: head angles within 15°, antennas within 40°, height offsets from −5 to 8 mm, and motion durations of at least 0.7 seconds. These are routine limits, not the robot's maximum hardware limits.

```sh
PYTHONPATH=src python3 -m unittest discover -s tests
zsh -n commands/*.command
```

The tests use fake clients and clocks to verify unit conversion, complete playback, Stop handling, validation before motor enable, the recording checksum, and full-song scheduling without accumulated RPC delay. They do not contact a robot. Ctrl+C on a musical Auburn launcher stops the sound and returns to neutral after any short current movement. Keep the robot's power switch accessible.

## Music attribution

The bundled recording is **War Eagle - Auburn University Fight Song (1955 45rpm)**, credited to Auburn University and uploaded by Auburn University Libraries. The [Internet Archive item](https://archive.org/details/War_Eagle_1955_single) states [CC BY-NC-SA 4.0](https://creativecommons.org/licenses/by-nc-sa/4.0/). The original MP3 is unchanged; the music-and-dance adaptation follows the same terms. Source, checksum, duration, and attribution are included under `src/reachy_customizations/assets/`.

## Setup notes

- Desktop app v0.9.37 and robot software v1.13.0 were verified working on October 31, 2026. The original choreography was physically tested on 1.2.3 before the update.
- If an update completed but Control still shows the old version, disconnect and reconnect. This cleared a stale “Robot update required” page in this setup.
- Credentials, local IP addresses, logs, recordings, and session notes belong in ignored files such as `agents.local.md`.

## References

- [Reachy Mini setup](https://pollen-robotics.com/reachy-mini/getting-started/)
- [SDK and API documentation](https://huggingface.co/docs/reachy_mini/index)
- [Official app framework](https://github.com/pollen-robotics/reachy_mini/tree/main/src/reachy_mini/apps)
