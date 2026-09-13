# Which Way Is Up? — modern homage rework

Planning baseline: 12 September 2026. Status: implementation plan, not an implemented release.

## Intent and working decisions

Create an explicitly credited refresh of Olli “Hectigo” Etuaho’s *Which Way Is Up?*, centered on Omarchy but usable on other Linux desktops. Preserve the original artwork and campaigns as a first-class playable option. Add customizable presentation, smooth modern display behavior, optional faster play, and a path to community-created stages.

Use “Which Way Is Up? — Omarchy Refresh” as an internal working title. Public naming remains a creative decision. Present the project as an independent homage; retain the original author's credit prominently in the title screen/About view, repository, packaging and credits. The refresh maintainer receives separate adaptation credit.

Decisions for implementation:

- Keep Python and Pygame/SDL for the first release. Modernize the small existing engine incrementally. The measured workload does not justify an engine migration now.
- Linux desktop first, with Omarchy/Hyprland the primary validation target. Include laptops, high-DPI monitors, external displays and Linux handheld/controller layouts. Windows/macOS are portability targets after Linux acceptance; mobile/touch and browser builds are later product milestones, not implied launch support.
- Preserve the 520 × 520 logical playfield and the original 20 × 20 tile map. A larger window must not reveal hidden parts of a rotating stage or stretch the puzzle geometry. Put additional interface space around the playfield.
- Keep visual theme, character selection, gameplay rules, and stage pack independent. Offer curated presets that combine them, with individual overrides.
- Introduce local theme and stage packs before an online service. No accounts or network dependency for ordinary play.
- Finish one representative playable slice before replacing every asset or building the editor.

## What the current checkout establishes

The repository contains approximately 3,104 lines across 28 Python files. Three world lists reference 15 playable campaign stages: 7 + 7 + 1. There are additional template/older stage files, which are not campaign entries. Existing local edits already convert much of the game to Python 3; preserve and inventory these before reorganizing the code.

| Evidence | Consequence |
| --- | --- |
| `lib/locals.py`: `FPS = 24`; movement and gravity are applied per update | Raising the FPS constant also accelerates gameplay. The “pixels per second” comment does not match the actual update behavior. |
| `lib/game.py`: one loop handles input, updates, animation effects, rendering and scoring | Split simulation and presentation clocks before adding high-refresh support. |
| `lib/visibleobject.py`: rendering advances animation and updates object rectangles | Make rendering read-only; create simulation-owned collision shapes and update animation on the correct clock. |
| `lib/level.py`: collision loops over all active tiles; ground checks memoize stringified coordinates | Use spatial tile lookup with explicit invalidation and stable coordinate keys. |
| `lib/frame.py` / `lib/animation.py`: images and animation definitions are repeatedly loaded at construction | Share decoded assets and immutable animation definitions, while keeping each object's playback state independent. |
| `lib/game.py`: removal from object/particle lists during iteration | Use deferred spawning/removal to avoid skipped updates and order-dependent behavior. |
| `lib/menu.py`: the menu background is read inside the menu loop | Load once through the asset manager. |
| `lib/projectile.py`: projectile collision uses a few points | Add swept collision for genuinely faster projectiles to prevent tunneling. |
| `lib/main.py`: audio initialization is mandatory | Continue without audio when a device is missing, disconnected or unavailable. |
| `lib/level.py`: custom text stages, built-in triggers and rudimentary editing already exist | Import legacy content into a validated format; build on its concepts instead of discarding it. |

A bounded audit loaded all 15 stages and ran 241 loop iterations each with synthetic movement/jumps and requested rotations, dummy video/audio, a fixed random seed, and clock sleeping removed. All returned the expected requested-quit result. This is not a completion test or a real-display benchmark.

Across that run: 5,802 image-load attempts; about 3.779 seconds of profiled execution; about 1.017 seconds cumulatively in tile collision and 1.267 seconds in surface blits. Cumulative times overlap and must not be added. Existing missing-asset fallbacks were logged for broken key, pants, crystal and cake sprites. Investigate whether those animation states should exist before drawing replacements.

Audit artifacts: [method and per-stage results](docs/legacy-audit.json), [profile](docs/legacy-profile.txt), [reproducible harness](docs/audit_legacy.py). Run `python docs/audit_legacy.py` to regenerate them; it uses temporary save data. Its forced inputs and debug rotations exercise code paths but do not prove level solvability or every trigger branch.

The earlier fullscreen disappearance remains unexplained: no process/window remained when inspected, but no exception was captured. Saved fullscreen was reset to off. Treat diagnosis and repeated native-window tests as the first implementation milestone, not as an already fixed bug.

## Presentation and customization

All five options must support all original campaign stages. Theme selection includes a preview room containing the player, spider, projectile, spikes, lever, collectible and dialogue. Previewing must not change the active save.

| Option | Art direction and behavior |
| --- | --- |
| **Original** | Ship the original backgrounds, sprites, colors and sound intact, with attribution. Default to nearest-neighbor scaling. Provide an Original Experience preset pairing these assets with Classic rules and original dialogue. Modern application controls remain accessible. |
| **Refresh** | Our collaboratively developed design: begin with expressive silhouettes, readable materials, cleaner typography and stronger hazard contrast. Produce three small art directions in one playable room before committing to a full sprite set. |
| **Omarchy / DHH** | An Omarchy-inspired visual identity and a newly drawn, stylized DHH player character with idle, run, jump, fall, hurt, exit and rotation states. Keep the cameo selectable separately from the world theme. State that this is an unofficial homage, without implying DHH or Omarchy endorsement. |
| **Follow Omarchy** | Adapt interface, tiles, backgrounds and effects to the installed desktop palette. Use purpose-built recolorable art rather than blindly recoloring Original assets. Include a “pin these colors” option. |
| **Cyberpunk** | Dark industrial rooms, bright cyan/magenta/lime accents, emissive circuit tiles, mechanical spiders, neon laser bolts, trails and impact sparks. Hazards stay recognizable without relying on color alone. |

Cyberpunk spiders initially fire laser-looking bolts with the same travel, damage and collision rules as the chosen gameplay mode. Actual beam weapons are a later, separately declared enemy variant: visible charge-up, line-of-sight blocking, firing duration and cooldown, plus a stage/rules identifier. A cosmetic selection must never secretly turn a dodgeable bolt into an instantaneous attack.

Theme packs contain a versioned TOML manifest, palette roles, asset mappings, sprite anchors, animation metadata, UI typography, sound mappings, effect defaults, authors and licenses. Resolution order: user overrides → selected theme → compatible shared defaults. Missing content must have a deliberate fallback and a useful diagnostic. Collision boxes belong to gameplay definitions, never to sprite dimensions. Cache identity includes theme, asset version, scale and orientation.

Expose palette overrides, character, UI scale, pixel/smooth filtering, effect strength and sound pack. User changes save as a new preset and can be reverted. Keep hit flashes, shake, scanlines and flashes optional; offer reduced motion and a low-effects preset. Bright neon should remain readable, with no forced strobing. Theme changes apply at a safe boundary after assets load successfully.

### Follow the real Omarchy installation

On this machine the active theme is **Osaka Jade**. Installed scripts use:

- `~/.local/state/omarchy/current/theme.name`
- `~/.local/state/omarchy/current/theme/colors.toml`

The older `~/.config/omarchy/current/theme` location is absent here. Resolve XDG defaults and known legacy locations rather than assuming one path works across all Omarchy releases. Read palette data only. Do not execute theme scripts or copy desktop settings into the game.

Map background/foreground/accent/selection/muted plus semantic warning, hazard, collectible and focus colors. Osaka Jade's current accent is `#509475`, background `#111c18`, and foreground `#C1C497`. Derive and contrast-check game colors; do not assume a color named “yellow” is literally yellow. Preserve hazard outlines when a palette has similar colors.

Watch the parent directory or periodically check its generation/mtime at low frequency: the installed theme setter replaces the theme directory during changes. Debounce updates and retain the last valid palette while a replacement is incomplete. Rebuild affected caches off the gameplay path, then swap at a menu/pause boundary. If Omarchy is unavailable, retain the saved palette or use a bundled fallback. Never change the user's system theme.

## Engine, speed and modern displays

### Two rulesets, independent display refresh

**Classic:** fixed 24 Hz simulation reproducing the legacy game's timing, jump trajectories, enemy behavior, rotation durations and speedrun timer. Render at 60/120/144/240 Hz as supported, with interpolated positions and rotations. Original sprite animation may retain its original cadence. Provide a strict presentation option if interpolation visually differs from the original.

**Modern:** target a fixed 120 Hz simulation, with 60 Hz default rendering and selectable higher refresh. Convert acceleration, gravity, drag, jump hold, invulnerability, fire cooldowns, particle lifetime, animation duration, fades and dialogue timing to explicit units. Derive initial tuning from the legacy motion and verify jump apex, range and landing behavior. Converting constants alone is insufficient because integration and collision order also affect the result.

Modern defaults start at 1.0× tempo. Offer 0.75×, 1.0×, 1.25× and 1.5×; expose 2.0× only after collision and stage testing. Apply tempo to accumulated simulation time, not monitor refresh or the integration step. Catch-up work is bounded; on a stall, pause or report a simulation overrun instead of silently dropping ranked simulation time. Unranked assisted play may recover with an explicitly documented policy. Faster rotation, coyote time and jump buffering belong to Modern/assist settings with versioned values.

Poll and queue input independently of rendering, consuming each press once even when several simulation steps run. Classic input remains quantized to its original tick. Modern can respond more frequently. Freeze both gameplay and interpolated motion on pause, focus loss and suspend; reset the accumulator on resume.

Keep legacy records in their original 24 Hz units. Store new elapsed time explicitly, along with stage content hash, rules version, tempo, assists and engine compatibility version. Maintain separate result categories. Skin choice does not affect scoring. Replays record tick-indexed inputs and seeded gameplay randomness; effects use a separate random stream. Only promise deterministic replay for tested engine/rules versions.

### Display and input behavior

Render the logical world to an offscreen canvas and scale it into a centered viewport. Size the interface separately so text remains readable. Default to a window fitting the usable monitor area; remember a validated size and position. Support arbitrary aspect ratios, fractional desktop scaling and monitor changes without exposing more of the stage. Original mode uses integer scaling where practical; small displays need a fit-to-window fallback.

Implement windowed and desktop-resolution fullscreen, with a tested exit shortcut and a timed “keep display setting” rollback. Add `--safe-window` for recovery from a bad saved setting. Capture display driver, SDL/Pygame versions and exceptions in a local diagnostic log. Test native Wayland first, with explicit XWayland fallback where necessary. Avoid globally changing the compositor, monitor mode or desktop scale.

Provide keyboard remapping, controller mappings and prompts, configurable dead zones, hotplug handling, and sensible pause behavior on controller disconnect. Fix the existing joystick branch that can read axis 1 when a device has only one axis. Menus need keyboard, controller and mouse support. Touch input and mobile packaging require their own later design pass.

## Optimization work and acceptance targets

| Priority | Change | Evidence and success criterion |
| --- | --- | --- |
| P0 | Establish repeatable profiling and display diagnostics | Measure load time, simulation/render p50/p95/p99, input response, allocations and resident memory on the actual device. Separate cold-load, warm-play, menu, rotation and effects-heavy samples. |
| P1 | Shared asset/animation cache; preload stage/theme dependencies | Eliminate image loading and animation-file parsing during warm gameplay and menu rendering. Measure unique-load counts before/after. Bound cache memory and discard retired theme generations. |
| P1 | Tile-grid broad phase | Query only overlapped/adjacent cells while preserving spikes and one-way bars. Differential collision tests compare against legacy traces where behavior should be unchanged. Rebuild indices atomically after rotation/edit. |
| P1 | Separate visual transforms from collision state | Cache left/right/up/down sprites; remove alpha mutation of shared surfaces. Stage rotation uses reusable surfaces and exact end-state coordinates. Do not rotate an entire cached image until its clipping/pivot behavior matches the original. |
| P1 | Stable object lifecycle | Queue spawning/removal, bound projectile/particle lifetimes and counts, avoid skipped updates. Pool objects only if allocation profiling justifies it. |
| P2 | Controlled glow and effects | Reuse glow sprites and lower-resolution effect buffers; cap particles and cull offscreen effects. Never lower simulation quality to raise visual FPS. |
| P2 | Bounded caches and reliable I/O | Fix stale ground checks after edits, avoid caches keyed by unbounded float strings, bound text caches, close files, narrow broad exceptions and write saves atomically. |

Initial targets, to be validated rather than advertised as achieved: consistent 60 FPS on the user's machine at its normal 2560 × 1600 / 2× desktop scale; p95 application CPU work below 8 ms per frame in the benchmark scenario at 60 FPS; no repeating 50+ ms stalls after warm-up; no sustained memory growth across 20 stage restarts and 20 theme changes. Measure 120/144/240 Hz modes separately. Record CPU/GPU, driver, effects tier and resolution with results. High-refresh and battery-saver modes have different budgets; avoid uncapped busy loops.

## Community stages: design now, ship incrementally

Introduce a versioned JSON stage format with stable IDs, title, author, description, license, schema version, supported rules, tile grid, player spawn, entities, built-in triggers, difficulty tags and dependencies. Retain a legacy `.txt` importer and preserve all original campaign content. Version stage packs independently from saves and themes. Theme hints are optional; player theme overrides remain possible.

For format v1, retain the proven 20 × 20 rotating board. Larger/arbitrary layouts require an explicit camera and rotation design; they are not automatically supported by accepting larger JSON arrays.

Validation covers tile dimensions, coordinates, legal entity types, exactly one player spawn, trigger references, finite numeric values and bounded object/event counts. Stages are data: no Python, shell commands, `eval`, dynamic imports or arbitrary scripts. Zip packs reject path traversal, absolute paths, symlinks, decompression bombs and oversized assets; use staged extraction and atomic install. Keep packs under the game's user-data directory. Report invalid content without crashing the game or altering built-in stages.

Delivery sequence:

1. **Local import/export:** stage browser, author credits, thumbnails, validation report and a user-stage directory. Ship a documented example pack and migration tool.
2. **Editor:** tile/entity palette, spawn/goal/lever placement, rotation preview, built-in trigger editor, undo/redo, autosave, playtest and package export. Do not overwrite bundled stages; create editable copies.
3. **Submissions:** repository pull requests using a template and automated validation/render checks. Require creator attribution, explicit content license and a completion replay or documented playtest. Automated structural validation does not prove a stage is fun or solvable.
4. **Curated catalog:** maintainer-reviewed metadata with immutable version/hash, compatibility info and opt-in downloads. Provide reporting/removal and creator-update workflows. Consider signed releases/catalogs before an in-game downloader. Accounts, voting, moderation service and global leaderboards are separate later scope.

Default recommendation for new submissions: CC BY 4.0 for independently created levels/art, GPL-2.0-compatible contributions for engine code. Preserve the original assets' CC BY 3.0 and font terms; new submission terms cannot relicense them. Track license/provenance per pack and any bundled dependencies.

## Project organization and preservation

Before refactoring, capture the current working diff and asset hashes and create a recoverable baseline. Keep existing user edits and legacy saves intact. Refactor into small responsibilities: app/state flow, display, simulation/physics, input, assets/themes, stage loading/validation, UI, audio, saves and diagnostics. A general-purpose plugin system or ECS is unnecessary at this scale.

Use one engine with explicit rules profiles and a legacy content adapter, avoiding two permanently diverging games. Keep a reference harness for compatibility comparisons. Migrate `~/.wwisup` saves once into XDG config/data/state locations with a backup; never overwrite the original records or silently reinterpret their frame units.

Package with a `pyproject.toml`, declared supported Python/Pygame versions, a launch command and `.desktop` file. Prepare an Arch `PKGBUILD`, clean-install checks and uninstall behavior. Keep runtime assets out of writable package directories. Local development and play should need neither root nor network access. System-wide installation/publication remains a separate concrete delivery step.

Maintain full GPL text, original notices, separate asset/font licenses, contributor records and a credits view. Document changed files/dates and provide corresponding source with distributed builds. Creating a DHH sprite is part of the plan; public packaging should check the specific artwork/reference permissions and applicable likeness/branding considerations. The game's GPL does not grant rights to third-party photos, logos or endorsement. Use newly created art with recorded provenance and no borrowed unlicensed portraits. Keep this review scoped to the public release; it does not block engineering or private concept work.

## Ordered milestones and completion gates

| Milestone | Deliverable | Done when |
| --- | --- | --- |
| **M0 — Recover and preserve** | Baseline snapshot, source/license inventory, display diagnosis, safe window recovery and native launcher | Original stages load; repeated launch/exit/fullscreen/focus tests work on the actual Omarchy session; saves are protected; remaining failures have reproducible logs. |
| **M1 — Modern runtime** | Separated update/render clocks, scalable viewport, input layer, audio fallback and Classic profile | Replay/trajectory fixtures cover jump, landing, damage, rotation and timing; 60/120/144/240 rendering does not change Classic outcomes; controller and high-DPI tests pass. |
| **M2 — Theme slice** | Manifest/asset pipeline, Original option, Follow Omarchy, one Refresh concept room and Omarchy/DHH concept | Same room plays identically across skins; theme switching cannot corrupt saves or collision state; Osaka Jade and a light palette remain readable; present a small creative review. |
| **M3 — Modern play and Cyberpunk** | Modern rules/tempo, collision improvements, measured optimizations, neon laser-bolt theme | Faster modes remain collision-safe and separately scored; stable benchmark targets are met; reduced-effects options work; no refresh-rate dependency. |
| **M4 — Complete homage release** | Full asset coverage for five themes, all original campaigns, settings, credits, migration and Arch package | All 15 campaign stages are completed/validated under intended rules; Original gets visual comparisons; clean install/update/uninstall and save migration work; packaging includes licenses. |
| **M5 — Local creation tools** | Versioned stage packs, importer/exporter, stage browser and editor | A new stage can be authored, exported, imported on a clean install and completed without editing source; bad packs fail safely. |
| **M6 — Community release workflow** | Submission template, automated checks, contribution guide and curated catalog format | A sample contributor submission passes validation, review, attribution and versioned release; distribution/publication is explicitly authorized. |

M0 → M1 → M2 → M3 → M4 is the first public-game path. Specify the stage schema during M1, but deliver the editor/catalog after core stability. Do not postpone credits or Original compatibility until release week. If profile data disproves the Pygame choice, evaluate an alternative engine with one imported stage and a measured comparison before committing to a migration.

## Verification and working agreement

Automate the checks that protect real behavior: legacy import, all stages loading, rotation invariants, collision edges/tunneling, timer independence from display rate, input consumption, theme fallback/cache isolation, save migration, malformed packs and path containment. Add screenshot comparisons for Original and themed preview rooms. Test menus as well as gameplay: paused changes, repeated fullscreen toggles, monitor changes, suspend/resume, missing audio, disconnected controller and theme changes while paused/running.

Headless tests are necessary but do not replace real Hyprland tests. Record which device/backend combinations were actually exercised. Final campaign acceptance needs successful playthroughs or trustworthy completion replays, not just loading the maps.

Routine implementation decisions, refactoring, local checks and fixes can proceed autonomously when implementation starts. This request is for the plan: it does not start a full rewrite, install packages, publish a repository or contact contributors. The expected user involvement is one bundled creative checkpoint after playable visual concepts exist, plus any genuinely necessary external publication/identity/permission decisions. Choose reasonable defaults and continue independent work instead of asking about every detail. No release date is promised before the runtime and art slices establish the effort.

## Technical references

- [Pygame display API](https://www.pygame.org/docs/ref/display.html): scaling, resizable windows, desktop sizing and display management. Its `SCALED` API is experimental; validate it against an explicit canvas/scaling implementation before choosing the display path.
- [Pygame time API](https://www.pygame.org/docs/ref/time.html): elapsed-time measurement and rate limiting; `Clock.tick` limits the loop, it does not itself decouple physics.
- [Debian source repository](https://salsa.debian.org/games-team/whichwayisup) and local `debian/copyright`, `README.txt`, `lib/`, `data/levels/` for provenance and current behavior.
- Installed `/usr/share/omarchy/bin/omarchy-theme-current` and `omarchy-theme-set` establish the actual theme-state paths and replacement behavior on this machine.
- [GNU GPL guidance](https://www.gnu.org/licenses/old-licenses/gpl-2.0-faq.en.html) and [CC BY 3.0](https://creativecommons.org/licenses/by/3.0/) for the distribution plan. Review actual included notices and new assets before packaging.
