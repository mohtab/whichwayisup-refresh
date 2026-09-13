# Which Way Is Up? — Omarchy Refresh

A playable desktop homage to Olli “Hectigo” Etuaho's 2007 platform game.
Turn the world, find the key, and choose how the adventure looks.

## Play

Requires Python 3.11+ and Pygame 2.6+. This machine already has both.

```sh
python run_game.py
```

The application starts safely in a resizable window. On a Wayland desktop it
prefers the native Wayland backend. Use **F11** for fullscreen, **Enter** to keep
that change, or **Esc** to revert. Unconfirmed fullscreen changes revert after
10 seconds. Every new launch starts windowed for recoverability.

```sh
python run_game.py --safe-window
python run_game.py --theme cyberpunk --play
python run_game.py --legacy
```

`--legacy` retains the original menu/game entry point. Its old display behavior is
unchanged; use the refresh launcher for modern window management.

Register this checkout in your application launcher without root:

```sh
python packaging/install_local.py
```

Then open **Which Way Is Up? — Refresh**, or run `whichwayisup-refresh`.

## Controls

| Action | Keyboard | Controller |
| --- | --- | --- |
| Move | Left / Right, A / D | Left stick |
| Jump / advance dialogue | Z, Up, Space | Button 1 |
| Pick up / pull lever | Down, S, E | Button 2 |
| Pause | Esc / P | Start (button 7 or 8) |
| Restart | R | Pause menu |
| Navigate menus | Tab / arrows / Enter, or mouse | Vertical stick / Button 1 |

Holding jump slows your fall, as in the original. Remap primary keyboard controls
in Customize; secondary keys remain available. Losing window focus pauses play.
Controller mappings are generic SDL joystick mappings; device-specific layouts
need verification on actual controllers.

## Five visual options

- **Original:** original assets, colors and levels with crisp scaling.
- **Refresh:** the initial warm/cool material design, ready for further art direction.
- **Omarchy:** an independent tribute featuring a stylized DHH cameo.
- **Follow Omarchy:** reads the current desktop palette and applies changes at a safe
  menu boundary. Falls back to Osaka Jade-derived colors outside Omarchy.
- **Cyberpunk:** circuit tiles, neon colors, mechanical spiders and laser-like bolts.

Choose the character independently. Override the accent in Customize; **Save theme
pack** creates an editable TOML file in the user-data `themes/` directory. Additional
palette roles can be edited there. Restart to discover new files. Packs contain data,
not executable plugins. Original sound remains available across designs.

This is a first playable art pass. Refresh and the DHH cameo are code-drawn and can
be revised; they are not the final collaboratively approved artwork.

## Smooth display and gameplay speed

The simulation retains the original 24 Hz rules and frame-based animations.
Presentation runs independently at 30, 60, 120, 144 or 240 FPS, interpolating positions
and rotation between simulation updates. Higher refresh is a target, not a guarantee
on every GPU/window size. Reduced Motion disables interpolation and effects.

Tempo options are **0.75×, 1×, 1.25× and 1.5×**. They alter the schedule of fixed
simulation steps, preserving per-step movement and collision distances. They do not
change physics based on display refresh. Tempo changes apply on the next run.
This build does **not** implement the proposed separately tuned 120 Hz Modern physics
profile, coyote time or jump buffering. The tested compatibility engine is the current
foundation. Local records distinguish content hashes, rules version and tempo.

No global leaderboard is enabled. Completion replays are recorded locally with a
one-hour input limit; longer recordings are marked incomplete. A public replay verifier
and complete campaign completion traces remain future validation work.

## Stage studio

Choose **Stage studio** or **New stage**. Paint walls, spikes or bars; place a spawn,
key, lever and enemies. Right-click erases. Set the spider's attachment direction.
The outlined lower-right region shows the initial playable viewport. Rotate the whole
board to inspect the other perspectives. Undo/redo works for edits and rotations.

Set the title and author. A goal event can complete the stage after collecting a key,
crystal, cake or pants. Edit its message, save, playtest, return to the studio, and export
JSON. Drafts autosave and can be restored with **Resume draft** in the stage library.
Remixing a bundled stage creates a separate copy and retains its attribution.

Import by dropping a JSON/TXT file into the game, using **Import file**, or:

```sh
python run_game.py --import-stage /path/to/stage.json
```

Version 1 stage files are bounded, data-only 20 × 20 boards. Invalid fields, unknown
entity/action types, unsafe IDs and non-finite coordinates are rejected. Zip packs,
custom scripts, online submissions and automatic downloads are not enabled.
See [the stage format](docs/STAGE_FORMAT.md) and [contribution guide](CONTRIBUTING.md).

## Saves and diagnostics

The refresh uses XDG paths under `whichwayisup-refresh`:

- Config: `~/.config/whichwayisup-refresh/settings.json`
- User data: `~/.local/share/whichwayisup-refresh/` (stages, drafts, exports, themes, records)
- Logs/cache: `~/.local/state/whichwayisup-refresh/`

Existing `~/.wwisup/config.txt` is copied once as `legacy-config.txt` and stored as
legacy record metadata; its original file and frame units are not overwritten. The
refresh opens all original stages for exploration. It does not silently merge old
records with new ones. `WWISUP_USER_DIR` provides an isolated root for testing.

## Build and verify

```sh
python -m unittest discover -s tests -v
SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy python run_game.py --smoke 2
python packaging/build_release.py
cd dist
makepkg
```

The source release includes all game code, data, license notices and build scripts.
The generated `PKGBUILD` pins the source archive's SHA-256. Installing the resulting
Arch package is a separate system action. A local launcher is sufficient for development.

Native window verification is in `docs/verify_desktop.py`; it deliberately opens and
changes the game window using temporary saves, then closes it. See [build status](docs/BUILD_STATUS.md)
for measured results and remaining work, and [credits](CREDITS.md) for all licensing.
