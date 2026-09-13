"""Bounded software lighting passes for SDL surfaces; no GPU context required."""
from functools import lru_cache
import pygame

@lru_cache(maxsize=384)
def shade(image,glow=0):
    result=image.copy()
    ramp=pygame.Surface((2,2))
    ramp.set_at((0,0),(255,252,241));ramp.set_at((1,0),(239,249,252))
    ramp.set_at((0,1),(213,224,230));ramp.set_at((1,1),(180,201,212))
    result.blit(pygame.transform.smoothscale(ramp,image.get_size()),(0,0),special_flags=pygame.BLEND_RGB_MULT)
    if glow:
        result.fill((glow*8,glow*5,glow*2,0),special_flags=pygame.BLEND_RGB_ADD)
    return result

@lru_cache(maxsize=256)
def shadow(image):
    result=image.copy();result.fill((0,0,0,90),special_flags=pygame.BLEND_RGBA_MULT)
    return result

@lru_cache(maxsize=16)
def halo(radius,color):
    surface=pygame.Surface((radius*2,radius*2),pygame.SRCALPHA)
    for r in range(radius,0,-2):
        pygame.draw.circle(surface,(*color,round(28*(1-r/radius)**2)),(radius,radius),r)
    return surface

def proximity(x,y,emitters):
    distance=min(((x-ex)**2+(y-ey)**2 for ex,ey in emitters),default=100000)
    return 3 if distance<35**2 else 2 if distance<65**2 else 1 if distance<95**2 else 0
