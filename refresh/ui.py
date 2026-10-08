"""Small immediate UI with mouse, keyboard and controller focus."""
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
import pygame
from .art import mix

FONT=Path(__file__).resolve().parents[1]/'data/misc/Vera.ttf'
@lru_cache(maxsize=40)
def font(size):return pygame.font.Font(str(FONT),size)
@lru_cache(maxsize=512)
def glyphs(value,size,color):return font(size).render(value,True,color)

def display_text(value):
    # Vera has no arrow glyphs; use readable words instead of missing-glyph boxes.
    return str(value).translate(str.maketrans({'←':'Left', '→':'Right', '↑':'Up', '↓':'Down'}))

def wrapped_lines(value,width,size):
    lines=[]
    for paragraph in display_text(value).split('\n'):
        line=''
        for word in paragraph.split():
            candidate=(line+' '+word).strip()
            if font(size).size(candidate)[0]<=width:
                line=candidate;continue
            if line:lines.append(line);line=''
            for char in word:
                if line and font(size).size(line+char)[0]>width:
                    lines.append(line);line=''
                line+=char
        lines.append(line)
    return lines


@dataclass
class Button:
    rect:pygame.Rect
    label:str
    action:object

@lru_cache(maxsize=24)
def heading_font(size):
    return pygame.font.Font(str(FONT.with_name('LiberationSerif-Bold.ttf')),size)

@lru_cache(maxsize=1)
def frame_source():
    image=pygame.image.load(str(FONT.parents[1].parent/'assets/refresh/ui-frame-v1.png')).convert_alpha()
    return image.subsurface(image.get_bounding_rect(min_alpha=8)).copy()

@lru_cache(maxsize=96)
def metal_panel(size, face, edge):
    """Original illustrated nine-slice relief; no repeated pixel work per frame."""
    w,h=size;source=frame_source();sw,sh=source.get_size()
    border=min(18 if h<=120 else 36,max(12,h//2-1),w//2-1);cut=min(sw,sh)//5
    sx=(0,cut,sw-cut,sw);sy=(0,cut,sh-cut,sh)
    dx=(0,border,w-border,w);dy=(0,border,h-border,h)
    result=pygame.Surface(size,pygame.SRCALPHA)
    pygame.draw.rect(result,(10,20,24,255),(border//2,border//2,w-border,h-border))
    for y in range(3):
        for x in range(3):
            tile=source.subsurface((sx[x],sy[y],sx[x+1]-sx[x],sy[y+1]-sy[y]))
            tile=pygame.transform.smoothscale(tile,(dx[x+1]-dx[x],dy[y+1]-dy[y]))
            if x==y==1 and sum(face)>280:
                warm=pygame.Surface(tile.get_size(),pygame.SRCALPHA);warm.fill((142,105,55,0));tile.blit(warm,(0,0),special_flags=pygame.BLEND_RGBA_ADD)
            result.blit(tile,(dx[x],dy[y]))
    if sum(face)>280 and h<90:
        inner=pygame.Rect(16,10,w-32,h-20)
        patch=reading_surface(inner.size).copy()
        warm=pygame.Surface(inner.size);warm.fill((155,119,65));patch.blit(warm,(0,0),special_flags=pygame.BLEND_RGB_ADD)
        mask=pygame.Surface(inner.size,pygame.SRCALPHA);iw,ih=inner.size
        pygame.draw.polygon(mask,(255,255,255,255),[(7,0),(iw-7,0),(iw,ih//2),(iw-7,ih),(7,ih),(0,ih//2)])
        patch.blit(mask,(0,0),special_flags=pygame.BLEND_RGBA_MULT);result.blit(patch,inner)
    return result

@lru_cache(maxsize=24)
def reading_surface(size):
    source=frame_source();w,h=source.get_size()
    tile=source.subsurface((w//4,h//4,w//2,h//2))
    image=pygame.transform.smoothscale(tile,size)
    result=pygame.Surface(size,pygame.SRCALPHA);result.fill((10,20,24,255));result.blit(image,(0,0))
    tint=pygame.Surface(size);tint.fill((170,180,185));result.blit(tint,(0,0),special_flags=pygame.BLEND_RGB_MULT)
    return result

class UI:
    def __init__(self):
        self.surface=pygame.Surface((1200,800))
        self.buttons=[];self.focus=0;self.mouse=(-1,-1)
    def begin(self,theme):
        self.theme=theme;self.buttons=[];self.surface.fill(theme['background'])
        self.refresh=theme.id=='refresh'
        if self.refresh:
            self.surface.blit(reading_surface((1200,800)),(0,0))
    def text(self,value,x,y,size=18,color=None):
        if self.refresh:
            size=max(16,size)
            if color==self.theme['muted']:color=mix(color,self.theme['foreground'],.35)
        image=(heading_font(size).render(display_text(value),True,color or self.theme['foreground']) if self.refresh and size>=28 else glyphs(display_text(value),size,tuple(color or self.theme['foreground'])))
        self.surface.blit(image,(x,y));return image.get_rect(topleft=(x,y))
    def fit(self,value,x,y,width,size=18,color=None):
        if self.refresh:size=max(16,size)
        value=display_text(value)
        while value and font(size).size(value)[0]>width:
            value=value[:-2].rstrip()+'…' if not value.endswith('…') else value[:-2]+'…'
        return self.text(value,x,y,size,color)
    def wrap(self,value,x,y,width,size=18,color=None,limit=20):
        if self.refresh:size=max(16,size)
        lines=wrapped_lines(value,width,size)
        for i,line in enumerate(lines[:limit]):
            if i==limit-1 and len(lines)>limit:line=line.rstrip()+'…'
            self.fit(line,x,y,width,size,color);y+=size+8
        return y
    def panel(self,rect):
        if self.refresh:
            rect=pygame.Rect(rect);self.surface.blit(metal_panel(rect.size,self.theme['panel'],self.theme['accent']),rect)
        else:pygame.draw.rect(self.surface,self.theme['panel'],rect,border_radius=16)
    def button(self,label,rect,action,primary=False,selected=False,align='center'):
        if self.refresh:return self.material_button(label,rect,action,primary,selected,align)
        rect=pygame.Rect(rect);index=len(self.buttons)
        hovered=rect.collidepoint(self.mouse) or self.focus==index
        t=self.theme
        bg=t['accent'] if primary or selected else t['panel']
        if hovered:bg=mix(bg,t['foreground'],.10)
        pygame.draw.rect(self.surface,bg,rect,border_radius=9)
        if not (primary or selected):pygame.draw.rect(self.surface,mix(t['panel'],t['muted'],.25),rect,1,border_radius=9)
        if hovered:pygame.draw.rect(self.surface,t['accent'],rect,2,border_radius=9)
        fg=t.readable(bg)
        label=display_text(label)
        size=17
        while size>11 and font(size).size(label)[0]>rect.w-24:size-=1
        shown=label
        while font(size).size(shown)[0]>rect.w-24 and len(shown)>1:shown=shown[:-2]+'…'
        image=glyphs(shown,size,tuple(fg))
        self.surface.blit(image,image.get_rect(center=rect.center))
        self.buttons.append(Button(rect,label,action))
    def material_button(self,label,rect,action,primary=False,selected=False,align='center'):
        rect=pygame.Rect(rect);rect.h=max(44,rect.h);index=len(self.buttons);t=self.theme
        focused=self.focus==index;hovered=rect.collidepoint(self.mouse)
        bg=mix(t['accent'],t['panel'],.16) if primary else t['panel']
        if hovered:bg=mix(bg,t['foreground'],.07)
        self.surface.blit(metal_panel(rect.size,bg,t['accent']),rect)
        if selected:
            pygame.draw.line(self.surface,t['accent'],(rect.x+18,rect.bottom-5),(rect.right-18,rect.bottom-5),3)
            pygame.draw.rect(self.surface,t['accent'],(rect.x+7,rect.y+rect.h//2-3,5,6))
        if focused:
            pygame.draw.rect(self.surface,t['foreground'],rect.inflate(4,4),1)
            pygame.draw.rect(self.surface,t['accent'],rect.inflate(8,8),1)
            pygame.draw.polygon(self.surface,t['accent'],[(rect.x-9,rect.centery-4),(rect.x-4,rect.centery),(rect.x-9,rect.centery+4)])
        label=display_text(label);size=18
        # Wrapped labels retain readable type rather than silently shrinking to11px.
        lines=wrapped_lines(label,rect.w-32,size)
        if len(lines)>2:lines=wrapped_lines(label,rect.w-24,16);size=16
        total=len(lines)*(size+2)
        for i,line in enumerate(lines):
            image=glyphs(line,size,tuple(t.readable(bg)))
            y=rect.centery-total/2+(i+.5)*(size+2)
            self.surface.blit(image,image.get_rect(midleft=(rect.x+28,y)) if align=='left' else image.get_rect(center=(rect.centerx,y)))
        if align=='left':self.text('>',rect.right-26,rect.centery-10,18,t['accent'])
        self.buttons.append(Button(rect,label,action))

    def header(self,section):
        t=self.theme
        if self.refresh:
            self.text(section,50,30,18,t['accent'])
            pygame.draw.line(self.surface,mix(t['panel'],t['accent'],.25),(36,65),(1164,65))
            return
        pygame.draw.rect(self.surface,t['accent'],(36,30,8,24),border_radius=3)
        self.text('WHICH WAY IS UP?',58,30,20)
        self.fit(section,690,34,345,13,t['muted'])
        pygame.draw.line(self.surface,t['panel'],(36,76),(1164,76),1)
    def footer(self):
        self.text('F1  Controls     F2  Window size     F6  Theme     F10  Settings     F11  Fullscreen',36,775 if self.refresh else 771,14 if self.refresh else 12,self.theme['muted'])
    def activate(self,index=None):
        if not self.buttons:return
        b=self.buttons[(self.focus if index is None else index)%len(self.buttons)]
        b.action()
    def move(self,delta):
        if self.buttons:self.focus=(self.focus+delta)%len(self.buttons)
    def click(self,pos):
        for i,b in enumerate(self.buttons):
            if b.rect.collidepoint(pos):self.focus=i;self.activate(i);return True
        return False
