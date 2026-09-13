"""Palette-driven, code-drawn art; original sprites remain an independent option."""
import math
import pygame


def mix(a,b,t):return tuple(round(x+(y-x)*t) for x,y in zip(a,b))

class Painter:
    def __init__(self):
        self.key=None;self.cache={}
        self.world=pygame.Surface((520,520))
    def configure(self,theme,settings):
        key=(theme.id,tuple(theme.palette.items()),settings['character'],settings['effects'])
        if key!=self.key:
            self.key=key;self.cache.clear()
            self.theme=theme;self.settings=settings.copy()
            self.background=self.make_background()
    def make_background(self):
        t=self.theme
        s=pygame.Surface((520,520))
        for y in range(520):
            pygame.draw.line(s,mix(t['background'],t['panel'],y/900),(0,y),(520,y))
        grid=mix(t['background'],t['secondary'],.10)
        for x in range(0,521,40):pygame.draw.line(s,grid,(x,0),(x,520))
        for y in range(0,521,40):pygame.draw.line(s,grid,(0,y),(520,y))
        if t.style=='cyberpunk':
            for i in range(12):
                x=i*47-18;h=50+(i*37)%120
                pygame.draw.rect(s,mix(t['background'],t['secondary'],.08),(x,520-h,30,h))
                for yy in range(530-h,510,12):pygame.draw.line(s,grid,(x+7,yy),(x+12,yy),2)
        else:
            pygame.draw.circle(s,mix(t['background'],t['accent'],.06),(440,80),140,1)
            pygame.draw.circle(s,mix(t['background'],t['accent'],.07),(440,80),180,1)
        return s
    def sprite(self,kind,w,h,state='default',phase=0,character=None):
        key=(kind,w,h,state,phase,character)
        if key in self.cache:return self.cache[key]
        t=self.theme
        s=pygame.Surface((w,h),pygame.SRCALPHA)
        accent,second,hazard=t['accent'],t['secondary'],t['hazard']
        ink=mix(t['background'],(0,0,0),.35)
        pale=t['foreground']
        cx=w//2
        if kind in ('wall','bars','spikes'):
            if kind=='wall':
                pygame.draw.rect(s,ink,(0,0,w,h))
                pygame.draw.rect(s,mix(t['panel'],second,.12),(1,1,w-2,h-2),border_radius=3)
                pygame.draw.line(s,mix(second,pale,.2),(2,2),(w-3,2),2)
                pygame.draw.line(s,mix(t['panel'],second,.3),(1,h-2),(w-2,h-2))
                if t.style=='cyberpunk':
                    pygame.draw.lines(s,mix(t['panel'],accent,.5),False,[(5,h-7),(14,h-7),(20,10),(w-7,10)],1)
                    pygame.draw.circle(s,accent,(w-7,10),2)
                else:
                    pygame.draw.line(s,mix(t['panel'],second,.25),(w//2,4),(w//2,h-4))
                    pygame.draw.circle(s,ink,(5,6),1)
                    pygame.draw.circle(s,ink,(w-6,h-7),1)
            elif kind=='bars':
                for x in range(3,w,10):
                    pygame.draw.rect(s,ink,(x,0,6,h))
                    pygame.draw.rect(s,second,(x+1,1,2,h-2))
                pygame.draw.line(s,second,(0,2),(w,2),3)
                pygame.draw.line(s,second,(0,h-3),(w,h-3),3)
            else:
                for x in range(0,w,10):
                    points=[(x,h-1),(x+5,max(0,h-22)),(x+10,h-1)]
                    pygame.draw.polygon(s,ink,points)
                    pygame.draw.polygon(s,hazard,[(x+2,h-2),(x+5,max(2,h-19)),(x+8,h-2)])
                    pygame.draw.line(s,pale,(x+5,max(2,h-19)),(x+6,h-9))
        elif kind=='player':
            # All styles share legacy physics dimensions. Only the drawing changes.
            bob=1 if state=='walking' and phase%2 else 0
            if state=='gone':return s
            if state in ('dying','exit'):
                alpha=max(40,255-phase*35)
            else:alpha=255
            dhh=character=='dhh'
            skin=(223,176,140);hair=(84,58,42)
            coat=second if dhh else accent
            step=(-2 if phase%2 else 2) if state=='walking' else 0
            head_y=max(1,h//7)+bob
            head=pygame.Rect(cx-8,head_y,16,15)
            pygame.draw.line(s,ink,(cx-5,h-12),(cx-6+step,h-2),5)
            pygame.draw.line(s,ink,(cx+5,h-12),(cx+6-step,h-2),5)
            pygame.draw.rect(s,coat,(cx-9,head_y+13,18,max(8,h-head_y-23)),border_radius=4)
            pygame.draw.line(s,mix(coat,pale,.3),(cx-2,head_y+15),(cx-2,h-13),2)
            pygame.draw.line(s,skin,(cx-10,head_y+16),(cx-12,head_y+24-step),3)
            pygame.draw.line(s,skin,(cx+10,head_y+16),(cx+12,head_y+24+step),3)
            pygame.draw.ellipse(s,skin,head)
            pygame.draw.arc(s,hair,head.inflate(1,1),0,math.pi,5)
            if dhh:
                pygame.draw.polygon(s,hair,[(cx-8,head_y+7),(cx-5,head_y+16),(cx+4,head_y+16),(cx+8,head_y+8),(cx+3,head_y+10),(cx-4,head_y+10)])
                pygame.draw.line(s,skin,(cx-2,head_y+11),(cx+3,head_y+11),2)
            else:
                pygame.draw.rect(s,accent,(cx-9,head_y,18,5),border_radius=2)
                pygame.draw.line(s,accent,(cx+4,head_y+4),(cx+11,head_y+4),2)
            pygame.draw.circle(s,ink,(cx+4,head_y+6),1)
            if t.style=='cyberpunk':pygame.draw.line(s,accent,(cx-4,head_y+6),(cx+7,head_y+6),2)
            s.set_alpha(alpha)
        elif kind=='spider':
            cy=h//2
            for side in (-1,1):
                for n in range(3):
                    yy=cy-6+n*6
                    pygame.draw.lines(s,second,False,[(cx+side*5,yy),(cx+side*(12+n%2*2),yy-4),(cx+side*(w//2-1),yy+3+phase%2)],2)
            pygame.draw.ellipse(s,ink,(cx-9,cy-10,18,21))
            pygame.draw.ellipse(s,mix(t['panel'],second,.4),(cx-7,cy-8,14,16))
            pygame.draw.circle(s,hazard,(cx-3,cy-3),2)
            pygame.draw.circle(s,hazard,(cx+3,cy-3),2)
            pygame.draw.rect(s,accent,(cx-3,cy+6,6,5),border_radius=2)
        elif kind=='projectile':
            cy=h//2
            pygame.draw.line(s,accent,(0,cy),(w-1,cy),max(3,h-2))
            pygame.draw.line(s,(245,255,255),(2,cy),(w-2,cy),max(1,h//3))
        elif kind=='blob':
            pygame.draw.ellipse(s,second,(1,h//4,w-2,h*3//4))
            pygame.draw.circle(s,pale,(w//3,h//2),3)
            pygame.draw.circle(s,pale,(w*2//3,h//2),3)
            pygame.draw.circle(s,ink,(w//3+1,h//2),1)
            pygame.draw.circle(s,ink,(w*2//3+1,h//2),1)
        elif kind=='lever':
            cy=h-5
            pygame.draw.rect(s,second,(2,cy,w-4,5),border_radius=2)
            end=(w-6,4) if state=='broken' else (6,4)
            pygame.draw.line(s,pale,(cx,cy),end,3)
            pygame.draw.circle(s,hazard if state=='broken' else accent,end,4)
        elif kind=='key':
            pygame.draw.circle(s,accent,(cx,h//3),max(3,w//3),3)
            pygame.draw.line(s,accent,(cx,h//3+4),(cx,h-3),3)
            pygame.draw.line(s,accent,(cx,h-4),(w-2,h-4),3)
            pygame.draw.line(s,accent,(cx,h-8),(w-4,h-8),2)
        elif kind=='other_pants':
            pygame.draw.polygon(s,accent,[(2,2),(w-2,2),(w-2,h-1),(cx+2,h-1),(cx,h//2),(cx-2,h-1),(2,h-1)])
        elif kind=='cake':
            pygame.draw.rect(s,accent,(2,h//3,w-4,h*2//3),border_radius=2)
            pygame.draw.line(s,pale,(2,h//3),(w-2,h//3),4)
            pygame.draw.line(s,second,(cx,0),(cx,h//3),2)
        else:
            pygame.draw.polygon(s,accent,[(cx,0),(w-2,h//2),(cx,h-1),(2,h//2)])
            pygame.draw.line(s,pale,(cx,2),(cx,h-3),2)
        if len(self.cache)>512:self.cache.clear()
        self.cache[key]=s
        return s
    def draw(self,session,theme,settings,alpha=1.,preview=False):
        self.configure(theme,settings)
        scene=session.scene
        level=scene['level']
        original=theme.style=='original'
        if original:
            bg=level.bg_animations[level.current_animation].image
            self.world.blit(bg,(0,0))
        else:self.world.blit(self.background,(0,0))
        objects=(*level.tiles,*scene['objects'])
        for o in objects:
            x,y=session.position(o,alpha)
            if x < -60 or y < -80 or x>580 or y>580:continue
            kind=getattr(o,'tileclass',o.itemclass)
            character=settings['character'] if settings['character']!='theme' else theme.character
            use_original=original or (kind=='player' and character=='original')
            # A chosen non-original character can be used inside the Original world.
            if kind=='player' and settings['character'] not in ('theme','original'):use_original=False
            if use_original:
                im=o.image
            else:
                state=o.current_animation
                phase=o.animations[state].i
                im=self.sprite(kind,o.rect.width,o.rect.height,state,phase,character)
            orientation=o.get_orientation()
            if orientation==2:im=pygame.transform.flip(im,True,False)
            elif orientation==3:im=pygame.transform.rotate(im,90)
            elif orientation==1:im=pygame.transform.rotate(im,-90)
            rect=im.get_rect(center=(round(x),round(y)))
            if kind=='projectile' and not original and settings['effects']:
                dx,dy=getattr(o,'dx',0),getattr(o,'dy',0)
                if dx or dy:
                    norm=max(1,math.hypot(dx,dy))
                    end=(x-dx/norm*20,y-dy/norm*20)
                    pygame.draw.line(self.world,mix(theme['background'],theme['accent'],.35),(x,y),end,6)
                    pygame.draw.line(self.world,theme['accent'],(x,y),end,2)
            self.world.blit(im,rect)
            if kind=='player' and y<0:
                pygame.draw.polygon(self.world,theme['accent'],[(x,3),(x-5,12),(x+5,12)])
        if settings['effects']:
            for p in scene['particles']:
                x,y=session.position(p,alpha)
                pygame.draw.circle(self.world,p.color if original else theme['accent'],(round(x),round(y)),max(0,int(p.radius)))
        if scene['fade'] and not preview:
            overlay=pygame.Surface((520,520));overlay.set_alpha(scene['fade']);self.world.blit(overlay,(0,0))
        return self.world
