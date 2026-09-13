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

| Action | Keyboard |
| --- | --- |
| Move | Left / Right, A / D |
| Jump / slow fall / advance dialogue | Z, Up, Space |
| Pick up / pull lever | Down, S, E |
| Pause / resume | Esc / P |
| Retry current stage and rules | R |
| Controls guide | F1 |
| Cycle window sizes | F2 |
| Next / previous theme | F6 / Shift+F6 |
| Settings, including during play | F10 |
| Board-only play / restore HUD | F9 |
| Fullscreen (Enter confirms, Esc reverts) | F11 |
| Music on / off | M |
| Save stage in studio; settings and practice replay during play | Ctrl+S |
| Studio playtest / export | F5 / Ctrl+Shift+S |
| Studio cursor / paint / erase | Arrows / Space / Delete |
| Previous / next studio tool | [ / ] |
| Studio undo / redo / rotate | Ctrl+Z / Ctrl+Y / Ctrl+R |
| Menu focus / activate | Tab, Shift+Tab, Up/Down / Enter |

Remap the primary movement keys in Customize. The extra keys above remain available;
conflicting bindings are rejected. A practice replay is an input recording, **not a
resumable checkpoint**. Stage completions and settings save automatically. Fullscreen
and size changes pause play. On Hyprland, F2 floats and resizes only this game window using the local compositor
API. It changes no desktop configuration. Other desktops use SDL resizing.

Generic controllers: horizontal stick moves, first button jumps/advances dialogue,
second interacts; buttons 7/8 pause (SDL indexes 6/7). Menu navigation uses the vertical
stick and first button. Hardware controller acceptance is still required.

## Run your way

Story keeps dialogue; Speedrun skips it and selects 1× tempo. Both presets apply to
the next stage. Restart keeps the current run's rules, even if you changed settings
while paused. The HUD shows in-game time, exact ticks, attempt count and personal best.
Personal bests compare stage content, rules, tempo and dialogue category. Older records
remain visible with an unknown-category label; they are not merged into new categories.

Version 0.2 uses `refresh24-v2`: original 24 Hz physics with isolated preview state and
single-press refresh dialogue. Pauses and scripted sequences are excluded by the legacy
in-game clock; this is not a real-time speedrun clock. Recorded pauses are metadata.
No global rankings or online uploads are live. See [the polish/release plan](docs/POLISH_PLAN.md).

The new scarf-wearing explorer has a six-frame run cycle, jump stretch, apex/fall/glide
poses, landing compression and hit recoil. Articulated spiders keep their feet against
the supporting surface, including during room rotation. A clockwork compass key
sways and glints. See [sprite preview and provenance](assets/sprites/README.md).
Music is an original synthesized ambient loop, off by default; music and original sound
effects have independent volume controls. Reduced effects retain smooth positioning
and essential character animation.

## Five visual options

- **Original:** original assets, colors and levels with crisp scaling.
- **Refresh:** warm brass and teal, with an illustrated explorer and clockwork creatures.
- **Omarchy:** an independent tribute featuring a stylized DHH cameo.
- **Follow Omarchy:** reads the current desktop palette and applies changes at a safe
  menu boundary. Falls back to Osaka Jade-derived colors outside Omarchy.
- **Cyberpunk:** circuit tiles, neon colors, mechanical spiders and laser-like bolts.

Choose the character independently. Override the accent in Customize; **Save theme
pack** creates an editable TOML file in the user-data `themes/` directory. Additional
palette roles can be edited there. Restart to discover new files. Packs contain data,
not executable plugins. Original sound remains available across designs.

Refresh uses generated raster sprite sheets, rendered at twice the logical resolution.
The Omarchy DHH cameo now has an illustrated 24-pose atlas inspired by his public X
portrait: long hair, short beard, expressive running, falling, gliding and hit poses. The Original theme preserves the original assets;
choose Refresh with F6 to see the new art. This is a local art review build.

## Smooth display and gameplay speed

The simulation retains the original 24 Hz rules and frame-based animations.
Presentation runs independently at 30, 60, 120, 144 or 240 FPS, interpolating positions
and rotation between simulation updates. Higher refresh is a target, not a guarantee
on every GPU/window size. Reduced effects disable particles and trails while keeping positioning and essential animation smooth.

Tempo options are **0.75×, 1×, 1.25× and 1.5×**. They alter the schedule of fixed
simulation steps, preserving per-step movement and collision distances. They do not
change physics based on display refresh. Tempo changes apply on the next run.
This build does **not** implement the proposed separately tuned 120 Hz Modern physics
profile, coyote time or jump buffering. The tested compatibility engine is the current
foundation. Local records distinguish content hashes, rules version and tempo.

No global leaderboard is enabled. Completion replays are recorded locally with a
one-hour input limit; longer recordings are marked incomplete. A local replay verifier is available:

```sh
python tools/verify_replay.py stage.json replay.json
```

It validates bounded schema-2 input and re-simulates actual completion and ticks. It
is not a hardened public worker or proof of human play. Full campaign completion
traces and the hosted verifier remain release work.

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

## Board-only play and scene depth (0.2.2)

Press **F9** during a stage, or choose **Board only / F9** in Settings. The square
playfield fills the available window while preserving its aspect ratio. This does
not float, resize or change the window manager layout; portrait, landscape and
square tiles work alongside other apps. Empty space is letterboxed. Esc restores
the pause menu; F10 opens Settings. Dialogue, results and fullscreen confirmation
temporarily show the interface so a run never silently waits for hidden controls.
Focus loss still pauses. The preference is saved.

Carved stone/brass tiles, metal spike plinths, animated gear switches and directional
crystalline bolts replace the earlier primitives in modern themes. Spider placement
uses the actual nearby supporting face; wall art fills the collision tile footprint.
**Depth** in Settings toggles software lighting: directional sprite shading, local
light response, glow and cast shadows. This is an SDL surface pass, not a GPU/GLSL
shader pipeline. It changes neither collision geometry nor replay inputs.

[Visual preview](docs/visual-review-v3/visual-review.mp4) ·
[New artwork prompts and reference provenance](assets/sprites/V3-PROMPTS.md)
