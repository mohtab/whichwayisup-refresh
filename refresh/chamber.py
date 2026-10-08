"""Authored Refresh chamber layers; decorative relief never enters simulation."""
from functools import lru_cache
import math
import pygame

def blend(a,b,t):return tuple(round(x+(y-x)*t) for x,y in zip(a,b))

@lru_cache(maxsize=1)
def background():
    """Far cavity/masonry layer, independent of the alpha-masked receivers."""
    s=pygame.Surface((520,520));s.fill((12,21,28))
    for y in range(520):pygame.draw.line(s,blend((17,27,33),(7,15,22),y/520),(0,y),(520,y))
    for row,y in enumerate(range(24,520,68)):
        for x in range(-50+(row%2)*63,520,126):
            pygame.draw.rect(s,(8,17,24),(x,y,123,65))
            pygame.draw.line(s,(24,34,39),(x+2,y+1),(x+121,y+1),2)
            pygame.draw.line(s,(17,28,35),(x+2,y+3),(x+2,y+62),2)
    return s

@lru_cache(maxsize=4)
def relief(size):
    from pathlib import Path
    source=pygame.image.load(str(Path(__file__).resolve().parents[1]/'assets/refresh/chamber-relief-v1.png')).convert_alpha()
    surface=pygame.transform.smoothscale(source,size)
    # A recessed material plane: textured relief sits below traversable stone.
    surface.fill((145,149,158,255),special_flags=pygame.BLEND_RGBA_MULT)
    return surface

@lru_cache(maxsize=8)
def surround(size):
    """Stationary room housing fills display margins while room stays square."""
    from .objects import masonry
    w,h=size;result=pygame.Surface(size);result.fill((7,13,18))
    material=masonry((1040,1040)).copy()
    def field(rect,tint):
        layer=material.copy();color=pygame.Surface(layer.get_size());color.fill(tint)
        layer.blit(color,(0,0),special_flags=pygame.BLEND_RGB_MULT)
        old=result.get_clip();result.set_clip(rect)
        for y in range(0,h,1040):
            for x in range(0,w,1040):result.blit(layer,(x,y))
        result.set_clip(old)
    field(result.get_rect(),(36,44,50))
    wing=max(0,(w-round(h*1040/1120))//2)
    # Broad recessed masonry piers meet the room; no illuminated output bezel.
    for left in (True,False):
        x=wing-72 if left else w-wing
        if wing>100:
            field(pygame.Rect(x,0,72,h),(61,64,61))
            pygame.draw.rect(result,(7,13,18),(x+64 if left else x,0,8,h))
            field(pygame.Rect(0 if left else w-wing//2,0,wing//2,h),(24,32,39))
    return result



def lit_relief(size,emitters):
    return cached_lit_relief(size,tuple((round(x,2),round(y,2)) for x,y in emitters))

@lru_cache(maxsize=2)
def cached_lit_relief(size,emitters):
    from . import lighting
    receiver=relief(size)
    return lighting.spatial_response(receiver,receiver.get_rect(),lighting.room_field(emitters,size),warm=lighting.warm_field(emitters,size))
