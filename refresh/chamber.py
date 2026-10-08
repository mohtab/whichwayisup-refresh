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
    surface.fill((157,169,180,255),special_flags=pygame.BLEND_RGBA_MULT)
    return surface

@lru_cache(maxsize=8)
def surround(size):
    """Stationary room housing fills display margins while room stays square."""
    w,h=size;s=pygame.Surface(size);s.fill((7,13,18))
    wing=max(0,(w-round(h*1040/1120))//2)
    for side in (0,1):
        x0=0 if side==0 else w-wing
        for x in range(wing):
            inward=x/max(1,wing) if side==0 else 1-x/max(1,wing)
            c=blend((7,13,18),(25,37,40),inward**1.7)
            pygame.draw.line(s,c,(x0+x,0),(x0+x,h))
        # Large recessed housings with restrained brass rim and broad shadows.
        cx=x0+wing//2;cy=h//2;r=max(20,wing//2-35)
        for rad,c,width in ((r,(5,11,16),18),(r-5,(43,47,40),3),(r-17,(14,24,30),10),(r-38,(28,38,39),2)):
            if rad>0:pygame.draw.circle(s,c,(cx,cy),rad,width)
        for y in (int(h*.16),int(h*.84)):
            pygame.draw.line(s,(10,18,23),(x0+20,y+7),(x0+wing-20,y+7),12)
            pygame.draw.line(s,(41,44,37),(x0+20,y),(x0+wing-20,y),2)
        edge=x0+wing-7 if side==0 else x0+7
        pygame.draw.line(s,(57,61,50),(edge,0),(edge,h),2)
        pygame.draw.line(s,(11,19,23),(edge+3,0),(edge+3,h),4)
    return s


def lit_relief(size,emitters):
    return cached_lit_relief(size,tuple((round(x,2),round(y,2)) for x,y in emitters))

@lru_cache(maxsize=2)
def cached_lit_relief(size,emitters):
    from . import lighting
    receiver=relief(size)
    return lighting.spatial_response(receiver,receiver.get_rect(),lighting.room_field(emitters,size),warm=lighting.warm_field(emitters,size))
