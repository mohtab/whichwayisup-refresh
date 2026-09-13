# Build status — 0.4.0rc4 public preview preparation, 2026-09-13

The player-facing README now leads with downloads, first-game controls, and links
to separate installation and player guides. The changelog and release notes use
plain-language descriptions. GitHub has issue forms and a pull-request template.
Codex (OpenAI) is explicitly credited for AI coding assistance.

67 automated tests pass locally. Packaging now rejects symlinked input directories,
handles special characters in local launcher paths, and includes the player guides
in the Arch package. CI verifies both sprite-contrast modes and installs the Arch
package in a disposable system. GitHub Actions passed on Python 3.11 and 3.13,
including all 15 campaign replays, 40 pixel checks per source job, and clean Arch
installation and launch. Release assets are taken from the passing workflow run. Earlier native rendering and campaign evidence
remain below; human and hardware coverage is documented in RELEASE_ACCEPTANCE.md.

The repository is prepared privately. Publish a preview for wider feedback; do not
present pending hardware or external playtests as completed stable-release checks.

---

# Build status — 0.4.0rc3 sprite edges, 2026-09-13

Modern player and enemy sprites now use a thin, dark, theme-tinted edge by default.
Settings → Display → High-contrast sprites restores the bright outline when wanted;
it defaults off for new and existing profiles and persists when changed. Original
art remains unchanged. The Display tab fits the extra setting without overlap.

65 automated tests pass, including saved toggle behavior. Native screenshots of
both appearances and the Display tab are in `docs/release-review/rc3-*.png`.
All 40 native Wayland pixel comparisons pass: five themes × four views with
high contrast off and on. Reports: `rc3-render-pixels.json` and
`rc3-high-contrast-pixels.json`.

---

# Build status — 0.4.0rc2 sprite rendering fix, 2026-09-13

Fixed a regression in the new final compositor: native Wayland display-format
canvases can retain an alpha mask with blending disabled. Copying them re-enabled
alpha blending, hiding finished sprite pixels. Presentation now treats fully
composed canvases as opaque RGB without changing source sprite transparency.

Reproduced with the actual Omarchy profile and native Wayland display, then visually
verified walls, player, enemies and items after the fix. The regression test
recreates that pixel format and fails before the fix in both full and board layouts.
65 automated tests pass. `tools/verify_render_pixels.py --desktop` compares actual
framebuffer pixels against RGB-only references across all five themes and four views;
all 20 comparisons pass on native Wayland and on the headless backend.

The rc1 native window/soak checks below established window operation and timing,
but did not detect this visual corruption. They must not be treated as visual
acceptance. Human/hardware release gates in RELEASE_ACCEPTANCE.md remain open.

---

# Build status — 0.4.0rc1 release candidate, 2026-09-13

Local offline release candidate. No public publishing or hosted services were enabled.

- Hardened legacy imports, all-device fullscreen confirmation and board notifications.
- Compact HUD; friendly stage labels, Continue, category-specific PBs in the library,
  campaign progression/results, PB deltas and one primary death retry action.
- Grouped settings, binding reset, controller-aware hints and D-pad support.
- Modern actor outlines and quieter wall interiors; smooth UI/HUD independent of
  crisp world presentation and optional Original integer fitting.
- Immutable PB replays and retryable failed completion saves. Previous progression
  stays intact if a later save fails.
- Metadata-derived version, explicit reproducible source manifest, Arch recipe and
  GitHub build/test/install workflow. CI workflow is prepared, not remotely executed.

64 automated tests pass. Source and extracted Arch package each pass 25 headless
startup/render checks. A real isolated 0.3.0 profile upgrade preserves settings,
bindings, a completed original-stage PB/replay, a custom stage and an unfinished draft.
This is profile-upgrade coverage, not a clean operating-system package install.

Native Wayland on a 2560×1600 desktop passed three fullscreen round trips (keyboard,
synthetic controller and mouse confirmation), timeout rollback, synthetic focus-loss
input clearing and settings/compact-HUD recovery. No physical controller is attached.

Final stable-source headless soak: 300.0s / 18,577 frames, median frame work 6.76ms, p95 10.53ms; no errors. Post-warmup RSS median increased 3.91 MiB. Finite sampling does not prove absence of leaks.

Final stable-source native soak: 120.0s / 7,323 frames, median work 9.94ms and p95 14.60ms; no errors. These are scripted measurements, not guaranteed sustained FPS.

All 15 original stages have retained completion input recordings that pass
independent re-simulation against unchanged stage hashes. The strict completion
gate passes. See [campaign-acceptance/README.md](campaign-acceptance/README.md). Human novice/runner
playtests, final art/music acceptance, physical controller/multiple-monitor/suspend
checks, clean OS installation and extended human play remain open. See
[RELEASE_ACCEPTANCE.md](RELEASE_ACCEPTANCE.md) for exact procedures and limitations.

Screenshots and final measurements: `docs/release-review/`. The ending screenshot is
explicitly a layout fixture, not evidence of campaign completion.

---

# Build status — 0.3.0 Cyberpunk art review, 2026-09-13

Private review build for mohtab/whichwayisup-refresh. Not a public release.

- Dedicated Cyberpunk courier and spider drone animations, titanium bulkheads,
  plasma spikes, security gates, industrial switches, plasma bolts, access keys,
  nanogel blobs, armored trousers and futuristic cake collectibles.
- Actual Omarchy emblem replaces keys in Omarchy/Follow Omarchy, with a gentle
  pulse and glow. Reduced effects freezes the pulse. Pickup and goal rules unchanged.
- Explicit atlas frame bounds preserve complete strides and tile edges. Source
  PNGs remain intact. Generated artwork prompts and upstream MIT logo notice included.
- Fresh-checkout instructions and source/Arch packaging. Local installer remembers
  its Python interpreter, including virtual environments.

42 automated tests pass. New tests cover every Cyberpunk sprite category, all atlas
frames, four-way spider contact across the scuttle cycle, Omarchy pulse and reduced
motion behavior. Earlier simulation, replay, profile and board-only checks also pass.

Native Wayland remained tiled alongside five mapped windows. A short scripted
rendering diagnostic measured median 14.15 ms and p95 15.44 ms frame work; not a
sustained FPS guarantee. Preview movie and screenshots: docs/cyberpunk-review-v4/.

Human art/playtesting acceptance and full campaign completion remain open. Global
scores and community hosting remain proposed; no online service is connected.
The current Git history scan found no credential-pattern matches or blobs over 50 MB.

---

# Build status — 0.2.2 materials and board-only play, 2026-09-13

Local visual review build; not a public release.

- F9 saved board-only preference: aspect-correct square playfield inside arbitrary
  tiled windows. No compositor mutation. Pause, Settings, dialogue and results stay
  reachable; focus loss pauses. Depth and board-only toggles are in Settings.
- Illustrated stone/brass tiles, sharp metal spikes, animated gear switches and
  directional crystalline projectiles. Actual wall faces determine spider foot contact.
- Omarchy's DHH uses a generated 24-pose atlas based on the observed public X portrait.
  Both characters have animated freefall body flutter, distinct from slow-fall glide.
- Optional cached software shading, local light response, glow and cast shadows.
  This is not a GPU shader implementation. Original simulation/collision rules remain.
- Assets, exact prompts and provenance accompany the source. No portrait photo bundled.

38 automated tests pass, covering board-only at portrait/landscape/square sizes,
no window resize/fullscreen calls during toggles, menu/dialogue/focus-loss recovery,
DHH animation, alpha preservation, non-mutating lighting, all four wall contacts,
and single lever activation events, plus previous physics/replay/profile checks.

Native Wayland: board-only remained tiled alongside five other mapped windows.
The 1280×774 window contained a 774×774 playfield. A short scripted diagnostic
measured median 8.79 ms and p95 13.06 ms frame work, not a sustained FPS guarantee.
Review movie, screenshots and reports: docs/visual-review-v3/.

Human acceptance, sustained sessions, full campaign completion and the proposed
online architecture remain release gates. No global scores or uploads are connected.

---

# Build status — 0.2.1 sprite polish, 2026-09-13

Local review build; not a public release.

- Illustrated explorer with scarf, goggles, six-frame stride, jump stretch, apex,
  falling/gliding poses, landing compression, damage recoil and collapse.
- Armored spiders with articulated scuttle poses and feet anchored to all four
  supporting directions, interpolated through room turns. Studio previews match.
- Ornate compass key with glint/sway animation; restrained pickup, landing and hit effects.
- World art rendered at 1040×1040, preserving more sprite detail when enlarged.
- Original theme and original physics remain available. DHH retains its existing art.
- Four intact generated PNG sheets, exact prompts and provenance in assets/sprites/.
  Arch packaging now includes these required assets.

32 automated tests pass. New checks cover actual jump/landing/damage events, four-way
spider contact, continuous rotation, uncut run strides, grounded crouches, frozen pause
poses and presentation that leaves physics and replay inputs unchanged.

Native Wayland scripted review observed takeoff, rising, apex, falling, gliding,
landing and hurt. Short diagnostic: median frame work 12.78 ms, p95 19.30 ms with
rendering/presentation; not a sustained FPS promise. Preview movie, screenshots and
native/headless reports are in docs/sprite-review-v2/.

Human art approval, sustained play and campaign completion remain release gates.
Online scores and uploads remain proposed, not implemented. Local replay validation
cannot establish that a human performed a run. The prior release gates below still apply.

---

# Build status — 0.2.0 local polish, 2026-09-13

A tested local review build. Not yet approved for a public release.

## Delivered in this pass

- F1 keyboard guide, F2 window sizes, F6/Shift+F6 themes, F10 in-game settings,
  F11 fullscreen, M music, Ctrl+S context-aware saving, F5 playtest and keyboard
  studio cursor/painting/tools/rotation. Shortcuts and custom binding hints visible.
- Redesigned home, settings, run HUD, results, records and Credits. Timer, ticks,
  attempts, health and category-specific PBs; Story/Speedrun presets; retry retains
  current rules. New procedural walking/rising/falling/gliding poses.
- Independent original SFX and synthesized ambient music with volume controls.
- Correct multiline/long-word wrapping, bounded titles and modal text, long-dialogue
  pages, single-press dialogue advance and adaptive tutorial control hints.
- Isolated preview/session globals, recoverable malformed records, save-error
  notifications and cleared stale menu callbacks.
- Mohtab Arabiat's credits and first-Linux-game story. Original creator/content/
  license notices retained in Credits; main-screen creator footer removed.
- Bounded local replay validator/re-simulator and per-PB replay files. Proposed
  public stage hub/leaderboard design and release gates in POLISH_PLAN.md.

## Verification

25 automated tests pass, including simulated novice, runner, creator, reduced-effects/
silent player, returning-player content and malformed-input workflows. All 15 original
stages load; original collision sampling, tempo and display-rate independence pass.
Actual stage completion and replay verification pass for a controlled user stage.
These are simulated profiles, not external playtester feedback or full playthroughs.

Native Wayland on a 2560×1600 desktop: four window presets verified at 800×532,
1000×668, 1200×800 and 1440×960 (HiDPI rounding), three fullscreen round trips,
rollback, and settings pause/resume. F2 uses a process/address-scoped Hyprland
adapter because tiled windows ignore ordinary SDL size requests. No desktop config
or global keyboard binding was changed. Other desktops retain SDL-only behavior.

180 scripted native frames: median work 8.45 ms, p95 11.01 ms. Includes rendering/
presentation, not a sustained FPS benchmark or hardware-independent guarantee.
Native window tests used dummy audio; music synthesis/mute was exercised in tests,
not assessed by a human listening session. Gallery and reports: `polish-review/`.

## Remaining release gates

- Mohtab's approval of art/music and human novice/speedrunner playtesting.
- Full completion of all 15 stages, real controller hardware, sustained sessions,
  suspend/resume, multiple monitors and broader platform/package install testing.
- A separately approved community architecture: authentication, moderation, hosting,
  costs, backups, privacy/terms and a hardened server replay worker. No global
  scoreboard, online upload or browsing service is currently connected.
- Hardened RTA/anti-cheat rules if desired; current records are local IGT, and replay
  determinism does not prove human play. Stage ZIP/asset packs remain future work.

Original files and Git history are retained, with a separate rollback backup made
before applying this pass. See POLISH_PLAN.md for sequencing and acceptance gates.

---

## Previous build record (historical)

# Build status — 0.1.0, 2026-09-12

This is a playable local build, not completion of every milestone in `REWORK_PLAN.md`.
No repository, public catalog or release has been published.

## Implemented

- Safe, resizable desktop application; native Wayland preference; fullscreen
  confirmation and 10-second rollback. New launches start in windowed mode.
- Five selectable visual treatments, independent character selection, editable accent,
  exportable TOML palette packs and live Omarchy palette reading at menu boundaries.
- Original assets and all 15 campaigns preserved and playable.
- New code-drawn Refresh / Omarchy / DHH / Cyberpunk art. These are revisable first
  designs, not an approved final art direction. Cyberpunk laser bolts preserve existing
  projectile rules.
- Independent display pacing and interpolation; selectable 0.75×–1.5× gameplay tempo.
- Shared asset/animation caches, indexed tile collision, bounded text caches, stable
  removal iteration, one-axis controller guard and audio fallback.
- Remappable primary keyboard bindings, generic controller input, mouse/menu controls,
  pause on focus loss, and controller-disconnect pause.
- Separate atomic XDG settings/records and a one-time preserved copy of old save metadata.
- Original and user-stage browser, validated JSON/TXT import, local authoring studio,
  undo/redo, board rotation, entity placement, goal/message editing, metadata, autosaved
  drafts, playtest, and JSON export. Resume the most recent draft from the library.
- Credits, full original notices, GPL text, source archive recipe, local application
  registration and a checksum-pinned Arch package recipe.

## Verification evidence

- Automated suite covers all original stage round-trips and simulation, 4,800 sampled
  collision comparisons across four rotations, timing independence at 30/60/120/144/240
  display rates, each supported tempo, stage-goal completion, stage authoring/import,
  malformed content, warm asset loading, non-mutating theme rendering and theme export.
- `desktop-verification.json` records actual **Wayland** tests on **2560 × 1600**:
  three fullscreen/windowed round-trips, rollback, play/pause, theme changes and editor
  playtest. Windowed size was ultimately managed by Hyprland at 1280 × 774.
- `legacy-comparison.json`: the first stage's scripted 221-frame trace matched the
  pre-refresh checkout for player position, health, gameplay timer and rotation.
  This is a sampled compatibility check, not a proof of exact whole-game equivalence.
- Comparable headless audit: image-load attempts **5,802 → 70**; profiled execution
  **3.779 s → 1.592 s**; cumulative tile collision **1.017 s → 0.051 s**. These are
  single-run diagnostic measurements, not promised end-user FPS improvements.
  See `legacy-profile.txt`, `refresh-profile.txt`, and their audit JSON files.
- Screenshots of the main themes and studio are in `docs/screenshots/`.

## Explicitly outstanding

- Collaborative final art direction and richer sprite animation, including refinement
  of the DHH cameo. Theme manifests currently customize palettes and built-in drawing
  styles; arbitrary image/sound replacement packs are not implemented yet.
- A distinct 120 Hz Modern physics profile, jump buffering/coyote time, true beam
  weapon variants and assist tuning. Current tempo uses the tested original 24 Hz
  rules, independent of render rate. This avoids claiming an unvalidated physics port.
- Successful full playthrough/completion replays of all 15 original stages. The audit
  exercises loading, movement and rotation; it does not establish campaign completion.
- Hardware controller testing, multiple monitors, suspend/resume, Windows/macOS/mobile,
  and sustained high-refresh performance/memory acceptance across devices.
- ZIP/asset packs, arbitrary event editing beyond the built-in goal controls, draft
  history browsing, public replay verification, hosted submissions/catalog, moderation
  and online leaderboards. Local JSON stages are the current community-content foundation.
- A publication review of final branding and all new asset provenance before distribution.

Original data and saves remain recoverable in the pre-build archive. The local launcher
points at this checkout, so moving/deleting it requires rerunning local installation.
