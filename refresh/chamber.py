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
    from .ui import metal_panel
    # Same worn stone/brass family as the interface, with no unrelated rings.
    return metal_panel(size,(12,22,28),(150,122,72)).copy()



def lit_relief(size,emitters):
    return cached_lit_relief(size,tuple((round(x,2),round(y,2)) for x,y in emitters))

@lru_cache(maxsize=2)
def cached_lit_relief(size,emitters):
    from . import lighting
    receiver=relief(size)
    return lighting.spatial_response(receiver,receiver.get_rect(),lighting.room_field(emitters,size),warm=lighting.warm_field(emitters,size))
