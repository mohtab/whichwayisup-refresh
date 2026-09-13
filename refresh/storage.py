"""Versioned user settings, separate from the original game's save files."""
from pathlib import Path
import json
import math
import os
import shutil
import tempfile

DEFAULTS = dict(theme='refresh', character='theme', tempo=1.0, fps=60, effects=True,
                sound=True, music=False, music_volume=50, sfx_volume=75, profile='story', dialogue=True, smooth=False, accent='', fullscreen=False,
                window=[1100, 760], stage='w0-l0', key_left='left', key_right='right',
                key_jump='z', key_interact='down')

def user_path(kind):
    override = os.environ.get('WWISUP_USER_DIR')
    if override:
        base = Path(override) / kind
    else:
        folders = {'config': ('XDG_CONFIG_HOME', '.config'), 'data': ('XDG_DATA_HOME', '.local/share'),
                   'state': ('XDG_STATE_HOME', '.local/state')}
        env, fallback = folders[kind]
        base = Path(os.environ.get(env, str(Path.home()/fallback))) / 'whichwayisup-refresh'
    base.mkdir(parents=True, exist_ok=True)
    return base

def atomic_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile('w', dir=path.parent, delete=False, encoding='utf8') as f:
        temporary = Path(f.name)
        try:
            json.dump(value, f, indent=2, ensure_ascii=False, allow_nan=False)
            f.write('\n')
            f.flush()
            os.fsync(f.fileno())
        except BaseException:
            temporary.unlink(missing_ok=True)
            raise
    try:
        temporary.replace(path)
    finally:
        temporary.unlink(missing_ok=True)

class Store:
    def __init__(self):
        self.path = user_path('config')/'settings.json'
        self.settings = DEFAULTS.copy()
        self.records_path = user_path('data')/'records.json'
        self.records = {}
        for path, dest in ((self.path, self.settings), (self.records_path, self.records)):
            if path.exists():
                try:
                    content = json.loads(path.read_text())
                    if not isinstance(content, dict): raise ValueError('Expected object')
                    dest.update(content)
                except (ValueError, OSError):
                    shutil.copy2(path, path.with_suffix('.invalid-backup'))
        self.validate()
        invalid=[]
        for key,row in self.records.items():
            if key=='legacy_import':continue
            if not isinstance(row,dict):invalid.append(key);continue
            seconds=row.get('best_seconds')
            if type(seconds) not in (int,float) or not math.isfinite(seconds) or not 0<=seconds<10**9:
                invalid.append(key);continue
            if not isinstance(row.get('stage'),str) or not isinstance(row.get('category',''),str):invalid.append(key)
        if invalid:
            if self.records_path.exists():shutil.copy2(self.records_path,self.records_path.with_suffix('.invalid-backup'))
            for key in invalid:del self.records[key]
        self.migrate()
    def validate(self):
        s = self.settings
        for key in ('theme','character','accent','stage','key_left','key_right','key_jump','key_interact'):
            if not isinstance(s.get(key),str): s[key]=DEFAULTS[key]
        for key in ('sound','music','dialogue','effects','smooth','fullscreen'):
            if not isinstance(s.get(key),bool): s[key]=DEFAULTS[key]
        if s.get('profile') not in ('story','speedrun'):s['profile']='story'
        for key in ('music_volume','sfx_volume'):
            if type(s.get(key)) is not int or s[key] not in (0,25,50,75,100):s[key]=DEFAULTS[key]
        if s.get('tempo') not in (.75,1.,1.25,1.5): s['tempo']=1.
        if s.get('fps') not in (30,60,120,144,240): s['fps']=60
        if s['character'] not in ('theme','original','guy','dhh'): s['character']='theme'
        if not (isinstance(s.get('window'), list) and len(s['window'])==2 and all(type(x)==int and 320<=x<=7680 for x in s['window'])):
            s['window']=[1100,760]
    def migrate(self):
        original=Path.home()/'.wwisup/config.txt'
        dest=user_path('data')/'legacy-config.txt'
        if os.environ.get('WWISUP_USER_DIR') or dest.exists() or not original.exists(): return
        shutil.copy2(original,dest)
        self.records['legacy_import']={'source':str(original),'units':'24 Hz gameplay frames','values':original.read_text().splitlines()}
        self.save_records()
    def save(self):
        atomic_json(self.path,self.settings)
    def save_records(self):
        atomic_json(self.records_path,self.records)
