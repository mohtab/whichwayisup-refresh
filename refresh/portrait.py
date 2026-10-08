"""Portrait assembly from the full-resolution owned character atlas.

Uses the original illustration, never a rendered gameplay sprite. The source's
head, goggles, scarf and shoulder detail retain the established painted identity.
A curved shoulder matte and directional silhouette finish are authored at output
resolution; all work is cached and independent of the live actor pose.
"""
from functools import lru_cache
import pygame
from .sprites import source_frame

@lru_cache(maxsize=2)
def speaker():
    source,_=source_frame('explorer-v1.png',6,4,17)
    # Head through upper coat. No feet/full-body enlargement in the speech UI.
    bust=source.subsurface((0,0,157,159)).copy()
    image=pygame.transform.smoothscale(bust,(296,300))
    matte=pygame.Surface(image.get_size(),pygame.SRCALPHA)
    pygame.draw.polygon(matte,(255,255,255,255),[(0,0),(296,0),(296,245),(259,274),(211,287),(157,292),(109,277),(56,272),(0,248)])
    image.blit(matte,(0,0),special_flags=pygame.BLEND_RGBA_MULT)
    result=pygame.Surface((320,300),pygame.SRCALPHA)
    silhouette=pygame.mask.from_surface(image,80).to_surface(setcolor=(4,14,18,145),unsetcolor=(0,0,0,0))
    result.blit(silhouette,(20,5));result.blit(image,(12,0))
    return result
