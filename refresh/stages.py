"""Bounded, data-only stage files with legacy import and export."""
from pathlib import Path
from dataclasses import dataclass
import hashlib
import json
import math
import re
from .storage import user_path, atomic_json

ROOT=Path(__file__).resolve().parents[1]
WORLD_NAMES=('Quest For The Keys','The Other Side','A Piece of Cake')
TYPES=('player','key','lever','spider','blob','other_pants','power_crystal','cake')
TRIGGERS=('level_begin','flipped','key','other_pants','power_crystal','cake')
MAX_BYTES=128*1024

class StageError(ValueError):pass

def text(value,label,limit=100):
    if not isinstance(value,str) or not value.strip() or len(value)>limit or any(ord(c)<32 for c in value):
        raise StageError(f'Invalid {label}')
    return value

def validate(d):
    if not isinstance(d,dict) or d.get('schema')!=1:raise StageError('Stage schema must be 1')
    if not re.fullmatch(r'[a-zA-Z0-9_-]{1,60}',text(d.get('id'),'id',60)):raise StageError('Invalid stage id')
    for key in ('title','author','license'):text(d.get(key),key)
    if d.get('tileset') not in ('brown','green','grey'):raise StageError('Unknown legacy tileset')
    tiles=d.get('tiles')
    if not isinstance(tiles,list) or len(tiles)!=20 or any(not isinstance(r,str) or len(r)!=20 or set(r)-set('WSB .') for r in tiles):
        raise StageError('Tiles must be exactly 20 rows of 20 characters (W, S, B or space)')
    entities=d.get('entities')
    if not isinstance(entities,list) or not 1<=len(entities)<=128:raise StageError('Expected 1–128 entities')
    players=0
    for e in entities:
        if not isinstance(e,dict) or e.get('type') not in TYPES:raise StageError('Unknown entity type')
        players+=e['type']=='player'
        for key in ('x','y'):
            n=e.get(key)
            if type(n) not in (float,int) or not math.isfinite(n) or not 0<=n<20:raise StageError('Entity coordinates must be finite and inside the board')
        if e['type']=='spider' and e.get('attached') not in ('LEFT','RIGHT','UP','DOWN'):raise StageError('Spider needs an attachment direction')
        if e['type']=='lever' and (type(e.get('uses')) is not int or not -1<=e['uses']<=100 or e['uses']==0):raise StageError('Lever uses must be -1 or 1–100')
    if players!=1:raise StageError('Exactly one player spawn is required')
    events=d.get('events')
    if not isinstance(events,list) or len(events)>64:raise StageError('Expected at most 64 events')
    for event in events:
        if not isinstance(event,dict) or event.get('trigger') not in TRIGGERS:raise StageError('Unknown trigger')
        if type(event.get('times')) is not int or not -1<=event['times']<=100:raise StageError('Invalid trigger repeat count')
        actions=event.get('actions')
        if not isinstance(actions,list) or len(actions)>100:raise StageError('Too many trigger actions')
        for action in actions:
            text(action,'action',500)
            if action in ('change_level','wait'):continue
            if action.startswith('dialogue '):continue
            if action.startswith('player orientation ') and action.split()[-1] in ('LEFT','RIGHT','UP','DOWN') and len(action.split())==3:continue
            if action.startswith('player animation ') and action.split()[-1] in ('sleep','default','standing','walking','shouting','jumping','exit','gone') and len(action.split())==3:continue
            raise StageError('Unsupported event action: '+action[:60])
    return d

def parse_legacy(path, title=None):
    path=Path(path)
    if path.stat().st_size>MAX_BYTES:raise StageError('Stage exceeds 128 KiB')
    lines=path.read_text().splitlines()
    d=dict(schema=1,id=path.stem,title=title or path.stem,author='Olli Hectigo Etuaho',license='CC-BY-3.0',tileset='brown',tiles=[],entities=[],events=[])
    i=0;current=None
    while i<len(lines):
        line=lines[i].strip();i+=1
        if not line:continue
        parts=line.split()
        if line=='tiles':
            d['tiles']=lines[i:i+20];i+=20;continue
        if parts[0]=='set':d['tileset']=parts[1];continue
        if parts[0]=='trigger':
            current=dict(trigger=parts[1],times=int(parts[2]),actions=[])
            d['events'].append(current);continue
        if line=='end trigger':current=None;continue
        if current is not None:current['actions'].append(line);continue
        if parts[0] not in TYPES:raise StageError('Unknown entity: '+parts[0])
        e=dict(type=parts[0],x=float(parts[1]),y=float(parts[2]))
        if e['type']=='spider':e['attached']=parts[3]
        if e['type']=='lever':e['uses']=int(parts[3])
        d['entities'].append(e)
    return validate(d)

def legacy(d):
    validate(d)
    lines=['set '+d['tileset'],'','tiles',*d['tiles'],'']
    for e in sorted(d['entities'],key=lambda e:e['type']!='player'):
        line=f"{e['type']} {e['x']} {e['y']}"
        if e['type']=='spider':line+=' '+e['attached']
        if e['type']=='lever':line+=f" {e['uses']} TRIGGER_FLIP"
        lines.append(line)
    for event in d['events']:
        lines+=['',f"trigger {event['trigger']} {event['times']}",*event['actions'],'end trigger']
    return '\n'.join(lines)+'\n'

def read(path):
    path=Path(path)
    if path.stat().st_size>MAX_BYTES:raise StageError('Stage exceeds 128 KiB')
    if path.suffix=='.txt':return parse_legacy(path)
    try:return validate(json.loads(path.read_text()))
    except (KeyError,TypeError,json.JSONDecodeError) as e:raise StageError(str(e)) from e

def fingerprint(d):return hashlib.sha256(json.dumps(d,sort_keys=True).encode()).hexdigest()

def materialize(d):
    folder=user_path('state')/'stages'
    folder.mkdir(exist_ok=True)
    path=folder/(fingerprint(d)+'.txt')
    if not path.exists():path.write_text(legacy(d))
    return str(path.with_suffix(''))

def import_stage(path):
    d=read(path)
    folder=user_path('data')/'stages';folder.mkdir(exist_ok=True)
    target=folder/(d['id']+'-'+fingerprint(d)[:10]+'.json')
    atomic_json(target,d)
    return target

def blank():
    rows=[' '*20 for _ in range(20)]
    rows[19]='W'*20
    return dict(schema=1,id='my-stage',title='My first stage',author='Your name',license='CC-BY-4.0',tileset='brown',tiles=rows,
                entities=[dict(type='player',x=9.5,y=18.5),dict(type='key',x=17.5,y=18.5),dict(type='lever',x=14.5,y=18.5,uses=-1)],
                events=[dict(trigger='key',times=1,actions=['dialogue Stage complete!','change_level'])])

@dataclass
class Stage:
    id:str
    title:str
    world:str
    path:Path
    document:dict
    original:bool=True
    @property
    def engine_path(self):return str(self.path.with_suffix('')) if self.original else materialize(self.document)

class Catalog:
    def __init__(self):self.refresh()
    def refresh(self):
        self.stages=[];self.errors=[]
        for world in WORLD_NAMES:
            listing=ROOT/'data/levels'/f'{world}.txt'
            for i,line in enumerate(listing.read_text().splitlines()):
                name=line.split()[1];path=listing.parent/(name+'.txt')
                self.stages.append(Stage(name,f'{i+1:02d} / '+world,world,path,parse_legacy(path)))
        folder=user_path('data')/'stages';folder.mkdir(exist_ok=True)
        for path in sorted(folder.glob('*.json')):
            try:
                d=read(path)
                self.stages.append(Stage(d['id']+'-'+fingerprint(d)[:10],d['title'],'Your stages',path,d,False))
            except (ValueError,OSError,IndexError) as e:self.errors.append(f'{path.name}: {e}')
