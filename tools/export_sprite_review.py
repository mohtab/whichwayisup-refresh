"""Export the current renderer and original artwork for visual review, without modifying the game."""
import os
os.environ['SDL_VIDEODRIVER']='dummy'
os.environ['SDL_AUDIODRIVER']='dummy'
os.environ['PYGAME_HIDE_SUPPORT_PROMPT']='1'
import sys
import json
import shutil
import tempfile
import hashlib
import datetime
import math
import html
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
import pygame
pygame.display.init();pygame.font.init();pygame.display.set_mode((1,1))
from refresh.art import Painter
from refresh.storage import DEFAULTS
from refresh.themes import Themes
from refresh.runtime import ROOT as GAME_ROOT
from level import Level
from variables import Variables
Variables.vdict.update(devmode=False,sound=False,dialogue=False,verbose=False)

stamp=datetime.datetime.now().strftime('%Y%m%d-%H%M%S')
out=ROOT/'sprite-review'/stamp
out.mkdir(parents=True)
shutil.copytree(ROOT/'data/pictures',out/'original/source')
shutil.copytree(ROOT/'themes',out/'drawing-source/themes')
shutil.copy2(ROOT/'refresh/art.py',out/'drawing-source/art.py')
shutil.copy2(ROOT/'refresh/themes.py',out/'drawing-source/themes.py')
shutil.copy2(ROOT/'CREDITS.md',out/'CREDITS.md')
shutil.copy2(ROOT/'LICENSE',out/'GPL-2.0.txt')
shutil.copy2(ROOT/'licenses/original-copyright',out/'original-copyright.txt')
font_path=str(ROOT/'data/misc/Vera.ttf')
fonts={n:pygame.font.Font(font_path,n) for n in (12,14,16,20,28)}
entries=[];by_group={};sequences=[]

def save(surface,path):
    path.parent.mkdir(parents=True,exist_ok=True)
    # Bake blanket alpha (used by the current exit animation) into PNG pixels.
    baked=pygame.Surface(surface.get_size(),pygame.SRCALPHA)
    baked.blit(surface,(0,0))
    pygame.image.save(baked,path)
    return baked

def add(surface,path,group,label,**meta):
    baked=save(surface,out/path)
    digest=hashlib.sha256(pygame.image.tobytes(baked,'RGBA')).hexdigest()
    e=dict(path=str(path),group=group,label=label,width=baked.get_width(),height=baked.get_height(),pixel_hash=digest,**meta)
    entries.append(e);by_group.setdefault(group,[]).append(e)
    return e

for path in sorted((ROOT/'data/pictures').glob('*.png')):
    im=pygame.image.load(path).convert_alpha()
    im.set_colorkey((255,0,255))
    category='background-ui' if ('background' in path.name or path.name.startswith(('bg_','menu_','health_','key_p','key_z'))) else 'sprites'
    add(im,Path('original/transparent')/path.name,'Original',path.stem,category=category,source=str(Path('original/source')/path.name))

# Read dimensions and animation states from actual game entities in all campaign maps.
specs={}
for world in ('Quest For The Keys','The Other Side','A Piece of Cake'):
    for line in (ROOT/'data/levels'/f'{world}.txt').read_text().splitlines():
        level=Level(pygame.Surface((520,520)),line.split()[1])
        for obj in (*level.tiles,*level.objects,level.player):
            kind=getattr(obj,'tileclass',obj.itemclass)
            for state,animation in obj.animations.items():
                spec=(kind,obj.rect.width,obj.rect.height,state)
                specs[spec]=[f.frame_length for f in animation.frames]

# Projectiles are spawned during play rather than stored in stage entity lists.
from projectile import Projectile
projectile=Projectile(pygame.Surface((520,520)),100,100,5,0)
for state,animation in projectile.animations.items():
    specs[('projectile',projectile.rect.width,projectile.rect.height,state)]=[f.frame_length for f in animation.frames]

with tempfile.TemporaryDirectory(prefix='wwisup-export-') as temp:
    # Themes can read the real Omarchy palette but do not create/change game settings.
    os.environ['WWISUP_USER_DIR']=temp
    themes=Themes();themes.poll_system()
    system_name=themes.system_name
    for ident in ('refresh','omarchy','system','cyberpunk','original'):
        settings=dict(DEFAULTS,theme=ident)
        theme=themes.get(settings);painter=Painter();painter.configure(theme,settings)
        group=theme.name if ident!='original' else 'Original palette / character overrides'
        folder=Path('rendered')/ident
        (out/folder).mkdir(parents=True,exist_ok=True)
        (out/folder/'palette.json').write_text(json.dumps({k:'#%02x%02x%02x'%v for k,v in theme.palette.items()},indent=2)+'\n')
        if ident!='original':add(painter.background,folder/'background.png',group,'background',category='background-ui')
        for (kind,w,h,state),durations in sorted(specs.items()):
            if ident=='original' and kind!='player':continue
            characters=('guy','dhh') if kind=='player' else (None,)
            for character in characters:
                stem=f'{kind}_{character}_' if character else f'{kind}_'
                paths=[]
                for phase,duration in enumerate(durations):
                    image=painter.sprite(kind,w,h,state,phase,character)
                    path=folder/(stem+state+f'_{w}x{h}_f{phase:02d}.png')
                    e=add(image,path,group,path.stem,category='sprites',kind=kind,state=state,character=character,phase=phase,
                          legacy_frame_length=duration,duration_ms=round((duration+1)*1000/24))
                    paths.append(str(path))
                sequences.append(dict(theme=ident,kind=kind,character=character,state=state,size=[w,h],frames=paths,
                                      durations_ms=[round((x+1)*1000/24) for x in durations],
                                      note='Current procedural output; repeated poses are intentional exports of the existing implementation.'))

# Export current representative procedural effects in addition to actual sprite states.
# These are reference renders because trails/particles are drawn directly on the world.
for ident in ('refresh','omarchy','system','cyberpunk'):
    group=themes.packs[ident].name
    settings=dict(DEFAULTS,theme=ident);theme=themes.get(settings)
    for label in ('laser-trail-reference','particle-reference','offscreen-arrow-reference'):
        s=pygame.Surface((64,48),pygame.SRCALPHA)
        if label.startswith('laser'):
            from refresh.art import mix
            pygame.draw.line(s,mix(theme['background'],theme['accent'],.35),(44,24),(24,24),6)
            pygame.draw.line(s,theme['accent'],(44,24),(24,24),2)
        elif label.startswith('particle'):
            for x,r in ((12,4),(28,3),(42,2),(54,1)):pygame.draw.circle(s,theme['accent'],(x,24),r)
        else:pygame.draw.polygon(s,theme['accent'],[(32,3),(27,12),(37,12)])
        add(s,Path('rendered')/ident/(label+'.png'),group,label,category='effect-reference')

# Build a contact sheet for each group. Pixel art is enlarged with nearest-neighbor.
def text(surface,value,pos,size=14,color=(220,225,230)):
    surface.blit(fonts[size].render(value,True,color),pos)
def checker(surface,rect):
    colors=((36,40,49),(45,50,59))
    for y in range(rect.top,rect.bottom,12):
        for x in range(rect.left,rect.right,12):
            pygame.draw.rect(surface,colors[((x-rect.left)//12+(y-rect.top)//12)%2],pygame.Rect(x,y,12,12).clip(rect))
def thumb(surface,entry,rect):
    checker(surface,rect)
    im=pygame.image.load(out/entry['path'])
    scale=min(rect.w/im.get_width(),rect.h/im.get_height(),6)
    if scale>=1:scale=max(1,int(scale))
    size=(max(1,round(im.get_width()*scale)),max(1,round(im.get_height()*scale)))
    preview=pygame.transform.scale(im,size)
    surface.blit(preview,preview.get_rect(center=rect.center))

sheets=[]
for group,items in by_group.items():
    # Keep sheets at manageable sizes; the gallery contains all backgrounds at full size.
    sprites=[e for e in items if e['category']!='background-ui']
    for start in range(0,len(sprites),40):
        subset=sprites[start:start+40];rows=math.ceil(len(subset)/5)
        sheet=pygame.Surface((1400,90+rows*180));sheet.fill((19,24,32))
        text(sheet,group+' / sprite inventory',(24,18),28)
        text(sheet,'Native dimensions shown. Repeated animation frames are included. Checkerboard = transparency.',(24,55),14)
        for i,e in enumerate(subset):
            x=20+i%5*276;y=88+i//5*180
            thumb(sheet,e,pygame.Rect(x,y,252,122))
            label=e['label']
            text(sheet,label[:35],(x,y+128),12)
            if len(label)>35:text(sheet,label[35:70],(x,y+144),12)
            text(sheet,f"{e['width']} × {e['height']} px",(x,y+160),12,(146,166,181))
        slug=group.lower().replace(' ','-').replace('/','-')
        name=Path('contact-sheets')/(slug+f'-{start//40+1:02d}.png')
        save(sheet,out/name);sheets.append(str(name))

# A compact cross-theme overview for the first visual review.
columns=['Original','Refresh','Omarchy','Follow Omarchy','Cyberpunk']
rows=[('Guy','player','guy'),('DHH','player','dhh'),('Spider','spider',None),('Blob','blob',None),('Projectile','projectile',None),('Wall','wall',None),('Spikes','spikes',None),('Lever','lever',None),('Key','key',None)]
original_names={'Guy':'guy_standing_0','Spider':'spider_standing_0','Blob':'blob_standing_0','Projectile':'energy_flying_0','Wall':'brown_wall_0','Spikes':'brown_spikes_0','Lever':'brown_lever_0','Key':'brown_key_0'}
overview=pygame.Surface((1400,120+len(rows)*134));overview.fill((19,24,32))
text(overview,'WHICH WAY IS UP? / current sprite review',(24,18),28)
text(overview,'Exact renderer exports, not proposed redesigns. New themes use code-drawn art. System palette: '+system_name,(24,59),14)
for j,col in enumerate(columns):text(overview,col,(158+j*247,95),16)
for i,(label,kind,char) in enumerate(rows):
    y=126+i*134;text(overview,label,(20,y+44),16)
    for j,col in enumerate(columns):
        chosen=None
        if col=='Original':chosen=next((e for e in by_group[col] if e['label']==original_names.get(label)),None)
        else:chosen=next((e for e in by_group[col] if e.get('kind')==kind and e.get('character')==char and e.get('state')=='default' and e.get('phase')==0),None)
        rect=pygame.Rect(146+j*247,y,225,110)
        assert chosen is not None or (col=='Original' and label=='DHH'), (col,label)
        if chosen:thumb(overview,chosen,rect)
        else:text(overview,'Not in original',(rect.x+30,rect.y+44),14)
save(overview,out/'OVERVIEW.png')

# Offline gallery: zero dependencies, full-size download links, filtering and pixel zoom.
cards=[]
for e in entries:
    path=html.escape(e['path'],quote=True)
    details=f"{e['width']} × {e['height']} px"
    if 'phase' in e:details+=f" · frame {e['phase']} · {e['duration_ms']} ms"
    cards.append(f'<article data-group="{html.escape(e["group"],quote=True)}" data-label="{html.escape(e["label"].lower(),quote=True)}"><a class="preview" href="{path}" target="_blank"><img loading="lazy" src="{path}" alt="{html.escape(e["label"],quote=True)}" style="--w:{e["width"]};--h:{e["height"]}"></a><strong>{html.escape(e["label"])}</strong><span>{html.escape(e["group"])} · {details}</span><a href="{path}" download>Save PNG</a></article>')
options='<option value="">All themes</option>'+''.join(f'<option>{html.escape(g)}</option>' for g in by_group)
page='''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>Which Way Is Up? — Sprite review</title>
<style>*{box-sizing:border-box}body{margin:0;background:#111820;color:#e6edf2;font:16px system-ui,sans-serif}header{padding:32px;max-width:1200px}h1{margin:0 0 12px;font-size:32px}p{line-height:1.6;color:#adbdc9}a{color:#7cdbd1}nav{position:sticky;top:0;padding:14px 32px;background:#17232e;display:flex;flex-wrap:wrap;gap:14px;z-index:2}input,select{font:inherit;padding:9px;background:#223342;color:#fff;border:1px solid #4a606f;border-radius:6px}main{padding:24px;display:grid;grid-template-columns:repeat(auto-fill,minmax(260px,1fr));gap:16px}article{padding:14px;background:#1b2731;border:1px solid #324450;border-radius:10px;overflow:hidden}article[hidden]{display:none}.preview{height:210px;display:flex;align-items:center;justify-content:center;overflow:auto;background:repeating-conic-gradient(#303844 0% 25%,#252c36 0% 50%) 50%/20px 20px}img{image-rendering:pixelated;object-fit:contain;max-width:100%;max-height:100%;width:calc(var(--w)*var(--zoom,4)*1px);height:calc(var(--h)*var(--zoom,4)*1px)}strong,span{display:block;overflow-wrap:anywhere;margin:12px 0;font-size:13px}span{color:#9caebb}small{align-self:center;color:#adbdc9}</style>
<header><h1>Which Way Is Up? / Sprite review</h1><p>All original PNGs and all current code-drawn animation frames. Several new animations repeat a pose: these are exact exports of what exists, not completed animation sets. Click any image for the PNG at full size.</p><p><a href="OVERVIEW.png">Open comparison sheet</a> · <a href="README.md">Read asset notes</a> · <a href="manifest.json">Asset manifest</a> · <a href="animation-sequences.json">Animation sequences</a></p></header>
<nav><input id="search" aria-label="Search sprites" placeholder="Search: player, dhh, walking…"><select id="group" aria-label="Theme">OPTIONS</select><select id="zoom" aria-label="Preview scale"><option value="1">1× pixels</option><option value="2">2× pixels</option><option value="4" selected>4× pixels</option><option value="6">6× pixels</option></select><small id="count"></small></nav><main>CARDS</main>
<script>const cards=[...document.querySelectorAll('article')],search=document.querySelector('#search'),group=document.querySelector('#group'),zoom=document.querySelector('#zoom');function filter(){let n=0;for(const card of cards){card.hidden=!!((group.value&&card.dataset.group!==group.value)||!card.dataset.label.includes(search.value.toLowerCase()));if(!card.hidden)n++}document.querySelector('#count').textContent=n+' images'}search.oninput=group.onchange=filter;zoom.onchange=()=>document.documentElement.style.setProperty('--zoom',zoom.value);filter();</script></html>'''
(out/'index.html').write_text(page.replace('OPTIONS',options).replace('CARDS',''.join(cards)))
(out/'manifest.json').write_text(json.dumps(dict(system_palette=system_name,images=entries,contact_sheets=sheets),indent=2)+'\n')
(out/'animation-sequences.json').write_text(json.dumps(sequences,indent=2)+'\n')
raw_count=len(list((ROOT/'data/pictures').glob('*.png')))
readme=f'''# Sprite review pack

Start with **index.html** (offline, searchable gallery) or **OVERVIEW.png** (theme comparison).

- `original/source/`: exact copies of every original picture-directory file: {raw_count} PNGs plus animation-definition TXT files. Originals use magenta (#ff00ff) as a transparency key; it is not part of the intended character design.
- `original/transparent/`: PNG review exports with the same magenta color key rendered as alpha transparency. Original source files above remain byte-for-byte unchanged.
- `rendered/refresh`, `rendered/omarchy`, `rendered/system`, `rendered/cyberpunk`: every frame/state requested by the current procedural renderer at the real in-game sprite dimensions, plus a full background, palette snapshot, and representative effects.
- `rendered/original`: new Guy and DHH character overrides using the Original UI palette. The actual original Guy sprite is in `original/`.
- `contact-sheets/`: labeled enlarged inventories. Native dimensions appear under every sprite. Repeated frames and transparent states are intentionally included.
- `drawing-source/`: current Python drawing code and theme manifests, the actual editable source for the new graphics.
- `animation-sequences.json`: frame order and approximate per-frame duration, derived from the legacy animation definitions. Runtime orientations are flips/rotations of these canonical sprites rather than separate authored files.
- `manifest.json`: filenames, dimensions, categories, animation state/frame and pixel hashes. Identical hashes identify repeated visual frames.

This pack contains {len(entries)} review PNGs, plus {len(sheets)} contact sheets and the overview. Current system palette snapshot: **{system_name}**.

## What needs art work

The refresh build currently draws new art in `refresh/art.py`; it does not load these exported PNGs. Editing an export is useful for design review, but it will require an image-pack loader or a drawing-code change to appear in the game. Keep replacements in a separate folder, and preserve the filename when describing a proposed replacement.

Many new states (standing/jumping/shouting, several enemy states) share the same drawing. Exit/death use limited fades; running uses very few distinct poses. The DHH cameo is a rough code-drawn placeholder. These exports expose those limitations without inventing missing art. Effects are line/circle primitives; their reference PNGs are illustrative snapshots rather than original sprite assets. The new UI is also code-drawn; original UI graphics are included in the original picture inventory.

Review sprites enlarged with nearest-neighbor scaling. Canonical sprite PNGs retain native size, transparency and the current palette. Do not enlarge the canvas to alter collision behavior: the build still takes collision geometry from the original game's entities.

## Credit

Original content by Olli “Hectigo” Etuaho: CC BY 3.0. New drawing code and code-drawn graphics: GPL version 2. Full credits and licenses accompany the pack. Exporting files does not transfer or change their licenses.
'''
(out/'README.md').write_text(readme)
archive=out.parent/f'whichwayisup-sprites-{stamp}.zip'
with ZipFile(archive,'w',ZIP_DEFLATED) as z:
    for path in sorted(out.rglob('*')):
        if path.is_file():z.write(path,Path('whichwayisup-sprites')/path.relative_to(out))
# Verify raw originals and inventory before declaring the export complete.
for src in (ROOT/'data/pictures').iterdir():
    if src.is_file():assert src.read_bytes()==(out/'original/source'/src.name).read_bytes()
for e in entries:
    image=pygame.image.load(out/e['path'])
    assert image.get_size()==(e['width'],e['height'])
with ZipFile(archive) as z:assert z.testzip() is None
print(json.dumps(dict(folder=str(out),archive=str(archive),original_pngs=raw_count,review_pngs=len(entries),contact_sheets=len(sheets),sequences=len(sequences),archive_bytes=archive.stat().st_size),indent=2))
pygame.quit()
