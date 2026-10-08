"""Original Refresh object sheet, isolated alpha cells and fixed game anchors."""
from functools import lru_cache
from pathlib import Path
import math
import pygame
from . import terrain_sampler

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

@lru_cache(maxsize=6)
def wall_frame(index):
    source=pygame.image.load(str(Path(__file__).resolve().parents[1]/'assets/refresh/terrain-v1.png')).convert_alpha()
    w,h=source.get_size();col=index%3;row=index//3
    x=round(col*w/3);y=round(row*h/2);right=round((col+1)*w/3);bottom=round((row+1)*h/2)
    cell=source.subsurface((x,y,right-x,bottom-y))
    return cell.subsurface(cell.get_bounding_rect(min_alpha=64)).copy()

@lru_cache(maxsize=48)
def wall(w,h,phase,scale):
    return pygame.transform.smoothscale(wall_frame(int(phase)%6),(w*scale,h*scale))

@lru_cache(maxsize=2)
def masonry(size):
    source=pygame.image.load(str(Path(__file__).resolve().parents[1]/'assets/refresh/masonry-v1.png')).convert()
    return pygame.transform.smoothscale(source,size)

@lru_cache(maxsize=2)
def material_source(scale):
    # Full 20x20 level is centered on the actual120,120 pivot, including offscreen tiles.
    size=800*scale;result=pygame.Surface((size,size));texture=masonry((520*scale,520*scale))
    for x in (-240*scale,280*scale):
        for y in (-240*scale,280*scale):result.blit(texture,(x,y))
    return result

def attached_material(size,scale,matrix):
    accelerated=terrain_sampler.material(material_source(scale),size,scale,matrix)
    if accelerated is not None:return accelerated
    c,s=matrix;image=pygame.transform.rotozoom(material_source(scale),-math.degrees(math.atan2(s,c)),math.hypot(c,s))
    result=pygame.Surface(size);result.blit(image,image.get_rect(center=(120*scale,120*scale)))
    return result

def terrain_layer(rectangles,size,scale,polygons=None,matrix=None):
    """One authored material coordinate system, clipped to actual moving solids."""
    occupancy=pygame.Surface(size,pygame.SRCALPHA)
    if polygons is None:
        for rect in rectangles:pygame.draw.rect(occupancy,(255,255,255,255),rect)
    else:
        for polygon in polygons:pygame.draw.polygon(occupancy,(255,255,255,255),polygon)
    mask=pygame.mask.Mask(size)
    for rect in rectangles:mask.draw(solid_rectangle((rect[2],rect[3])),rect[:2])
    result=pygame.Surface(size,pygame.SRCALPHA);result.blit(attached_material(size,scale,matrix) if matrix is not None else masonry(size),(0,0))
    result.blit(occupancy,(0,0),special_flags=pygame.BLEND_RGBA_MULT)
    # Shade a low-resolution relief field; the exact full-resolution union retains alpha.
    relief_size=(max(1,size[0]//4),max(1,size[1]//4))
    relief_mask=pygame.transform.scale(occupancy,relief_size)
    relief=pygame.Surface(relief_size,pygame.SRCALPHA)
    for width in (6*scale,3*scale,scale):
        strength=1-width/(6*scale+1)
        for direction,color,opacity in (((0,1),(200,185,132),int(18+strength*35)),((1,0),(155,176,147),int(12+strength*22)),((0,-1),(4,17,24),int(24+strength*55)),((-1,0),(8,24,32),int(18+strength*40))):
            edge=relief_mask.copy();step=max(1,round(width/4))
            edge.blit(relief_mask,(direction[0]*step,direction[1]*step),special_flags=pygame.BLEND_RGBA_SUB)
            tinted=pygame.Surface(relief_size,pygame.SRCALPHA);tinted.fill((*color,opacity))
            tinted.blit(edge,(0,0),special_flags=pygame.BLEND_RGBA_MULT)
            relief.blit(tinted,(0,0))
    result.blit(pygame.transform.smoothscale(relief,size),(0,0))
    result.blit(occupancy,(0,0),special_flags=pygame.BLEND_RGBA_MULT)
    # Tiny exposed corner chamfers live inside the fixed collision bounds.
    for raw in rectangles:
        rect=pygame.Rect(raw)
        for x,y,dx,dy in ((rect.left,rect.top,1,1),(rect.right-1,rect.top,-1,1),(rect.left,rect.bottom-1,1,-1),(rect.right-1,rect.bottom-1,-1,-1)):
            if not (0<=x<size[0] and 0<=y<size[1]):continue
            def solid(xx,yy):return 0<=xx<size[0] and 0<=yy<size[1] and mask.get_at((xx,yy))
            if not solid(x-dx,y) and not solid(x,y-dy):
                nick=scale+(abs(x+y)//max(1,scale))%scale if scale>1 else 1
                pygame.draw.polygon(result,(0,0,0,0),[(x,y),(x+dx*nick,y),(x,y+dy*nick)])
    shadow=pygame.Surface(size,pygame.SRCALPHA);shadow.fill((0,0,0,110));shadow.blit(occupancy,(0,0),special_flags=pygame.BLEND_RGBA_MULT)
    return result,shadow

def reveal_lever(world,lever,lever_rect,spider,spider_rect,scale):
    """Only covered lever contour reads through the real spider alpha overlap."""
    area=lever_rect.clip(spider_rect)
    if not area.width or not area.height:return False
    lm=pygame.mask.from_surface(lever,96);sm=pygame.mask.from_surface(spider,96)
    offset=(spider_rect.x-lever_rect.x,spider_rect.y-lever_rect.y)
    if not lm.overlap(sm,offset):return False
    wire=pygame.Surface(lever.get_size(),pygame.SRCALPHA)
    for component in lm.connected_components(3):
        points=component.outline()
        if len(points)>2:
            pygame.draw.lines(wire,(16,20,22,205),True,points,max(2,2*scale))
            pygame.draw.lines(wire,(242,193,102,185),True,points,max(1,scale))
    clip=pygame.Surface(lever.get_size(),pygame.SRCALPHA)
    clip.blit(sm.to_surface(setcolor=(255,255,255,255),unsetcolor=(0,0,0,0)),offset)
    wire.blit(clip,(0,0),special_flags=pygame.BLEND_RGBA_MULT)
    world.blit(wire,lever_rect)
    return True


@lru_cache(maxsize=2)
def stone_response(size):
    layer=pygame.Surface(size);layer.fill((73,76,54));return layer


@lru_cache(maxsize=8)
def solid_rectangle(size):
    return pygame.mask.Mask(size,fill=True)
