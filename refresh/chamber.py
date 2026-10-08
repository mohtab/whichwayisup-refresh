"""Authored Refresh chamber layers; decorative relief never enters simulation."""
from functools import lru_cache
import math
import pygame

def blend(a,b,t):return tuple(round(x+(y-x)*t) for x,y in zip(a,b))

@lru_cache(maxsize=8)
def background():
    s=pygame.Surface((520,520))
    # A recessed chamber with cool lower fill and a warm, upper-left light well.
    for y in range(520):
        pygame.draw.line(s,blend((20,34,39),(9,20,28),y/520),(0,y),(520,y))
    for col,x in enumerate((-46,126,298,470)):
        pygame.draw.rect(s,(9,21,28),(x,38,144,456),border_radius=60)
        pygame.draw.rect(s,(31,47,50),(x-5,32,154,470),3,border_radius=67)
        pygame.draw.rect(s,(16,29,35),(x,39,144,455),2,border_radius=60)
        # Back-wall courses are irregular and far below solid tile contrast.
        for row,y in enumerate(range(100,500,54)):
            pygame.draw.line(s,(24,37,42),(x+9,y),(x+135,y),1)
            joint=x+45+(row%2)*48
            pygame.draw.line(s,(22,35,40),(joint,y),(joint,y+52),1)
        for rib in (x-11,x+150):
            pygame.draw.line(s,(5,15,22),(rib+4,36),(rib+4,520),5)
            pygame.draw.line(s,(37,50,50),(rib,36),(rib,520),3)
            pygame.draw.line(s,(23,36,41),(rib+2,36),(rib+2,520),2)
    # Recessed circular drive and hanging transmission: visibly behind actors.
    center=(265,240)
    for radius,c,width in ((125,(8,18,25),10),(120,(34,47,49),3),(111,(15,29,35),5),(82,(25,39,44),2)):
        pygame.draw.circle(s,c,center,radius,width)
    for n in range(12):
        a=n*math.tau/12
        start=(265+87*math.cos(a),240+87*math.sin(a));end=(265+108*math.cos(a),240+108*math.sin(a))
        pygame.draw.line(s,(27,42,46),start,end,5)
    pygame.draw.circle(s,(11,24,31),center,40)
    pygame.draw.circle(s,(37,50,51),center,39,2)
    pygame.draw.circle(s,(27,42,47),center,16,3)
    # Broad soft exposure masses, not small repeated decorative light sprites.
    light=pygame.Surface((130,130),pygame.SRCALPHA)
    for y in range(130):
        for x in range(130):
            warm=max(0,1-math.hypot((x-16)/100,(y-4)/96))
            cool=max(0,1-math.hypot((x-120)/82,(y-110)/90))
            light.set_at((x,y),(round(12*warm+3*cool),round(8*warm+7*cool),round(3*warm+10*cool),255))
    s.blit(pygame.transform.smoothscale(light,s.get_size()),(0,0),special_flags=pygame.BLEND_RGB_ADD)
    # Relief falls into recess; keep rear architecture below playable faces.
    s.fill((175,180,186),special_flags=pygame.BLEND_RGB_MULT)
    return s

@lru_cache(maxsize=8)
def surround(size):
    """Stationary room housing fills display margins while room stays square."""
    w,h=size;s=pygame.Surface(size);s.fill((7,13,18))
    wing=max(0,(w-round(h*1040/1120))//2)
    for side in (0,1):
        x0=0 if side==0 else w-wing
        for x in range(wing):
            inward=x/max(1,wing) if side==0 else 1-x/max(1,wing)
            c=blend((7,13,18),(25,37,40),inward**1.7)
            pygame.draw.line(s,c,(x0+x,0),(x0+x,h))
        # Large recessed housings with restrained brass rim and broad shadows.
        cx=x0+wing//2;cy=h//2;r=max(20,wing//2-35)
        for rad,c,width in ((r,(5,11,16),18),(r-5,(43,47,40),3),(r-17,(14,24,30),10),(r-38,(28,38,39),2)):
            if rad>0:pygame.draw.circle(s,c,(cx,cy),rad,width)
        for y in (int(h*.16),int(h*.84)):
            pygame.draw.line(s,(10,18,23),(x0+20,y+7),(x0+wing-20,y+7),12)
            pygame.draw.line(s,(41,44,37),(x0+20,y),(x0+wing-20,y),2)
        edge=x0+wing-7 if side==0 else x0+7
        pygame.draw.line(s,(57,61,50),(edge,0),(edge,h),2)
        pygame.draw.line(s,(11,19,23),(edge+3,0),(edge+3,h),4)
    return s
