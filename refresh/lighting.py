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
    result.fill((32,37,29,0) if wall else (12,16,13,0),special_flags=pygame.BLEND_RGB_ADD)
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

def room_field(emitters,size):
    field=room_ambient().copy()
    pool=receiving_pool()
    for x,y in emitters:field.blit(pool,(round(x/4-30),round(y/4-30)),special_flags=pygame.BLEND_RGB_ADD)
    return pygame.transform.smoothscale(field,size)

def spatial_response(image,rect,field,actor=False):
    """Sample room light after sprite orientation; preserve every source alpha."""
    result=image.copy();light=pygame.Surface(image.get_size());light.fill((102,126,145))
    area=rect.clip(field.get_rect())
    if area.width and area.height:light.blit(field, (area.x-rect.x,area.y-rect.y),area)
    if actor:light.fill((165,175,180),special_flags=pygame.BLEND_RGB_MAX)
    result.blit(light,(0,0),special_flags=pygame.BLEND_RGB_MULT)
    return result
