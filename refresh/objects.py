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
    size=800*scale;result=pygame.Surface((size,size),0,32,(0xff0000,0xff00,0xff,0));pitch=260*scale
    texture=masonry((pitch,pitch))
    for x in range(-240*scale,size,pitch):
        for y in range(-240*scale,size,pitch):result.blit(texture,(x,y))
    return result

def attached_material(size,scale,matrix,source=None):
    source=material_source(scale) if source is None else source
    accelerated=terrain_sampler.material(source,size,scale,matrix)
    if accelerated is not None:return accelerated
    c,s=matrix;image=pygame.transform.rotozoom(source,-math.degrees(math.atan2(s,c)),math.hypot(c,s))
    result=pygame.Surface(size,0,32,(0xff0000,0xff00,0xff,0));result.blit(image,image.get_rect(center=(120*scale,120*scale)))
    return result


def canonical_solids(polygons,scale,matrix):
    """Recover stable material-space vertices, never screen-space decoration."""
    from .enhanced import transform
    c,s=matrix;den=c*c+s*s
    return tuple(tuple(tuple(round(v,5) for v in transform((x/scale,y/scale),(c/den,-s/den))) for x,y in poly) for poly in polygons)

@lru_cache(maxsize=8)
def exposed_edges(solids):
    """Cancel shared edges before authoring the connected stone end faces."""
    edges=set()
    for poly in solids:
        for a,b in zip(poly,poly[1:]+poly[:1]):
            if (b,a) in edges:edges.remove((b,a))
            else:edges.add((a,b))
    # Merge straight neighbors: corners belong to the union, not each tile.
    changed=True
    while changed:
        changed=False
        starts={a:b for a,b in edges}
        for a,b in sorted(edges):
            c=starts.get(b)
            if c is None:continue
            ab=(b[0]-a[0],b[1]-a[1]);bc=(c[0]-b[0],c[1]-b[1])
            if abs(ab[0]*bc[1]-ab[1]*bc[0])<1e-8 and ab[0]*bc[0]+ab[1]*bc[1]>0:
                edges.remove((a,b));edges.remove((b,c));edges.add((a,c));changed=True;break
    return tuple(sorted(edges))

def terrain_layer(rectangles,size,scale,polygons=None,matrix=None,solids=None):
    """One authored material coordinate system, clipped to actual moving solids."""
    if polygons is None:
        # Refresh previews use legacy sessions, but share the same surface finish.
        polygons=tuple(((x,y),(x+w,y),(x+w,y+h),(x,y+h)) for x,y,w,h in rectangles)
        matrix=(1.,0.)
    occupancy=pygame.Surface(size,pygame.SRCALPHA)
    for polygon in polygons:pygame.draw.polygon(occupancy,(255,255,255,255),polygon)
    from .stonework import constructed_material
    if solids is None:solids=canonical_solids(polygons,scale,matrix)
    source=constructed_material(solids,scale)
    result=pygame.Surface(size,pygame.SRCALPHA);result.blit(attached_material(size,scale,matrix,source),(0,0))
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


@lru_cache(maxsize=64)
def lever_body(image,style=None):
    """Retain the authored handle/gear; the enhanced mount replaces its wide slab."""
    body=image.copy();w,h=body.get_size()
    # Keep the handle and circular gearbox, not the rectangular pedestal beneath
    # it. Rectangular cuts left a second-looking base next to the moving mount.
    mask=pygame.Surface((w,h),pygame.SRCALPHA)
    hub_y=round(h*(.60 if style=='cyberpunk' else .67))
    pygame.draw.rect(mask,(255,255,255,255),(0,0,w,hub_y))
    pygame.draw.circle(mask,(255,255,255,255),(w//2,hub_y),round(min(w,h)*.25))
    mask.fill((0,0,0,0),(0,round(h*.88),w,h))
    body.blit(mask,(0,0),special_flags=pygame.BLEND_RGBA_MULT)
    return body


def lever_mount(center,height,polygons,matrix):
    """Keep a compact socket bolted to one material-space support point.

    The gear stays upright while its short link articulates. Unlike choosing a
    nearest world-space face each frame, the bolt cannot jump across a recess
    when faces exchange proximity. Side-only supports use the same construction.
    """
    from .enhanced import closest,transform
    c,s=matrix;den=c*c+s*s
    local=transform(center,(c/den,-s/den))
    base=(round(local[0],6),round(local[1]+height/2,6))
    contacts=[closest(base,p) for p in polygons]
    contact=min(contacts,key=lambda p:(round(math.dist(base,p),6),p)) if contacts else None
    return transform(contact,matrix) if contact is not None and math.dist(base,contact)<=40 else None


def draw_lever_mount(world,pivot,contact,scale):
    a=tuple(round(v*scale) for v in pivot);b=tuple(round(v*scale) for v in contact)
    pygame.draw.line(world,(30,35,31),a,b,6*scale)
    pygame.draw.line(world,(109,100,62),a,b,4*scale)
    pygame.draw.line(world,(191,159,94),(a[0]-scale,a[1]),(b[0]-scale,b[1]),scale)
    length=math.dist(a,b)
    if length:
        dx=(b[0]-a[0])/length;dy=(b[1]-a[1])/length
        for distance in range(4*scale,max(4*scale,round(length)-2*scale),4*scale):
            x=a[0]+dx*distance;y=a[1]+dy*distance
            pygame.draw.line(world,(55,61,46),(x-dy*2*scale,y+dx*2*scale),(x+dy*scale,y-dx*scale),scale)
    # A flush, subdued wall plate must not resemble another bright switch knob.
    plate=pygame.Rect(0,0,5*scale,4*scale);plate.center=b
    pygame.draw.rect(world,(34,38,32),plate)
    pygame.draw.rect(world,(87,82,57),plate.inflate(-2*scale,-2*scale))
