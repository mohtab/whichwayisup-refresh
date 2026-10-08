"""Original Refresh object sheet, isolated alpha cells and fixed game anchors."""
from functools import lru_cache
from pathlib import Path
import math
import pygame

@lru_cache(maxsize=4)
def frame(kind):
    source=pygame.image.load(str(Path(__file__).resolve().parents[1]/'assets/refresh/objects-v1.png')).convert_alpha()
    index={'other_pants':0,'power_crystal':1,'cake':2,'blob':3}[kind]
    w,h=source.get_size();left=round(index%2*w/2);top=round(index//2*h/2)
    cell=source.subsurface((left,top,round(w/2),round(h/2)))
    return cell.subsurface(cell.get_bounding_rect(min_alpha=64)).copy()

@lru_cache(maxsize=160)
def sprite(kind,w,h,state,phase,scale):
    source=frame(kind);canvas=pygame.Surface((w*scale,h*scale),pygame.SRCALPHA)
    target_h=h*scale
    if kind=='blob':target_h=max(1,round((h*.83+math.sin(phase*math.tau/16)*1.5)*scale))
    factor=min(w*scale/source.get_width(),target_h/source.get_height())
    size=(max(1,round(source.get_width()*factor)),max(1,round(source.get_height()*factor)))
    image=pygame.transform.smoothscale(source,size)
    canvas.blit(image,image.get_rect(midbottom=(w*scale//2,h*scale)))
    return canvas
