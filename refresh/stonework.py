"""Whole dressed stones assembled within canonical solids, baked once per topology.

Raised chipped faces sit over opaque recessed backing. The renderer alone applies
occupancy and screen-space light; these joints never alter support or collision.
"""
from functools import lru_cache
import math
import random
import pygame
from pathlib import Path

REVISION=1

@lru_cache(maxsize=8)
def courses(solids):
    boxes=[(min(p[0] for p in poly),min(p[1] for p in poly),max(p[0] for p in poly),max(p[1] for p in poly)) for poly in solids]
    if not boxes:return ()
    # Include every topology change, so a course never slices through a step.
    breaks=sorted({round(v,5) for b in boxes for v in (b[1],b[3])}|{float(y) for y in range(math.floor(min(b[1] for b in boxes)/20)*20,math.ceil(max(b[3] for b in boxes)/20)*20+1,20)})
    result=[]
    for y,bottom in zip(breaks,breaks[1:]):
        spans=sorted((x,r) for x,t,r,b in boxes if t<(y+bottom)/2<b)
        merged=[]
        for x,r in spans:
            if merged and x<=merged[-1][1]+.001:merged[-1]=(merged[-1][0],max(r,merged[-1][1]))
            else:merged.append((x,r))
        for x,right in merged:
            # Alternate bonds, but absorb narrow residuals into full terminal stones.
            cuts=[x];step=42;offset=21 if round(y/20)%2 else 0
            joint=(math.floor((x-offset)/step)+1)*step+offset
            while joint<right-14:
                if joint-cuts[-1]>=16:cuts.append(joint)
                joint+=step
            cuts.append(right)
            result.extend((a,y,b-a,bottom-y) for a,b in zip(cuts,cuts[1:]))
    return tuple(result)

@lru_cache(maxsize=1)
def grain_patches():
    # Interior mineral only: none of these hand-selected patches includes mortar.
    source=pygame.image.load(str(Path(__file__).resolve().parents[1]/'assets/refresh/masonry-v1.png')).convert()
    w,h=source.get_size()
    regions=((.065,.125,.18,.055),(.32,.14,.14,.05),(.55,.03,.15,.05),(.68,.24,.18,.055),(.27,.57,.18,.045),(.68,.69,.15,.045))
    return tuple(source.subsurface((round(x*w),round(y*h),round(a*w),round(b*h))).copy() for x,y,a,b in regions)

@lru_cache(maxsize=8)
def constructed_material(solids,scale,revision=REVISION):
    """Fixed800-unit canonical plane centered on the established120-unit pivot."""
    from .objects import exposed_edges
    edges=exposed_edges(solids)
    # Wayland's default display format may carry unused alpha bytes. Rotating
    # that format enables blending and hides the baked faces; use opaque RGB.
    result=pygame.Surface((800*scale,800*scale),0,32,(0xff0000,0xff00,0xff,0));result.fill((22,32,28))
    for x,y,w,h in courses(solids):
        seed=round(x*197+y*733+w*71+h*31);rng=random.Random(seed)
        rect=pygame.Rect(round((x+280)*scale),round((y+280)*scale),round(w*scale),round(h*scale))
        # A whole block: dark mortar bed, substantial end/underside and a chipped face.
        pygame.draw.rect(result,(34,43,35),rect)
        terminal=any(abs(a[0]-b[0])<.001 and (abs(x-a[0])<.001 or abs(x+w-a[0])<.001) and min(a[1],b[1])<y+h/2<max(a[1],b[1]) for a,b in edges)
        pad=.65*scale;bevel=(3.0 if terminal else 2.0)*scale
        l,t,r,b=rect.left+pad,rect.top+pad,rect.right-pad,rect.bottom-pad
        chip=[rng.uniform(1.1,2.8)*scale for _ in range(4)]
        outline=[(l+chip[0],t),(r-chip[1],t),(r,t+chip[1]),(r,b-chip[2]),(r-chip[2],b),(l+chip[3],b),(l,b-chip[3]),(l,t+chip[0])]
        base=(85+rng.randrange(-9,10),96+rng.randrange(-8,9),76+rng.randrange(-8,9))
        pygame.draw.polygon(result,tuple(max(0,c-29) for c in base),outline)
        inner=[(l+bevel,t+bevel*.75),(r-bevel,t+bevel*.65),(r-bevel*.7,b-bevel),(l+bevel,b-bevel*.8)]
        pygame.draw.polygon(result,base,inner)
        pygame.draw.polygon(result,tuple(c+17 for c in base),[outline[0],outline[1],outline[2],inner[1],inner[0]])
        pygame.draw.polygon(result,tuple(c-12 for c in base),[outline[2],outline[3],outline[4],inner[2],inner[1]])
        pygame.draw.polygon(result,tuple(c-24 for c in base),[outline[4],outline[5],outline[6],inner[3],inner[2]])
        # Neutral mineral grain is fitted to each COMPLETE face, never projected
        # across joints. Face bevels and terminals remain assembled geometry.
        patch=grain_patches()[seed%6]
        pw,ph=patch.get_size();density=min(2.5,pw/w,ph/h)
        cw,ch=max(1,round(w*density)),max(1,round(h*density))
        patch=patch.subsurface(((pw-cw)//2,(ph-ch)//2,cw,ch))
        face=pygame.transform.smoothscale(patch,rect.size).convert_alpha()
        face.fill((174+seed%13,181+seed%9,166+seed%11,255),special_flags=pygame.BLEND_RGBA_MULT)
        mask=pygame.Surface(rect.size,pygame.SRCALPHA)
        facepoints=[(l+bevel,t+bevel*.75),((l+r)*.5,t+bevel*(.5+seed%3*.15)),(r-bevel,t+bevel*.65),(r-bevel*.7,b-bevel),(l+(r-l)*.43,b-bevel*(.7+seed%4*.1)),(l+bevel,b-bevel*.8)]
        pygame.draw.polygon(mask,(255,255,255,255),[(px-rect.x,py-rect.y) for px,py in facepoints])
        face.blit(mask,(0,0),special_flags=pygame.BLEND_RGBA_MULT);result.blit(face,rect)
        # Tool scars meet the dressed arris, and stop before the recessed backing.
        for i in range(max(2,round(w/9))):
            px=l+rng.uniform(.15,.85)*(r-l)
            pygame.draw.line(result,tuple(c+8 for c in base),(px,t+scale),(px+scale,t+bevel*.8),max(1,scale//2))
        # Interrupted tool nicks stay within the solid recessed backing.
        for fraction in (.28,.73):
            px=l+(r-l)*fraction
            pygame.draw.line(result,tuple(c-15 for c in base),(px,t),(px+scale,t+scale),max(1,scale))
    return result
