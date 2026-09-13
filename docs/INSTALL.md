# Install Which Way Is Up? — Refresh

This release is for Linux desktops. **0.4.0rc4 is a release candidate**: a preview
for testing before the stable release. Windows and macOS installers are not provided.

Open the [release downloads](https://github.com/mohtab/whichwayisup-refresh/releases)
and expand **Assets** under 0.4.0rc4. Choose one of these files:

| Your system | Download | What it contains |
| --- | --- | --- |
| Arch Linux / Omarchy | `whichwayisup-refresh-0.4.0rc4-1-any.pkg.tar.zst` | The game and an application-menu entry; Pacman installs the dependencies. |
| Other Linux desktops, or a local install without root | `whichwayisup-refresh-0.4.0rc4.tar.gz` | The complete game; you provide Python and install Pygame below. |

Choose the named game archive above, rather than GitHub's automatically generated
**Source code (zip)** or **Source code (tar.gz)** links. The instructions below assume
your browser saved the download in `~/Downloads`.

## Arch Linux and Omarchy

Open a terminal and run:

```sh
sudo pacman -U ~/Downloads/whichwayisup-refresh-0.4.0rc4-1-any.pkg.tar.zst
```

Open **Which Way Is Up? — Refresh** from your application menu, or run:

```sh
whichwayisup-refresh
```

## Other Linux desktops: run from the archive

You need **Python 3.11 or newer**, its `venv` module, and an internet connection to
install **Pygame 2.6 or newer, below 3**. Check Python with `python3 --version`.
If Python or `venv` is missing, install it using your distribution's package manager.
The native desktop checks for this release were run on Arch/Omarchy with Wayland;
other Linux distributions may need additional setup.

Extract the game into a folder you will keep:

```sh
mkdir -p ~/Games
tar -xzf ~/Downloads/whichwayisup-refresh-0.4.0rc4.tar.gz -C ~/Games
cd ~/Games/whichwayisup-refresh-0.4.0rc4
python3 -m venv .venv
.venv/bin/python -m pip install 'pygame>=2.6,<3'
.venv/bin/python run_game.py
```

To add the game to your application menu, run this from the same folder:

```sh
.venv/bin/python packaging/install_local.py
```

Then open **Which Way Is Up? — Refresh** from the application menu. This registers
the existing folder and virtual environment; it does not copy them elsewhere.
Keep both in place. No administrator password is needed for this local registration.

## Updating

Close the game first. For the Arch package, download the new package and install it
with `sudo pacman -U` as above.

For the archive, extract the new version into its own folder and repeat the virtual
environment and launcher-registration steps. Your progress and settings are stored
separately from the game folder, so the new version uses them automatically.
Keep the previous folder until you have checked the new version.

## If the game does not open

- **“No module named pygame”:** launch with `.venv/bin/python run_game.py` from the
  extracted game folder. Install Pygame with that same `.venv/bin/python` as above.
- **The application-menu entry stopped working:** if you moved the game folder,
  repeat `packaging/install_local.py` using the new folder's virtual environment.
- **The window is difficult to recover:** run `whichwayisup-refresh --safe-window`
  for the Arch package, or `.venv/bin/python run_game.py --safe-window` from the
  extracted folder. New launches start windowed; F11 toggles fullscreen.
- **A different error:** start the game from a terminal to see the message. Include
  your Linux distribution, desktop, game version and relevant error text in a
  [bug report](https://github.com/mohtab/whichwayisup-refresh/issues).

See the [player guide](PLAYER_GUIDE.md) for controls, display options and save locations.
