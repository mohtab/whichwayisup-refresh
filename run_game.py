#!/usr/bin/env python3
"""Which Way Is Up? refresh launcher. --legacy opens the preserved original UI."""
from pathlib import Path
import sys
import os

# Prefer the native backend on Wayland sessions, while respecting explicit overrides.
if os.environ.get("WAYLAND_DISPLAY") and "SDL_VIDEODRIVER" not in os.environ:
    os.environ["SDL_VIDEODRIVER"] = "wayland"
    os.environ["WWISUP_AUTO_WAYLAND"] = "1"

if __name__ == '__main__':
    if '--legacy' in sys.argv:
        sys.argv.remove('--legacy')
        sys.path.insert(0,str(Path(__file__).resolve().parent/'lib'))
        import main
        main.main()
    else:
        from refresh.app import main
        main()
