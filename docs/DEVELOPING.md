# Developer guide

For playing the game, start with the [install guide](INSTALL.md).

## Run from a checkout

```sh
git clone https://github.com/mohtab/whichwayisup-refresh.git
cd whichwayisup-refresh
python3 -m venv .venv
.venv/bin/python -m pip install 'pygame>=2.6,<3'
.venv/bin/python run_game.py
```

Python 3.11 or newer is required. Use the virtual environment’s Python for the
commands below. `pyproject.toml` is the source of the game version.

## Check a change

```sh
.venv/bin/python -B -m unittest discover -s tests -v
.venv/bin/python -B tools/campaign_acceptance.py --require-complete
.venv/bin/python -B tools/verify_render_pixels.py --output /tmp/render-pixels.json
```

The campaign check replays retained inputs against all 15 original stages. The
pixel check compares finished canvases with RGB-only references. Add `--desktop`
to check a real display, or `--high-contrast` to check bright sprite outlines.
Desktop checks open a temporary game window and use isolated saves.

The game retains the original 24 Hz simulation. Display refresh and interpolation
are separate; changing art must preserve collision geometry and replay results.
See [Contributing](../CONTRIBUTING.md) and [the stage format](STAGE_FORMAT.md).

## Build downloads

```sh
.venv/bin/python -B packaging/build_release.py
.venv/bin/python -B packaging/smoke_release.py --archive dist/whichwayisup-refresh-0.4.0rc4.tar.gz
```

The builder creates a complete source archive, `PKGBUILD`, and `SHA256SUMS` under
`dist/`. The source manifest excludes local caches and prior builds. Archive
metadata is normalized; `SOURCE_DATE_EPOCH` controls its timestamp.

On Arch Linux, build the package as a normal user:

```sh
cd dist
makepkg
```

GitHub Actions also checks supported Python versions and builds, installs, and
launches the Arch package in a disposable environment. A release draft should
contain the source archive, Arch package, `SHA256SUMS`, and readable release notes.
Preserve the exact artifacts tested by CI.

## Saves and diagnostics

Normal Linux saves use XDG config, data, and state directories under
`whichwayisup-refresh`. Set `WWISUP_USER_DIR` to an isolated folder for scripted
checks. Do not use your real player profile for acceptance fixtures.

A practice replay records inputs; it does not restore a suspended game. Verify an
exported replay with `python tools/verify_replay.py stage.json replay.json`.
Local records distinguish stage content, tempo, dialogue, and rules version.

Historical measurements live in [build status](BUILD_STATUS.md). Current release
checks and remaining hardware coverage are in [release acceptance](RELEASE_ACCEPTANCE.md).
