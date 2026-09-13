"""Data-only palettes and responsive Omarchy integration."""
from dataclasses import dataclass
from pathlib import Path
import os
import re
import tomllib
from .storage import user_path

ROOT=Path(__file__).resolve().parents[1]
ROLES=('background','panel','foreground','muted','accent','secondary','hazard')

def color(value):
    if not isinstance(value,str) or not re.fullmatch(r'#[0-9a-fA-F]{6}',value):
        raise ValueError('Colors must be six-digit hex values, e.g. #46f4ea')
    return tuple(int(value[i:i+2],16) for i in (1,3,5))

def luminance(rgb):
    c=[v/255 for v in rgb]
    c=[v/12.92 if v<=.04045 else ((v+.055)/1.055)**2.4 for v in c]
    return sum(v*w for v,w in zip(c,(.2126,.7152,.0722)))

def contrast(a,b):
    l,h=sorted((luminance(a),luminance(b)))
    return (h+.05)/(l+.05)

@dataclass
class Theme:
    id:str
    name:str
    subtitle:str
    style:str
    character:str
    palette:dict
    source:str=''
    def __getitem__(self,key):return self.palette[key]
    def readable(self,bg,preferred='foreground'):
        candidate=self[preferred]
        if contrast(candidate,bg)>=4.5:return candidate
        return max(((248,248,240),(10,13,18)),key=lambda c:contrast(c,bg))

class Themes:
    def __init__(self):
        self.packs={}
        self.errors=[]
        for folder in (ROOT/'themes',user_path('data')/'themes'):
            if not folder.exists():continue
            for path in sorted(folder.glob('*.toml')):
                try:
                    pack=self.read(path)
                    # A user pack cannot silently replace a built-in theme.
                    if pack.id not in self.packs:self.packs[pack.id]=pack
                except (OSError,ValueError,KeyError,TypeError) as e:self.errors.append(f'{path.name}: {e}')
        self.system_signature=None
        self.system_palette={}
        self.system_name='Saved palette'
    def read(self,path):
        if path.stat().st_size>32768:raise ValueError('Theme manifest is too large')
        d=tomllib.loads(path.read_text())
        if d.get('schema')!=1:raise ValueError('Unsupported theme schema')
        if not re.fullmatch(r'[a-z][a-z0-9-]{0,39}',d['id']):raise ValueError('Invalid theme id')
        if d['style'] not in ('original','refresh','omarchy','cyberpunk'):raise ValueError('Unknown art style')
        if d['character'] not in ('original','guy','dhh'):raise ValueError('Unknown character')
        return Theme(d['id'],str(d['name'])[:60],str(d.get('subtitle',''))[:100],d['style'],d['character'],{k:color(d['palette'][k]) for k in ROLES},str(path))
    def poll_system(self):
        state=Path(os.environ.get('XDG_STATE_HOME',str(Path.home()/'.local/state')))
        config=Path(os.environ.get('XDG_CONFIG_HOME',str(Path.home()/'.config')))
        for base in (state/'omarchy/current',config/'omarchy/current'):
            path=base/'theme/colors.toml'
            try:
                payload=path.read_bytes()
                if len(payload)>32768:continue
                if payload==self.system_signature:return False
                d=tomllib.loads(payload.decode())
                mapped=dict(background=d['background'],panel=d.get('lighter_background',d['background']),
                            foreground=d.get('light_foreground',d['foreground']),muted=d.get('dark_foreground',d['foreground']),
                            accent=d['accent'],secondary=d.get('cyan',d['accent']),hazard=d.get('red','#ff667c'))
                parsed={k:color(v) for k,v in mapped.items()}
                namepath=base/'theme.name'
                name=namepath.read_text().strip() if namepath.exists() else path.parent.resolve().name
            except (OSError,ValueError,KeyError):continue
            self.system_palette=parsed
            self.system_signature=payload
            self.system_name=name
            return True
        return False
    def get(self,settings):
        source=self.packs.get(settings['theme'],self.packs['refresh'])
        palette=source.palette.copy()
        subtitle=source.subtitle
        if source.id=='system':
            palette.update(self.system_palette)
            subtitle=self.system_name.replace('-',' ').title()
        if settings.get('accent'):
            try:palette['accent']=color(settings['accent'])
            except ValueError:pass
        return Theme(source.id,source.name,subtitle,source.style,source.character,palette,source.source)
    def export(self,theme):
        folder=user_path('data')/'themes'
        folder.mkdir(exist_ok=True)
        path=folder/'my-design.toml'
        # Export is explicit and numbered, never overwrite a user's pack.
        index=1
        while path.exists():
            index+=1;path=folder/f'my-design-{index}.toml'
        ident=path.stem
        lines=['schema = 1',f'id = "{ident}"',f'name = "My design {index}"',
               'subtitle = "Your custom palette"',f'style = "{theme.style}"',f'character = "{theme.character}"',
               'author = "Your name"','license = "Choose a license before sharing"','[palette]']
        lines += [f'{k} = "#{v[0]:02x}{v[1]:02x}{v[2]:02x}"' for k,v in theme.palette.items()]
        path.write_text('\n'.join(lines)+'\n')
        self.packs[ident]=self.read(path)
        return path
