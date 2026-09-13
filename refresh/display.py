"""Resizable desktop window with fullscreen rollback and safe startup."""
import time
import pygame

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
        factor=min(w/1200,h/800)
        size=(max(1,round(1200*factor)),max(1,round(800*factor)))
        self.viewport=pygame.Rect(0,0,*size);self.viewport.center=(w//2,h//2)
        self.screen.fill((5,8,12))
        scaled=pygame.transform.smoothscale(surface,size)
        self.screen.blit(scaled,self.viewport)
        pygame.display.flip()
    def map(self,pos):
        return ((pos[0]-self.viewport.x)*1200/max(1,self.viewport.w),(pos[1]-self.viewport.y)*800/max(1,self.viewport.h))
