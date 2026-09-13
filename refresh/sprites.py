"""Raster sprite sheets with consistent body scale and contact anchors.

Sheets are kept intact on disk. Alpha extraction, frame slicing and scaling happen
through Pygame at runtime, with bounded caches. Art never supplies a collision rect.
"""
from functools import lru_cache
from pathlib import Path
import math
import pygame

ROOT=Path(__file__).resolve().parents[1]/'assets/sprites'

@lru_cache(maxsize=4)
def sheet(name):
    surface=pygame.image.load(str(ROOT/name)).convert_alpha()
    if surface.get_at((0,0)).a!=0:raise ValueError('Sprite sheet must have a transparent background: '+name)
    return surface

@lru_cache(maxsize=80)
def source_frame(name,columns,rows,index):
    source=sheet(name);w,h=source.get_size()
    if name=='explorer-run-v1.png':
        # Reviewed alpha bounds: the long stride/scarf exceeds nominal grid cells.
        rects=((22,18,271,235),(330,36,178,220),(542,10,179,246),
               (776,19,264,234),(1092,35,196,221),(1327,13,181,243))
        rect=pygame.Rect(rects[index%6])
        return source.subsurface(rect).copy(),rect
    col=index%columns;row=index//columns
    rect=pygame.Rect(round(col*w/columns),round(row*h/rows),0,0)
    rect.width=round((col+1)*w/columns)-rect.x
    rect.height=round((row+1)*h/rows)-rect.y
    frame=source.subsurface(rect)
    bounds=frame.get_bounding_rect(min_alpha=96)
    return frame.subsurface(bounds).copy(),bounds

@lru_cache(maxsize=768)
def player(w,h,state,phase,scale=1):
    phase=int(phase)%16
    if state=='walking':index=(0,1,2,3,4,5)[int(phase*6/16)]
    elif state=='takeoff':index=7 if phase<2 else 8
    elif state=='rising':index=8
    elif state=='apex':index=9
    elif state=='falling':index=10
    elif state=='gliding':index=11
    elif state=='landing':index=(12,13,14,15,16,17)[min(5,phase)]
    elif state in ('hurt','shouting'):index=20 if phase<2 else 21 if phase<5 else 22
    elif state in ('dying','gone'):index=23
    elif state=='exit':index=7
    else:index=18 if phase==15 else 17
    frame,bounds=source_frame('explorer-run-v1.png' if state=='walking' else 'explorer-v1.png',6,4,index)
    # A standing body is ~225 source pixels. Crouches keep this scale instead of
    # being stretched back to standing height. The scarf can extend past the body.
    factor=(h+7)*scale/(235 if state=='walking' else 225)
    size=(max(1,round(frame.get_width()*factor)),max(1,round(frame.get_height()*factor)))
    art=pygame.transform.smoothscale(frame,size)
    canvas=pygame.Surface(((w+36)*scale,(h+14)*scale),pygame.SRCALPHA)
    x=round(canvas.get_width()/2+(-frame.get_width()*.65 if state=='walking' else bounds.x-145)*factor)
    # Walking bob is in the art. A small additional arc makes the contact cycle clear.
    if state=='walking':
        lean=math.sin(phase*math.tau/16)*2
        art=pygame.transform.rotate(art,lean)
    if state=='gliding':art=pygame.transform.rotate(art,math.sin(phase*math.tau/16)*3)
    canvas.blit(art,(x,canvas.get_height()-art.get_height()))
    if state=='gone':canvas.fill((0,0,0,0))
    return canvas

@lru_cache(maxsize=768)
def spider(w,h,state,phase,scale=1):
    phase=int(phase)%16
    if state=='firing':index=(15,16,17)[min(2,phase//2)]
    elif state=='charged':index=13
    elif state=='walking':index=6+int(phase*6/16)
    else:index=18+int(phase*6/16)
    frame,bounds=source_frame('spider-v1.png',6,4,index)
    factor=(w-2)*scale/245
    art=pygame.transform.smoothscale(frame,(max(1,round(frame.get_width()*factor)),max(1,round(frame.get_height()*factor))))
    canvas=pygame.Surface((w*scale,h*scale),pygame.SRCALPHA)
    canvas.blit(art,art.get_rect(midbottom=(w*scale//2,h*scale)))
    return canvas

@lru_cache(maxsize=192)
def key(w,h,phase,scale=1):
    frame,bounds=source_frame('compass-key-v1.png',4,4,int(phase)%16)
    factor=scale*min((w-8)/frame.get_width(),(h-4)/285)
    art=pygame.transform.smoothscale(frame,(max(1,round(frame.get_width()*factor)),max(1,round(frame.get_height()*factor))))
    canvas=pygame.Surface((w*scale,h*scale),pygame.SRCALPHA)
    canvas.blit(art,art.get_rect(center=(w*scale//2,h*scale//2)))
    return canvas


def spider_angle(attached,flipcounter=0,flipping=False,direction=1,alpha=1.):
    # Canonical raster faces out from a FLOOR. Legacy art instead attaches RIGHT.
    final={0:90,1:0,2:-90,3:180}[attached]
    if flipping:
        progress=max(0.,min(1.,(flipcounter-1+alpha)/31))
        return final+direction*90*(1-progress)
    return final


def orient_spider(image,attached,flipcounter=0,flipping=False,direction=1,alpha=1.):
    angle=spider_angle(attached,flipcounter,flipping,direction,alpha)
    return pygame.transform.rotate(image,angle)
