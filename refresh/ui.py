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

class UI:
    def __init__(self):
        self.surface=pygame.Surface((1200,800))
        self.buttons=[];self.focus=0;self.mouse=(-1,-1)
    def begin(self,theme):
        self.theme=theme;self.buttons=[];self.surface.fill(theme['background'])
    def text(self,value,x,y,size=18,color=None):
        image=glyphs(display_text(value),size,tuple(color or self.theme['foreground']))
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
        pygame.draw.rect(self.surface,self.theme['panel'],rect,border_radius=16)
    def button(self,label,rect,action,primary=False,selected=False):
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
    def header(self,section):
        t=self.theme
        pygame.draw.rect(self.surface,t['accent'],(36,30,8,24),border_radius=3)
        self.text('WHICH WAY IS UP?',58,30,20)
        self.fit(section,690,34,345,13,t['muted'])
        pygame.draw.line(self.surface,t['panel'],(36,76),(1164,76),1)
    def footer(self):
        self.text('F1  Controls     F2  Window size     F6  Theme     F10  Settings     F11  Fullscreen',36,771,12,self.theme['muted'])
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
