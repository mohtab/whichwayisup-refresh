# 0.4.0rc4 release acceptance

This is an offline Linux preview. The release is prepared as a GitHub draft;
repository visibility and publication are separate final decisions. The current version is
read from `pyproject.toml` by the game and release builder.

## Implemented acceptance work

- Malformed legacy TXT files fail with field/line context instead of escaping the
  import handler. Original stage documents and collision rules are preserved.
- Fullscreen confirmation owns keyboard, mouse and controller input. Gameplay
  remains paused until the player explicitly resumes after confirming or reverting.
- Board-only notifications remain visible. Compact HUD adds time, attempts, health
  and the stage goal without covering the board. Dialogue and menus remain reachable.
- UI and HUD text scale smoothly; the board independently follows Crisp/Smooth.
  Original supports integer fitting when a native pixel scale fits the window.
- Modern walls have quieter interiors; explorers and enemies have subtle dark
  edges, with optional bright outlines under Display → High-contrast sprites. Original art and gameplay geometry are unchanged.
- Home Continue targets unfinished content; stage cards show completion and PBs for
  the selected tempo/dialogue category. Campaign results recognize each complete
  world and all 15 stages. Death has one retry action; results compare the prior PB.
- Settings are grouped into Display, Audio, Controls, Gameplay and Advanced. Primary
  bindings can be reset; generic controller button and D-pad navigation is supported.
- PB replays are immutable, content-addressed files referenced by their records.
  A failed save does not commit in-memory progression. Ctrl+S on results retries an
  unsaved completion. Old records and old replay files remain readable/preserved.
- Reproducible source archives use an explicit distribution manifest and normalized
  timestamps. Arch metadata points to the refresh project. CI definitions test
  source, package contents and installation in a disposable Arch environment.

## Reproduce automated verification

```sh
python -B -m unittest discover -s tests -v
python -B tools/verify_render_pixels.py --desktop
python -B tools/campaign_acceptance.py --require-complete
python -B tools/release_soak.py --duration 300 --warmup 150
python -B packaging/build_release.py
python -B packaging/smoke_release.py --archive dist/whichwayisup-refresh-0.4.0rc4.tar.gz --report dist/source-smoke.json
cd dist
makepkg
```

All 15 original stages now have verified completion recordings. The campaign
verifier re-simulates retained input files against original stage hashes. Its report explicitly distinguishes completed stages from missing proof;
`--require-complete` fails while any stage is unproven. See
[campaign acceptance](campaign-acceptance/README.md). This is completion evidence,
not proof that an external human played the release candidate.

For native window testing, run `python tools/release_window_check.py --desktop`
and `python tools/release_soak.py --desktop --duration 120`. These open a temporary game window with isolated saves. Native tests do not
change desktop configuration. Timing is measured separately from frame pacing;
reported work times are diagnostics, not guaranteed FPS. Audio in automated
acceptance uses SDL dummy output.

## Upgrade verification

`python packaging/verify_upgrade.py --from-archive dist/whichwayisup-refresh-0.3.0.tar.gz`
creates a real completed run and populated profile using 0.3.0, then opens it using
this release. The local check preserved preferences, custom bindings, PBs, original
PB replay bytes, a custom stage and an unfinished draft. This covers profile upgrade
compatibility; it is separate from installation on a clean operating system.

## Remaining human and hardware checks

These cannot be replaced by scripted tests or marked passed merely because code
exists. Record tester, date, hardware, build version and result for each check.

| Check | Acceptance | Status |
| --- | --- | --- |
| Blind novice session | Start from empty saves, learn movement/rotation, finish first stage, pause/settings/retry without help; record confusion | Pending external tester |
| Experienced runner | Complete a familiar stage twice, assess input feel and PB/retry flow; compare category and replay result | Pending external tester |
| Full campaign human playthrough | Finish all 15 stages and review dialogue, hazards and final results; record observed failures | Pending human playthrough |
| Art and music | Listen to loop transitions/volume balance and judge sprites at small window/fullscreen in all themes | Pending Mohtab review |
| Physical controller | Stick/D-pad, jump/hold/interact, menus, cancel, fullscreen, unplug/reconnect; note controller model and SDL mapping | Pending; no joystick device found locally |
| Suspend/resume | Suspend during play and pause; resume without time jump or held input; audio/window recover | Pending supervised workstation test |
| Multiple monitors | Move between differing scale/refresh displays; fullscreen confirm/revert restores usable window | Pending physical display test |
| Clean OS installation | Install built Arch package in disposable environment, launch from menu and terminal without checkout | Passed in GitHub Actions: package installed and launched in a clean Arch container |
| Extended human session | At least 30 minutes actual play, no crashes or growing input/audio latency; capture memory and logs | Pending human session |

## Release decision

The next public release remains scoped to local play, the original 24 Hz rules,
local records, themes and the stage studio. Online leaderboards, community hosting
and new physics are separate milestones. Their proposed architecture is not a
prerequisite for shipping the offline game.

A public preview can gather the remaining player and hardware feedback. A stable
release should follow review of those results. Keep the
source archive, checksum, Arch package, test report and verified campaign inputs
for the exact approved revision together.

## Visual fixtures

The rc3 `rc3-render-pixels.json` and `rc3-high-contrast-pixels.json` record 40 native
Wayland comparisons with high contrast off and on. `rc3-default.png`,
`rc3-high-contrast.png` and `rc3-display-settings.png` show both styles and the setting.

The rc2 `render-pixels.json` records 20 native Wayland framebuffer comparisons
against opaque RGB references. `rc2-native-play.png` and `rc2-native-home.png` show
the corrected sprites using a copy of the user's display preferences. Earlier rc1
window and timing checks did not detect the canvas-alpha regression and do not
establish visual acceptance.

Images under `docs/release-review/` are rendered from isolated user profiles.
`ending-layout-fixture.png` uses synthetic completion records solely to inspect the
ending layout; it is not campaign completion evidence. Soak JSON includes source
hashes and flags any concurrent code change. Only runs with stable source hashes
should be cited as final build measurements.
