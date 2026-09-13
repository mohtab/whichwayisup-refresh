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
        image=glyphs(str(value),size,tuple(color or self.theme['foreground']))
        self.surface.blit(image,(x,y));return image.get_rect(topleft=(x,y))
    def wrap(self,value,x,y,width,size=18,color=None,limit=20):
        line='';rows=0
        for word in str(value).split():
            candidate=(line+' '+word).strip()
            if font(size).size(candidate)[0]>width and line:
                self.text(line,x,y,size,color);y+=size+8;rows+=1;line=word
                if rows>=limit:return y
            else:line=candidate
        if line:self.text(line,x,y,size,color);y+=size+8
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
        if hovered:pygame.draw.rect(self.surface,t['accent'],rect,2,border_radius=9)
        fg=t.readable(bg)
        size=17
        while size>11 and font(size).size(label)[0]>rect.w-24:size-=1
        image=glyphs(label,size,tuple(fg))
        self.surface.blit(image,image.get_rect(center=rect.center))
        self.buttons.append(Button(rect,label,action))
    def header(self,section):
        t=self.theme
        pygame.draw.rect(self.surface,t['accent'],(36,30,8,24),border_radius=3)
        self.text('WHICH WAY IS UP?',58,30,20)
        self.text(section,780,34,14,t['muted'])
        pygame.draw.line(self.surface,t['panel'],(36,76),(1164,76),1)
    def footer(self):
        self.text('Original game by Olli “Hectigo” Etuaho  /  An independent homage',36,769,12,self.theme['muted'])
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
