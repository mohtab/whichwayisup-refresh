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
    face=pygame.font.Font(str(FONT),size);face.set_bold(True);return face

@lru_cache(maxsize=96)
def metal_panel(size, face, edge):
    """Authored recessed/chamfered metal; fixed treatments cached by dimensions."""
    w,h=size;image=pygame.Surface(size,pygame.SRCALPHA);c=min(8,h//5)
    points=[(c,0),(w-c-1,0),(w-1,c),(w-1,h-c-1),(w-c-1,h-1),(c,h-1),(0,h-c-1),(0,c)]
    pygame.draw.polygon(image,face,points)
    pygame.draw.lines(image,mix(face,(0,0,0),.65),False,points[2:]+points[:1],3)
    pygame.draw.lines(image,mix(face,edge,.5),False,points[:3],1)
    pygame.draw.line(image,mix(face,edge,.18),(8,3),(w-9,3))
    if h>75:
        for x in (9,w-10):
            for y in (10,h-11):
                pygame.draw.circle(image,mix(face,edge,.45),(x,y),2)
                pygame.draw.line(image,face,(x-1,y),(x+1,y))
    return image

class UI:
    def __init__(self):
        self.surface=pygame.Surface((1200,800))
        self.buttons=[];self.focus=0;self.mouse=(-1,-1)
    def begin(self,theme):
        self.theme=theme;self.buttons=[];self.surface.fill(theme['background'])
        self.refresh=theme.id=='refresh'
        if self.refresh:
            self.surface.blit(metal_panel((1180,780),theme['background'],theme['accent']),(10,10))
    def text(self,value,x,y,size=18,color=None):
        image=(heading_font(size).render(display_text(value),True,color or self.theme['foreground']) if self.refresh and size>=28 else glyphs(display_text(value),size,tuple(color or self.theme['foreground'])))
        self.surface.blit(image,(x,y));return image.get_rect(topleft=(x,y))
    def fit(self,value,x,y,width,size=18,color=None):
        value=display_text(value)
        while value and font(size).size(value)[0]>width:
            value=value[:-2].rstrip()+'…' if not value.endswith('…') else value[:-2]+'…'
        return self.text(value,x,y,size,color)
    def wrap(self,value,x,y,width,size=18,color=None,limit=20):
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
            self.surface.blit(image,image.get_rect(midleft=(rect.x+18,y)) if align=='left' else image.get_rect(center=(rect.centerx,y)))
        if align=='left':self.text('>',rect.right-26,rect.centery-10,18,t['accent'])
        self.buttons.append(Button(rect,label,action))

    def header(self,section):
        t=self.theme
        if self.refresh:
            self.text(section,36,30,18,t['accent'])
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
