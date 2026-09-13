"""Palette-driven world art and illustrated sprites; original art remains optional."""
import math
import pygame
from . import sprites,lighting


def mix(a,b,t):return tuple(round(x+(y-x)*t) for x,y in zip(a,b))

class Painter:
    def __init__(self):
        self.key=None;self.cache={}
        self.scale=2
        self.world=pygame.Surface((520*self.scale,520*self.scale))
        self.tile_shadow=pygame.Surface((40*self.scale,40*self.scale),pygame.SRCALPHA)
        self.tile_shadow.fill((0,0,0,75))
    def configure(self,theme,settings):
        key=(theme.id,tuple(theme.palette.items()),settings['character'],settings['effects'])
        if key!=self.key:
            self.key=key;self.cache.clear()
            self.theme=theme;self.settings=settings.copy()
            self.background=pygame.transform.scale(self.make_background(),self.world.get_size())
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
    def sprite(self,kind,w,h,state='default',phase=0,character=None,scale=1):
        if kind=='player':return sprites.player(w,h,state,phase,scale,character)
        if kind=='spider':return sprites.spider(w,h,state,phase,scale)
        if kind=='key':return sprites.key(w,h,phase,scale)
        if kind in ('wall','spikes','lever','projectile'):return sprites.prop(kind,w,h,state,phase,scale)
        if scale!=1:return pygame.transform.scale(self.sprite(kind,w,h,state,phase,character),(w*scale,h*scale))
        key=(kind,w,h,state,phase,character)
        if key in self.cache:return self.cache[key]
        t=self.theme
        s=pygame.Surface((w,h),pygame.SRCALPHA)
        accent,second,hazard=t['accent'],t['secondary'],t['hazard']
        ink=mix(t['background'],(0,0,0),.35)
        pale=t['foreground']
        cx=w//2
        if kind=='bars':
            for x in range(3,w,10):
                pygame.draw.rect(s,ink,(x,0,6,h))
                pygame.draw.rect(s,second,(x+1,1,2,h-2))
            pygame.draw.line(s,second,(0,2),(w,2),3)
            pygame.draw.line(s,second,(0,h-3),(w,h-3),3)
        elif kind=='blob':
            squash=round(math.sin(phase*math.tau/16)*2)
            pygame.draw.ellipse(s,second,(1,h//4+squash,w-2,max(4,h*3//4-squash)))
            pygame.draw.circle(s,pale,(w//3,h//2),3)
            pygame.draw.circle(s,pale,(w*2//3,h//2),3)
            pygame.draw.circle(s,ink,(w//3+1,h//2),1)
            pygame.draw.circle(s,ink,(w*2//3+1,h//2),1)
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
        scale=self.scale
        level=scene['level']
        original=theme.style=='original'
        if original:
            bg=level.bg_animations[level.current_animation].image
            self.world.blit(pygame.transform.scale(bg,self.world.get_size()),(0,0))
        else:self.world.blit(self.background,(0,0))
        depth=settings.get('depth',True) and not original
        emitters=[session.position(o,alpha) for o in scene['objects'] if o.itemclass in ('key','projectile') or (o.itemclass=='lever' and o.current_animation!='broken')]
        if depth:
            # Cast platform shadows before any foreground geometry or hazards.
            for tile in level.tiles:
                if tile.tileclass!='wall':continue
                tx,ty=session.position(tile,alpha)
                if not (-60<tx<580 and -60<ty<580):continue
                self.world.blit(self.tile_shadow,((tx-17)*scale,(ty-15)*scale))
            for ex,ey in emitters:
                glow=lighting.halo(35*scale,theme['accent'])
                self.world.blit(glow,((ex-35)*scale,(ey-35)*scale))
        objects=(*level.tiles,*scene['objects'])
        for o in objects:
            x,y=session.position(o,alpha)
            if x < -60 or y < -80 or x>580 or y>580:continue
            x*=scale;y*=scale
            kind=getattr(o,'tileclass',o.itemclass)
            character=settings['character'] if settings['character']!='theme' else theme.character
            use_original=original or (kind=='player' and character=='original')
            # A chosen non-original character can be used inside the Original world.
            if kind=='player' and settings['character'] not in ('theme','original'):use_original=False
            if use_original:
                im=pygame.transform.scale(o.image,(o.image.get_width()*scale,o.image.get_height()*scale))
            else:
                state=o.current_animation
                phase=o.animations[state].i
                if kind in ('player','spider','blob','key') and state not in ('dying','exit','gone'):
                    phase=int((max(0,session.tick-1)+alpha)*1.5)%16
                if kind=='wall':phase=(o.tilex*7+o.tiley*11)%6
                if kind=='spikes':phase=int((session.tick+alpha)/5)%6
                if kind=='projectile':phase=int(session.tick+alpha)%6
                if kind=='lever':
                    age=session.tick-session.motion.levers.get(id(o),(0,-1000))[1]
                    phase=min(4,max(0,age)) if age<5 else min(4,getattr(o,'activated_times',0)*4)
                    if age<5:state='default'
                if kind=='player':
                    state,age=session.motion.pose(o,session.tick,session.driver.inputs)
                    if state in ('hurt','landing','takeoff'):phase=min(15,int(age))
                if kind=='spider':
                    delay=getattr(o,'fire_delay',0)
                    if delay>=25:state='firing';phase=30-delay
                    elif 0<delay<4 and o.current_animation!='walking':state='charged'
                im=self.sprite(kind,o.rect.width,o.rect.height,state,phase,character,scale)
            if depth and not use_original and kind not in ('projectile','key'):
                im=lighting.shade(im,lighting.proximity(x/scale,y/scale,emitters) if kind in ('player','spider') else 0)
            orientation=o.get_orientation()
            if kind=='spider' and not use_original:
                im=sprites.orient_spider(im,orientation,o.flipcounter,o.flipping,o.flip_direction,alpha)
                # Follow the actual solid face; bevels and transparent padding must not create a gap.
                angle=math.radians(sprites.spider_angle(orientation,o.flipcounter,o.flipping,o.flip_direction,alpha))
                gap=sprites.support_gap(o,level.tiles)
                x+=math.sin(angle)*gap*scale;y+=math.cos(angle)*gap*scale
            elif kind=='projectile' and not use_original:
                dx,dy=getattr(o,'dx',0),getattr(o,'dy',0)
                if dx or dy:im=pygame.transform.rotate(im,-math.degrees(math.atan2(dy,dx)))
                if o.current_animation=='dying':
                    im=im.copy();im.set_alpha(max(0,255-o.animations['dying'].i*40))
            else:
                if orientation==2:im=pygame.transform.flip(im,True,False)
                elif orientation==3:im=pygame.transform.rotate(im,90)
                elif orientation==1:im=pygame.transform.rotate(im,-90)
            if kind=='player' and not use_original:
                rect=im.get_rect(midbottom=(round(x),round(y+(o.rect.height/2+1)*scale)))
                hit_age=session.tick-session.motion.hit
                if 0<=hit_age<2:
                    im=im.copy()
                    flash=pygame.Surface(im.get_size(),pygame.SRCALPHA);flash.fill((120,75,55,0))
                    im.blit(flash,(0,0),special_flags=pygame.BLEND_RGB_ADD)
                if state in ('dying','exit'):
                    im=im.copy();im.set_alpha(max(0,255-o.animations[o.current_animation].i*32))
            else:
                if kind=='key' and not original and settings['effects']:y+=math.sin((session.tick+alpha)/8)*1.5*scale
                rect=im.get_rect(center=(round(x),round(y)))
            if kind=='projectile' and not original and settings['effects']:
                dx,dy=getattr(o,'dx',0),getattr(o,'dy',0)
                if dx or dy:
                    norm=max(1,math.hypot(dx,dy))
                    end=(x-dx/norm*20*scale,y-dy/norm*20*scale)
                    pygame.draw.line(self.world,mix(theme['background'],theme['accent'],.35),(x,y),end,6*scale)
                    pygame.draw.line(self.world,theme['accent'],(x,y),end,2*scale)
            if depth and not use_original and kind in ('player','spider','lever'):
                self.world.blit(lighting.shadow(im),rect.move(2*scale,2*scale))
            self.world.blit(im,rect)
            if kind=='player' and y<0:
                pygame.draw.polygon(self.world,theme['accent'],[(x,3*scale),(x-5*scale,12*scale),(x+5*scale,12*scale)])
        if settings['effects']:
            for p in scene['particles']:
                x,y=session.position(p,alpha)
                pygame.draw.circle(self.world,p.color if original else theme['accent'],(round(x*scale),round(y*scale)),max(0,int(p.radius*scale)))
        if settings['effects'] and not original:
            player=scene['player'];px,py=session.position(player,alpha)
            age=session.tick-session.motion.landing+alpha
            if 0<=age<7 and not player.flipping:
                # Short ground-level dust wisps, without displacing the camera/world.
                dust=pygame.Surface((72,22),pygame.SRCALPHA)
                opacity=round(145*(1-age/7))
                for side in (-1,1):
                    for n in range(3):
                        dx=side*(6+age*(2+n*.5));dy=-age*(.45+n*.18)
                        pygame.draw.ellipse(dust,(*theme['secondary'],opacity),(36+dx,15+dy,8-age*.65,3))
                self.world.blit(pygame.transform.scale(dust,(72*scale,22*scale)),((round(px)-36)*scale,(round(py+player.rect.height/2)-15)*scale))
            hit_age=session.tick-session.motion.hit+alpha
            if 0<=hit_age<4:
                impact=pygame.Surface((80,80),pygame.SRCALPHA)
                for n in range(7):
                    angle=n*math.tau/7
                    start=16+hit_age*3;end=start+6*(1-hit_age/4)
                    pygame.draw.line(impact,(*theme['hazard'],round(210*(1-hit_age/4))),
                                     (40+math.cos(angle)*start,40+math.sin(angle)*start),
                                     (40+math.cos(angle)*end,40+math.sin(angle)*end),2)
                self.world.blit(pygame.transform.scale(impact,(80*scale,80*scale)),((round(px)-40)*scale,(round(py)-40)*scale))
            pickup_age=session.tick-session.motion.pickup_tick+alpha
            if 0<=pickup_age<10:
                gleam=pygame.Surface((80,80),pygame.SRCALPHA)
                radius=8+pickup_age*2
                for n in range(6):
                    angle=n*math.tau/6
                    cx=40+math.cos(angle)*radius;cy=40+math.sin(angle)*radius
                    length=max(1,4-pickup_age*.3)
                    rgba=(*theme['accent'],round(230*(1-pickup_age/10)))
                    pygame.draw.line(gleam,rgba,(cx-length,cy),(cx+length,cy),1)
                    pygame.draw.line(gleam,rgba,(cx,cy-length),(cx,cy+length),1)
                qx,qy=session.motion.pickup_pos
                self.world.blit(pygame.transform.scale(gleam,(80*scale,80*scale)),((round(qx)-40)*scale,(round(qy)-40)*scale))
        if scene['fade'] and not preview:
            overlay=pygame.Surface(self.world.get_size());overlay.set_alpha(scene['fade']);self.world.blit(overlay,(0,0))
        return self.world
