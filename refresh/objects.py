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
    size=800*scale;result=pygame.Surface((size,size));pitch=260*scale
    texture=masonry((pitch,pitch))
    for x in range(-240*scale,size,pitch):
        for y in range(-240*scale,size,pitch):result.blit(texture,(x,y))
    return result

def attached_material(size,scale,matrix):
    accelerated=terrain_sampler.material(material_source(scale),size,scale,matrix)
    if accelerated is not None:return accelerated
    c,s=matrix;image=pygame.transform.rotozoom(material_source(scale),-math.degrees(math.atan2(s,c)),math.hypot(c,s))
    result=pygame.Surface(size);result.blit(image,image.get_rect(center=(120*scale,120*scale)))
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

def finish_contours(result,occupancy,solids,matrix,scale):
    from .enhanced import transform
    layer=pygame.Surface(result.get_size(),pygame.SRCALPHA)
    def points(values):return [tuple(round(v*scale) for v in transform(p,matrix)) for p in values]
    for a,b in exposed_edges(solids):
        dx,dy=b[0]-a[0],b[1]-a[1];length=math.hypot(dx,dy)
        nx,ny=-dy/length,dx/length
        # Each boundary stone has an inset dressed end face. Its inner arris is
        # chipped, while the outer support line remains the true solid envelope.
        count=max(1,round(length/20))
        for i in range(count):
            t0=i/count;t1=(i+1)/count
            p=(a[0]+dx*t0,a[1]+dy*t0);q=(a[0]+dx*t1,a[1]+dy*t1)
            seed=round(p[0]*13+p[1]*7);depth=2.4+(seed%5)*.42
            innerp=(p[0]+nx*depth,p[1]+ny*depth)
            innerq=(q[0]+nx*depth,q[1]+ny*depth)
            middle=((p[0]+q[0])/2+nx*(depth+.7),(p[1]+q[1])/2+ny*(depth+.7))
            pygame.draw.polygon(layer,(38,49,43,85+(seed%4)*8),points((p,q,innerq,middle,innerp)))
            # Mortar ends on the dressed face instead of being sliced by a mask.
            if i or (seed%3==0):pygame.draw.line(layer,(23,34,31,160),*points((p,innerp)),max(1,scale))
            pygame.draw.lines(layer,(26,37,33,90),False,points((innerp,middle,innerq)),max(1,scale))
        # Convex corner return: two short faces meet inside the exact support.
        pygame.draw.polygon(layer,(30,43,37,95),points((a,(a[0]+dx/length*3,a[1]+dy/length*3),(a[0]+dx/length*3+nx*3,a[1]+dy/length*3+ny*3),(a[0]+nx*3,a[1]+ny*3))))
    layer.blit(occupancy,(0,0),special_flags=pygame.BLEND_RGBA_MULT)
    result.blit(layer,(0,0))

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
    if polygons is not None and matrix is not None:
        finish_contours(result,occupancy,canonical_solids(polygons,scale,matrix),matrix,scale)
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


@lru_cache(maxsize=64)
def lever_body(image):
    """Retain the authored handle/gear; the enhanced mount replaces its wide slab."""
    body=image.copy();w,h=body.get_size()
    # The bottom rail and triangular outriggers belong to the old horizontal base.
    body.fill((0,0,0,0),(0,round(h*.88),w,h))
    body.fill((0,0,0,0),(0,round(h*.64),round(w*.25),h))
    body.fill((0,0,0,0),(round(w*.75),round(h*.64),w,h))
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
    pygame.draw.circle(world,(34,38,32),b,4*scale)
    pygame.draw.circle(world,(137,119,71),b,3*scale)
    pygame.draw.circle(world,(216,180,103),(b[0]-scale,b[1]-scale),scale)
