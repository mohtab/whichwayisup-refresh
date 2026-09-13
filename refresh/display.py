"""Resizable desktop window with fullscreen rollback and safe startup."""
import time
import pygame
from .desktop import resize_own_window

class Display:
    def __init__(self,settings):
        self.settings=settings
        desktop=pygame.display.get_desktop_sizes()[0]
        w=min(settings['window'][0],max(640,int(desktop[0]*.90)))
        h=min(settings['window'][1],max(480,int(desktop[1]*.88)))
        self.windowed=(w,h)
        self.screen=pygame.display.set_mode(self.windowed,pygame.RESIZABLE)
        pygame.display.set_caption('Which Way Is Up? — Omarchy Refresh')
        self.fullscreen=False;self.deadline=0.;self.confirmed=False
        self.viewport=pygame.Rect(0,0,*self.screen.get_size())
        self.content_size=(1200,800)
    def cycle_size(self):
        if self.fullscreen:self.toggle()
        desktop=pygame.display.get_desktop_sizes()[0]
        presets=[(800,533),(1000,667),(1200,800),(1440,960)]
        available=[size for size in presets if size[0]<=desktop[0]*.95 and size[1]<=desktop[1]*.90] or [presets[0]]
        current=self.settings['window']
        index=next((i for i,size in enumerate(available) if tuple(current)==size),-1)
        self.windowed=available[(index+1)%len(available)]
        self.screen=pygame.display.set_mode(self.windowed,pygame.RESIZABLE)
        self.settings['window']=list(self.windowed)
        if pygame.display.get_driver()!='dummy':resize_own_window(self.windowed)
        return self.windowed
    def toggle(self):
        if self.fullscreen:
            self.screen=pygame.display.set_mode(self.windowed,pygame.RESIZABLE)
            self.fullscreen=False;self.deadline=0.
        else:
            self.windowed=self.screen.get_size()
            self.screen=pygame.display.set_mode((0,0),pygame.FULLSCREEN)
            self.fullscreen=True;self.deadline=time.monotonic()+10
        self.settings['fullscreen']=self.fullscreen
    def confirm(self):self.deadline=0.
    def check(self):
        if self.deadline and time.monotonic()>self.deadline:self.toggle();return True
        return False
    def present(self,surface):
        self.screen=pygame.display.get_surface()
        w,h=self.screen.get_size()
        sw,sh=surface.get_size();self.content_size=(sw,sh)
        factor=min(w/sw,h/sh)
        size=(max(1,round(sw*factor)),max(1,round(sh*factor)))
        self.viewport=pygame.Rect(0,0,*size);self.viewport.center=(w//2,h//2)
        self.screen.fill((5,8,12))
        scaled=pygame.transform.smoothscale(surface,size)
        self.screen.blit(scaled,self.viewport)
        pygame.display.flip()
    def map(self,pos):
        return ((pos[0]-self.viewport.x)*self.content_size[0]/max(1,self.viewport.w),(pos[1]-self.viewport.y)*self.content_size[1]/max(1,self.viewport.h))
