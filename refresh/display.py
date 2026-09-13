"""Resizable desktop window with fullscreen rollback and safe startup."""
import time
import pygame
from .desktop import resize_own_window

def opaque_canvas(surface):
    """Present finished RGB content without interpreting unused native alpha bytes.

    Wayland display-format canvases may have an alpha mask with blending disabled.
    Surface.copy() re-enables blending for that format. These are fully composed
    canvases, not individual transparent sprites; preserve their RGB pixels.
    """
    if surface.get_alpha() is None and surface.get_colorkey() is None:return surface
    result=surface.copy()
    result.set_alpha(None)
    result.set_colorkey(None)
    return result


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
    def present(self,surface,smooth=None,integer_scale=False,pixel_scale=1,layers=()):
        """Fit the canvas, optionally keeping native pixels at whole-number sizes.

        pixel_scale describes an already enlarged source, e.g. the 2x world art.
        Windows smaller than the native canvas still fit rather than crop it.
        Layers (image, logical_rect, smooth, integer_scale, pixel_scale) are
        composited after the UI so crisp world pixels coexist with smooth text.
        """
        surface=opaque_canvas(surface)
        self.screen=pygame.display.get_surface()
        w,h=self.screen.get_size()
        sw,sh=surface.get_size();self.content_size=(sw,sh)
        factor=min(w/sw,h/sh)
        if integer_scale:
            native_factor=factor*max(1,pixel_scale)
            if native_factor>=1:factor=int(native_factor)/max(1,pixel_scale)
        size=(max(1,round(sw*factor)),max(1,round(sh*factor)))
        self.viewport=pygame.Rect(0,0,*size);self.viewport.center=(w//2,h//2)
        self.screen.fill((5,8,12))
        if smooth is None:smooth=self.settings.get('smooth',False)
        transform=pygame.transform.smoothscale if smooth and not integer_scale else pygame.transform.scale
        scaled=surface if size==(sw,sh) else transform(surface,size)
        self.screen.blit(scaled,self.viewport)
        for image,logical_rect,layer_smooth,layer_integer,layer_pixel_scale in layers:
            image=opaque_canvas(image)
            logical=pygame.Rect(logical_rect)
            left=self.viewport.x+round(logical.left*size[0]/sw)
            top=self.viewport.y+round(logical.top*size[1]/sh)
            right=self.viewport.x+round(logical.right*size[0]/sw)
            bottom=self.viewport.y+round(logical.bottom*size[1]/sh)
            area=pygame.Rect(left,top,right-left,bottom-top)
            if area.width<=0 or area.height<=0:continue
            iw,ih=image.get_size();fit=min(area.width/iw,area.height/ih)
            native=max(1,layer_pixel_scale)
            if layer_integer and fit*native>=1:fit=int(fit*native)/native
            layer_size=(max(1,round(iw*fit)),max(1,round(ih*fit)))
            target=pygame.Rect(0,0,*layer_size);target.center=area.center
            transform=pygame.transform.smoothscale if layer_smooth and not layer_integer else pygame.transform.scale
            scaled=image if layer_size==(iw,ih) else transform(image,layer_size)
            self.screen.fill((5,8,12),area)
            self.screen.blit(scaled,target)
        pygame.display.flip()
    def map(self,pos):
        return ((pos[0]-self.viewport.x)*self.content_size[0]/max(1,self.viewport.w),(pos[1]-self.viewport.y)*self.content_size[1]/max(1,self.viewport.h))
