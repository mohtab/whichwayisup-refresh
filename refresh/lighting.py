"""Bounded software lighting passes for SDL surfaces; no GPU context required."""
from functools import lru_cache
import pygame

@lru_cache(maxsize=192)
def quiet_wall(image,color,border=2):
    """Lower decorative contrast while retaining the tile's solid outer edge."""
    result=image.copy()
    interior=result.get_rect().inflate(-2*border,-2*border)
    if interior.width>0 and interior.height>0:
        veil=pygame.Surface(interior.size,pygame.SRCALPHA)
        veil.fill((*color,82))
        result.blit(veil,interior)
    return result

@lru_cache(maxsize=384)
def silhouette(image,color,width=1,high_contrast=False):
    """A subtle keyline, or an optional bright rim, separates actors from scenery.

    Work inside the existing canvas so animation anchors and support alignment
    remain unchanged. Cached source surfaces are never modified.
    """
    mask=pygame.mask.from_surface(image,80)
    result=pygame.Surface(image.get_size(),pygame.SRCALPHA)
    strokes=((2*width,(5,9,14,220)),(width,(*color,160))) if high_contrast else ((width,(*color,150)),)
    for radius,rgba in strokes:
        stroke=mask.to_surface(setcolor=rgba,unsetcolor=(0,0,0,0))
        for dx,dy in ((-radius,0),(radius,0),(0,-radius),(0,radius)):
            result.blit(stroke,(dx,dy))
    result.blit(image,(0,0))
    return result

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


@lru_cache(maxsize=384)
def refresh_relief(image,glow=0,wall=False,scale=1):
    """Upper-left key over opaque sprite faces; warm nearby light bounce.

    Alpha is unchanged, so visual silhouette and collision alignment agree.
    Bounded cached surfaces use only quantized emitter proximity.
    """
    result=image.copy()
    # Neutral material response preserves texels; spatial exposure is applied later.
    result.fill((73,76,54,0) if wall else (20,22,15,0),special_flags=pygame.BLEND_RGB_ADD)
    if glow:result.fill((glow*8,glow*4,0,0),special_flags=pygame.BLEND_RGB_ADD)
    if wall:
        # Lit upper return and dark lower return reinforce the existing bevel.
        w,h=image.get_size()
        edge=pygame.Surface((w,h),pygame.SRCALPHA)
        pygame.draw.line(edge,(212,188,126,105),(2,1),(w-3,1),max(1,scale))
        pygame.draw.line(edge,(2,10,15,155),(2,h-2),(w-2,h-2),max(1,scale*2))
        result.blit(edge,(0,0))
    return result


@lru_cache(maxsize=1)
def room_ambient():
    import math
    field=pygame.Surface((130,130))
    for y in range(130):
        for x in range(130):
            key=math.exp(-(((x-16)/77)**2+((y-9)/92)**2))
            fill=math.exp(-(((x-123)/64)**2+((y-109)/72)**2))
            field.set_at((x,y),(round(102+139*key+8*fill),round(126+118*key+15*fill),round(145+84*key+19*fill)))
    return field

@lru_cache(maxsize=1)
def receiving_pool():
    import math
    pool=pygame.Surface((60,60));pool.fill((0,0,0))
    for y in range(60):
        for x in range(60):
            distance=math.hypot(x-29.5,y-29.5)/30
            energy=max(0,1-distance)**1.5
            pool.set_at((x,y),(round(170*energy),round(76*energy),round(8*energy)))
    return pool

@lru_cache(maxsize=4)
def static_room_field(size):
    return pygame.transform.smoothscale(room_ambient(),size)

def room_field(emitters,size):
    return static_room_field(size)

def warm_field(emitters,size):
    return cached_warm_field(tuple((round(x,2),round(y,2)) for x,y in emitters),size)

@lru_cache(maxsize=2)
def cached_warm_field(emitters,size):
    field=room_key_radiance().copy()
    pool=receiving_pool()
    for x,y in emitters:field.blit(pool,(round(x/4-30),round(y/4-30)),special_flags=pygame.BLEND_RGB_ADD)
    return pygame.transform.smoothscale(field,size)

def spatial_response(image,rect,field,actor=False,warm=None):
    """Sample room light after sprite orientation; preserve every source alpha."""
    result=image.copy();light=pygame.Surface(image.get_size());light.fill((102,126,145))
    area=rect.clip(field.get_rect())
    if area.width and area.height:light.blit(field, (area.x-rect.x,area.y-rect.y),area)
    if actor:light.fill((165,175,180),special_flags=pygame.BLEND_RGB_MAX)
    result.blit(light,(0,0),special_flags=pygame.BLEND_RGB_MULT)
    if warm is not None and area.width and area.height:
        received=pygame.Surface(image.get_size());received.fill((0,0,0))
        received.blit(warm,(area.x-rect.x,area.y-rect.y),area)
        # Source albedo weights received radiance: dark cracks retain occlusion.
        radiance=image.copy();radiance.blit(received,(0,0),special_flags=pygame.BLEND_RGB_MULT)
        result.blit(radiance,(0,0),special_flags=pygame.BLEND_RGB_ADD)
    return result


@lru_cache(maxsize=1)
def room_key_radiance():
    """Broad warm room key receives on surfaces even between sparse emitters."""
    import math
    layer=pygame.Surface((130,130))
    for y in range(130):
        for x in range(130):
            upper=math.exp(-(((x-30)/53)**2+((y-24)/58)**2))
            lower=math.exp(-(((x-24)/45)**2+((y-118)/36)**2))
            layer.set_at((x,y),(round(88*upper+43*lower),round(42*upper+20*lower),round(6*upper+2*lower)))
    return layer

@lru_cache(maxsize=256)
def connected_wall(image,neighbors,variant,scale):
    """Connected stone facing; no repeated corner cap at interior tile joins."""
    w,h=image.get_size();inset=5*scale
    face=pygame.transform.smoothscale(image.subsurface((inset,inset,w-2*inset,h-2*inset)),(w,h))
    north,east,south,west=neighbors
    if not north:
        pygame.draw.line(face,(146,149,111),(0,0),(w-1,0),scale)
        pygame.draw.line(face,(99,117,103),(0,scale),(w-1,scale),scale)
    if not south:pygame.draw.line(face,(17,36,41),(0,h-scale),(w,h-scale),2*scale)
    if not west:pygame.draw.line(face,(100,120,107),(0,0),(0,h-1),scale)
    if not east:pygame.draw.line(face,(20,41,46),(w-scale,0),(w-scale,h),2*scale)
    # Chips are incised within the solid support line; outer collision stays clear.
    if not north and variant%3:
        x=(9+variant*5)%max(10,w//scale-6)*scale
        pygame.draw.lines(face,(49,66,62),False,[(x,scale),(x+2*scale,3*scale),(x+4*scale,2*scale)],scale)
    if not (west and north) and variant%2==0:
        pygame.draw.line(face,(74,91,80),(2*scale,4*scale),(6*scale,2*scale),scale)
    return face
