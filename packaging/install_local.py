"""Register the current checkout as a per-user application; no root required."""
from pathlib import Path
import shlex
import shutil
import sys
root=Path(__file__).resolve().parents[1]
launcher=Path.home()/'.local/bin/whichwayisup-refresh'
launcher.parent.mkdir(parents=True,exist_ok=True)
launcher.write_text('#!/bin/sh\nexec '+shlex.quote(sys.executable)+' '+shlex.quote(str(root/'run_game.py'))+' "$@"\n')
launcher.chmod(0o755)
icons=Path.home()/'.local/share/icons/hicolor/scalable/apps'
icons.mkdir(parents=True,exist_ok=True)
shutil.copy2(root/'packaging/icon.svg',icons/'whichwayisup-refresh.svg')
apps=Path.home()/'.local/share/applications';apps.mkdir(parents=True,exist_ok=True)
# Desktop Entry Exec quoting differs from shell quoting. Paths here are absolute.
escaped=str(launcher).replace('\\','\\\\').replace('"','\\"').replace('`','\\`').replace('$','\\$')
text=(root/'packaging/whichwayisup-refresh.desktop').read_text().replace('Exec=whichwayisup-refresh','Exec="'+escaped+'"')
(apps/'whichwayisup-refresh.desktop').write_text(text)
print(launcher)
print(apps/'whichwayisup-refresh.desktop')
