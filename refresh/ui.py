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

@lru_cache(maxsize=1)
def frame_components():
    """One isotropic source scale for every control and panel."""
    source=frame_source();w,h=source.get_size();scale=.085
    source=pygame.transform.smoothscale(source,(round(w*scale),round(h*scale)))
    w,h=source.get_size();c=20
    corners=[source.subsurface(r).copy() for r in ((0,0,c,c),(w-c,0,c,c),(0,h-c,c,c),(w-c,h-c,c,c))]
    strips={
        'top':source.subsurface((c,0,w-2*c,c)).copy(),
        'bottom':source.subsurface((c,h-c,w-2*c,c)).copy(),
        'left':source.subsurface((0,c,c,h-2*c)).copy(),
        'right':source.subsurface((w-c,c,c,h-2*c)).copy()}
    patch=source.subsurface((c+7,c+7,w-2*c-14,h-2*c-14)).copy()
    # Mirrored pair meets its own boundary continuously; quiet slate, fixed grain.
    pw,ph=patch.get_size();face=pygame.Surface((pw*2,ph*2),pygame.SRCALPHA);face.fill((10,20,24,255))
    for x in range(2):
        for y in range(2):face.blit(pygame.transform.flip(patch,bool(x),bool(y)),(x*pw,y*ph))
    tint=pygame.Surface(face.get_size());tint.fill((160,174,182));face.blit(tint,(0,0),special_flags=pygame.BLEND_RGB_MULT)
    return corners,strips,face

def tile_into(target,tile,rect):
    rect=pygame.Rect(rect);old=target.get_clip();target.set_clip(rect)
    for y in range(rect.y,rect.bottom,tile.get_height()):
        for x in range(rect.x,rect.right,tile.get_width()):target.blit(tile,(x,y))
    target.set_clip(old)

def repeat_edge(target,strip,rect,horizontal):
    rect=pygame.Rect(rect);length=strip.get_width() if horizontal else strip.get_height()
    cuts=(0,length//3,2*length//3,length);sequence=(0,2,1,2,0,1,1,0,2,2,1)
    old=target.get_clip();target.set_clip(rect);offset=0;i=0;previous=None
    while offset<(rect.w if horizontal else rect.h):
        index=sequence[i%len(sequence)];start,end=cuts[index:index+2]
        piece=strip.subsurface((start,0,end-start,strip.get_height()) if horizontal else (0,start,strip.get_width(),end-start)).copy()
        # Only the one-texel join is softened; the material itself is never blurred.
        if previous is not None:
            for j in range(piece.get_height() if horizontal else piece.get_width()):
                pos=(0,j) if horizontal else (j,0);a=piece.get_at(pos);b=previous[j]
                piece.set_at(pos,tuple((a[k]+b[k])//2 for k in range(4)))
        previous=[piece.get_at((piece.get_width()-1,j) if horizontal else (j,piece.get_height()-1)) for j in range(piece.get_height() if horizontal else piece.get_width())]
        target.blit(piece,(rect.x+offset,rect.y) if horizontal else (rect.x,rect.y+offset));offset+=end-start;i+=1
    target.set_clip(old)

@lru_cache(maxsize=24)
def reading_surface(size):
    result=pygame.Surface(size,pygame.SRCALPHA);result.fill((10,20,24,255))
    tile_into(result,frame_components()[2],result.get_rect());return result

@lru_cache(maxsize=96)
def metal_panel(size, face, edge):
    """Fixed-scale corners/lips; varying lengths reveal cropped repeated material."""
    w,h=size;c=20;corners,strips,_=frame_components();result=pygame.Surface(size,pygame.SRCALPHA)
    tile_into(result,frame_components()[2],(7,7,w-14,h-14))
    for name,rect in (('top',(c,0,w-2*c,c)),('bottom',(c,h-c,w-2*c,c)),('left',(0,c,c,h-2*c)),('right',(w-c,c,c,h-2*c))):
        if rect[2]>0 and rect[3]>0:repeat_edge(result,strips[name],rect,name in ('top','bottom'))
    for image,pos in zip(corners,((0,0),(w-c,0),(0,h-c),(w-c,h-c))):result.blit(image,pos)
    if sum(face)>280 and h<90:
        inner=pygame.Rect(16,10,w-32,h-20);patch=reading_surface(inner.size).copy()
        warm=pygame.Surface(inner.size);warm.fill((155,119,65));patch.blit(warm,(0,0),special_flags=pygame.BLEND_RGB_ADD)
        mask=pygame.Surface(inner.size,pygame.SRCALPHA);iw,ih=inner.size
        points=[(7,0),(iw-7,0),(iw,ih//2),(iw-7,ih),(7,ih),(0,ih//2)]
        pygame.draw.polygon(mask,(255,255,255,255),points)
        pygame.draw.line(patch,(218,185,120),(8,1),(iw-8,1));pygame.draw.line(patch,(97,71,38),(8,ih-2),(iw-8,ih-2),2)
        patch.blit(mask,(0,0),special_flags=pygame.BLEND_RGBA_MULT);result.blit(patch,inner)
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
    def button(self,label,rect,action,primary=False,selected=False,align='center',quiet=False):
        if self.refresh:return self.material_button(label,rect,action,primary,selected,align,quiet)
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
    def material_button(self,label,rect,action,primary=False,selected=False,align='center',quiet=False):
        rect=pygame.Rect(rect);rect.h=max(44,rect.h);index=len(self.buttons);t=self.theme
        focused=self.focus==index;hovered=rect.collidepoint(self.mouse)
        bg=mix(t['accent'],t['panel'],.16) if primary else t['panel']
        if hovered:bg=mix(bg,t['foreground'],.07)
        self.surface.blit(reading_surface(rect.size) if quiet else metal_panel(rect.size,bg,t['accent']),rect)
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
