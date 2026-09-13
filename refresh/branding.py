"""Omarchy's unmodified emblem with presentation-only glow and breathing."""
from functools import lru_cache
from pathlib import Path
import math
import pygame
from .lighting import halo

@lru_cache(maxsize=1)
def emblem():
    return pygame.image.load(str(Path(__file__).resolve().parents[1]/'assets/branding/omarchy-icon.png')).convert_alpha()

@lru_cache(maxsize=64)
def collectible(w,h,phase,scale=1,animate=True):
    pulse=(math.sin(int(phase)%32*math.tau/32)+1)/2 if animate else .5
    side=round((min(w,h)-10)*(0.9+0.1*pulse)*scale)
    art=pygame.transform.smoothscale(emblem(),(side,side))
    art.set_alpha(round(215+40*pulse))
    canvas=pygame.Surface((w*scale,h*scale),pygame.SRCALPHA)
    radius=max(1,round((min(w,h)/2-1)*scale))
    glow=halo(radius,(158,206,106)).copy();glow.set_alpha(round(160+95*pulse))
    canvas.blit(glow,glow.get_rect(center=canvas.get_rect().center))
    # Tight emissive rim follows the actual mark instead of turning it into a disc.
    rim=art.copy();rim.set_alpha(round(22+18*pulse))
    center=art.get_rect(center=canvas.get_rect().center)
    for dx,dy in ((-scale,0),(scale,0),(0,-scale),(0,scale)):
        canvas.blit(rim,center.move(dx,dy))
    canvas.blit(art,center)
    return canvas
