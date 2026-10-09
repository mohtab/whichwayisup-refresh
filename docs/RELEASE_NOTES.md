# Which Way Is Up? — 0.4.0rc5 October polish preview

Turn the world and find your way through 15 puzzle-platforming stages. This preview
adds constructed stone platforms, chamber lighting, redesigned menus and clearer
switch supports. It fixes transparent stone interiors on Wayland. Original keeps
its legacy gameplay; other themes use connected rotating terrain and swept missile
contacts, with separate records and replay profiles.

## Download

Open **Assets** below and choose one file:

| System | File |
| --- | --- |
| Arch Linux / Omarchy | `whichwayisup-refresh-0.4.0rc5-1-any.pkg.tar.zst` |
| Other Linux distributions | `whichwayisup-refresh-0.4.0rc5.tar.gz` |

**Arch / Omarchy:** open a terminal in your download folder, then run:

```sh
sudo pacman -U ./whichwayisup-refresh-0.4.0rc5-1-any.pkg.tar.zst
```

Launch **Which Way Is Up? — Refresh** from your application menu.

**Other Linux:** extract the `.tar.gz` download and follow the
[install guide](https://github.com/mohtab/whichwayisup-refresh/blob/v0.4.0rc5/docs/INSTALL.md).
You need Python 3.11 or newer and Pygame 2.6. Choose the named game archive above;
the automatically generated “Source code” links are primarily for contributors.

Windows and macOS installers are not available in this preview.
`SHA256SUMS` is provided for optional download verification.

## Start playing

Move with **← / →** or **A / D**. Jump with **Space**, **Z**, or **↑**; hold it to
fall more slowly. Use **↓**, **S**, or **E** to interact. **Esc** pauses and **F1**
shows the controls. Choose **Customize** to change themes, sound, and display.

[Player guide](https://github.com/mohtab/whichwayisup-refresh/blob/v0.4.0rc5/docs/PLAYER_GUIDE.md)
· [What’s new](https://github.com/mohtab/whichwayisup-refresh/blob/v0.4.0rc5/CHANGELOG.md)
· [Report a bug](https://github.com/mohtab/whichwayisup-refresh/issues/new?template=bug_report.yml)

## Upgrading and feedback

Existing refresh settings, stages, and local records stay in your user folders.
Arch users can install the new package with the same command above. Source users
should extract into a new folder and follow the upgrade steps in the install guide.

This is a preview release. Please share problems with controllers, audio,
suspend/resume, or multiple monitors, including your system and game version.

Original game by **Olli “Hectigo” Etuaho**. Refresh by **Mohtab Arabiat**, with
**AI coding assistance from Codex (OpenAI)**. See the included `CREDITS.md` for
artwork, music, licenses, and the unofficial Omarchy/DHH tribute attribution.

## Checks for this preview

Automated checks passed on Python 3.11 and 3.13, including 111 tests, all 15 campaign
completion replays, and both sprite-contrast modes. The Arch package was installed
and launched in a clean container. The attached game files come from GitHub Actions.
Native Wayland checks also cover five themes, four layouts and stone opacity
through rotation using both renderer paths. Final combined visual approval remains
open; this preview gathers further player and hardware feedback.
