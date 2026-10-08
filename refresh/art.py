"""Palette-driven world art and illustrated sprites; original art remains optional."""
import math
import pygame
from . import sprites,lighting,branding,chamber,objects


def mix(a,b,t):return tuple(round(x+(y-x)*t) for x,y in zip(a,b))

class Painter:
    def __init__(self):
        self.key=None;self.cache={};self.terrain_key=None;self.terrain_lit_key=None
        self.scale=2
        self.world=pygame.Surface((520*self.scale,520*self.scale))
        self.tile_shadow=pygame.Surface((40*self.scale,40*self.scale),pygame.SRCALPHA)
        self.tile_shadow.fill((0,0,0,75))
    def configure(self,theme,settings):
        key=(theme.id,tuple(theme.palette.items()),settings['character'],settings['effects'])
        if key!=self.key:
            self.key=key;self.cache.clear();self.terrain_key=None;self.terrain_lit_key=None
            self.theme=theme;self.settings=settings.copy()
            if theme.style=="refresh":objects.terrain_sampler.kernel()
            self.background=pygame.transform.scale(self.make_background(),self.world.get_size())
    def make_background(self):
        t=self.theme
        if t.style=='refresh':return chamber.background()
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
        style=self.theme.style
        if style=='refresh' and kind in ('blob','other_pants','power_crystal','cake'):
            return objects.sprite(kind,w,h,state,phase,scale)
        if kind=='player':return sprites.player(w,h,state,phase,scale,character,style)
        if kind=='spider':
            image=sprites.spider(w,h,state,phase,scale,style)
            return lighting.hazard_chitin(image) if style=='refresh' else image
        if kind=='key' and style=='omarchy':return branding.collectible(w,h,phase,scale,self.settings['effects'])
        if style=='cyberpunk' and kind in ('key','bars','blob','other_pants','cake'):
            return sprites.prop(kind,w,h,state,phase,scale,style)
        if kind=='key':return sprites.key(w,h,phase,scale)
        if kind=='wall' and style=='refresh':return objects.wall(w,h,phase,scale)
        if kind in ('wall','spikes','lever','projectile'):
            image=sprites.prop(kind,w,h,state,phase,scale,style)
            return lighting.quiet_wall(image,self.theme['panel'],scale) if kind=='wall' and style not in ('original','refresh') else image
        if scale!=1:return pygame.transform.scale(self.sprite(kind,w,h,state,phase,character),(w*scale,h*scale))
        key=(kind,w,h,state,phase,character)
        if key in self.cache:return self.cache[key]
        t=self.theme
        s=pygame.Surface((w,h),pygame.SRCALPHA)
        accent,second,hazard=t['accent'],t['secondary'],t['hazard']
        ink=mix(t['background'],(0,0,0),.35)
        pale=t['foreground']
        cx=w//2
        if kind=='bars' and style=='refresh':
            # Aged brass faces, cool shaded return, worn rim and recessed joints.
            for x in range(3,w,10):
                pygame.draw.rect(s,(15,25,28),(x,0,6,h))
                pygame.draw.rect(s,(96,98,68),(x+1,1,3,h-2))
                pygame.draw.line(s,(185,160,98),(x+1,2),(x+1,h-3))
                pygame.draw.line(s,(43,57,54),(x+4,2),(x+4,h-3))
                for yy in range(8,h-5,13):pygame.draw.line(s,(64,73,58),(x+2,yy),(x+3,yy+2))
            for yy in (1,h-5):
                pygame.draw.rect(s,(21,31,32),(0,yy,w,5))
                pygame.draw.line(s,(177,151,89),(0,yy),(w,yy))
                pygame.draw.line(s,(103,103,68),(0,yy+1),(w,yy+1))
                pygame.draw.line(s,(51,64,55),(0,yy+3),(w,yy+3))
                for x in range(5,w,10):
                    pygame.draw.circle(s,(15,25,26),(x,yy+2),2)
                    s.set_at((min(w-1,x),min(h-1,yy+1)),(203,169,93))
        elif kind=='blob' and style=='refresh':
            squash=round(math.sin(phase*math.tau/16)*2)
            body=pygame.Rect(1,h//4+squash,w-2,max(4,h*3//4-squash))
            pygame.draw.ellipse(s,(17,40,44),body)
            # Layered translucent skin: broad matte body, cool lower shade.
            for inset in range(1,max(2,min(body.w,body.h)//2)):
                inner=body.inflate(-inset*2,-inset*2);inner.y-=inset//3
                c=mix((36,83,82),(101,155,125),inset/max(1,min(body.w,body.h)/2))
                if inner.w>0 and inner.h>0:pygame.draw.ellipse(s,c,inner)
            pygame.draw.arc(s,(166,190,144),body.inflate(-5,-4),.65,2.5,1)
            for x,yy in ((w//4,h*3//4),(w*3//4,h*4//5),(w//2,h*7//8)):
                pygame.draw.circle(s,(36,72,69),(x,min(h-2,yy)),1)
            for x in (w//3,w*2//3):
                pygame.draw.circle(s,(23,45,42),(x,h//2+1),4)
                pygame.draw.circle(s,(190,185,135),(x,h//2),3)
                pygame.draw.circle(s,(71,99,76),(x+1,h//2+1),2)
                pygame.draw.circle(s,(13,25,27),(x+1,h//2),1)
                s.set_at((x-1,h//2-1),(234,221,168))
        elif kind=='bars':
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
    def draw(self,session,theme,settings,alpha=1.,preview=False,*,resolved=False):
        self.configure(theme,settings)
        scene=session.scene
        scale=self.scale
        level=scene['level']
        original=theme.style=='original'
        enhanced=session.rules if not original else None
        geometry_cache={}
        def geometry(tile):
            key=id(tile)
            if key not in geometry_cache:geometry_cache[key]=enhanced.geometry(tile,alpha)
            return geometry_cache[key]
        if original:
            bg=level.bg_animations[level.current_animation].image
            self.world.blit(pygame.transform.scale(bg,self.world.get_size()),(0,0))
        else:self.world.blit(self.background,(0,0))
        depth=settings.get('depth',True) and not original
        emitters=[session.position(o,alpha) for o in scene['objects'] if o.itemclass in ('key','projectile') or (o.itemclass=='lever' and o.current_animation!='broken')]
        field=lighting.room_field(emitters,self.world.get_size()) if theme.style=='refresh' else None
        warm=lighting.warm_field(emitters,self.world.get_size()) if field is not None else None
        if field is not None:
            self.world.blit(field,(0,0),special_flags=pygame.BLEND_RGB_MULT)
            self.world.blit(chamber.lit_relief(self.world.get_size(),emitters),(0,0))
        if depth:
            # Cast platform shadows before any foreground geometry or hazards.
            for tile in level.tiles:
                if tile.tileclass!='wall' or theme.style=='refresh':continue
                tx,ty=session.position(tile,alpha)
                if not (-60<tx<580 and -60<ty<580):continue
                offset=(15,12) if theme.style=='refresh' else (17,15)
                self.world.blit(self.tile_shadow,((tx-offset[0])*scale,(ty-offset[1])*scale))
            for ex,ey in emitters:
                glow=lighting.halo(35*scale,theme['accent'])
                self.world.blit(glow,((ex-35)*scale,(ey-35)*scale))
        if field is not None:
            rectangles=[]
            for tile in level.tiles:
                if tile.tileclass!='wall':continue
                tx,ty=session.position(tile,alpha)
                rectangles.append((round((tx-tile.rect.width/2)*scale),round((ty-tile.rect.height/2)*scale),tile.rect.width*scale,tile.rect.height*scale))
            polygons=None;material=None
            if enhanced:
                polygons=tuple(tuple((x*scale,y*scale) for x,y in geometry(tile)) for tile in level.tiles if tile.tileclass=='wall')
                material=enhanced.material_matrix(alpha)
            signature=(polygons,material) if enhanced else tuple(rectangles)
            if signature!=self.terrain_key:
                terrain,shadow=objects.terrain_layer(() if enhanced else rectangles,self.world.get_size(),scale,polygons,material)
                terrain.blit(objects.stone_response(terrain.get_size()),(0,0),special_flags=pygame.BLEND_RGB_ADD)
                self.terrain=terrain
                self.terrain_shadow=shadow;self.terrain_key=signature;self.terrain_lit_key=None
            if depth:self.world.blit(self.terrain_shadow,(5*scale,8*scale))
            light_key=(signature,tuple((round(x,2),round(y,2)) for x,y in emitters))
            if light_key!=self.terrain_lit_key:
                self.terrain_lit=lighting.spatial_response(self.terrain,self.terrain.get_rect(),field,warm=warm)
                self.terrain_lit_key=light_key
            self.world.blit(self.terrain_lit,(0,0))
        # Foreground occlusion is derived from real solids, never the previous framebuffer.
        occlusion=pygame.Surface(self.world.get_size(),pygame.SRCALPHA)
        if not original:
            for tile in level.tiles:
                if tile.tileclass not in ('wall','bars'):continue
                if enhanced:pygame.draw.polygon(occlusion,(255,255,255,255),[(x*scale,y*scale) for x,y in geometry(tile)])
                else:
                    tx,ty=session.position(tile,alpha)
                    pygame.draw.rect(occlusion,(255,255,255,255),((tx-tile.rect.w/2)*scale,(ty-tile.rect.h/2)*scale,tile.rect.w*scale,tile.rect.h*scale))
        def occlude(image,rect):
            result=image.copy();cut=pygame.Surface(image.get_size(),pygame.SRCALPHA)
            cut.blit(occlusion,(-rect.x,-rect.y));result.blit(cut,(0,0),special_flags=pygame.BLEND_RGBA_SUB)
            return result
        lever_layers=[];spider_layers=[]
        render_objects=(*level.tiles,*scene['objects'])
        for o in render_objects:
            x,y=session.position(o,alpha)
            fresh_impact=enhanced and getattr(o,'impact_rule_tick',-1)==enhanced.tick
            before_impact=fresh_impact and alpha<o.impact_fraction
            if fresh_impact:
                start=session.previous.get(id(o),(o.x,o.y));fraction=min(1.,alpha/max(1e-10,o.impact_fraction))
                x=start[0]+(o.x-start[0])*fraction;y=start[1]+(o.y-start[1])*fraction
            if x < -60 or y < -80 or x>580 or y>580:continue
            x*=scale;y*=scale
            kind=getattr(o,'tileclass',o.itemclass)
            if field is not None and kind=='wall':continue
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
                if kind=='key' and theme.style=='omarchy':phase=int((max(0,session.tick-1)+alpha)*.7)%32
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
            if theme.style=='refresh' and not use_original:
                im=lighting.refresh_relief(im,0,kind=='wall',scale)
            if depth and theme.style!='refresh' and not use_original and kind not in ('projectile','key'):
                im=lighting.shade(im,lighting.proximity(x/scale,y/scale,emitters) if kind in ('player','spider') else 0)
            if not original and not use_original and kind in ('player','spider'):
                high_contrast=settings.get('high_contrast',False)
                edge=theme.readable(theme['panel']) if high_contrast else (24,10,30) if theme.style=='refresh' and kind=='spider' else mix(theme['background'],(0,0,0),.55)
                im=lighting.silhouette(im,edge,scale,high_contrast)
            if kind=='player' and not use_original and state in ('exit','dying'):
                # Terminal poses stay inside the original body; raised hands cannot punch through a low ceiling.
                bounds=im.get_bounding_rect();body=im.subsurface(bounds)
                factor=min(o.rect.w*scale/max(1,body.get_width()),o.rect.h*scale/max(1,body.get_height()))
                im=pygame.transform.smoothscale(body,(max(1,round(body.get_width()*factor)),max(1,round(body.get_height()*factor))))
            orientation=o.get_orientation()
            if kind=='spider' and not use_original:
                if enhanced:
                    from .enhanced import ray_contact
                    c,ss=enhanced.material_matrix(alpha)
                    relative=math.atan2(ss,c)-level.orientation*math.pi/2
                    relative=math.atan2(math.sin(relative),math.cos(relative))
                    angle=math.radians({0:90,1:0,2:-90,3:180}[orientation])-relative
                    im=pygame.transform.rotate(im,math.degrees(angle))
                    normal=(math.sin(angle),math.cos(angle));half=o.rect.h/2
                    distance=ray_contact((x/scale,y/scale),normal,[geometry(t) for t in level.tiles if t.tileclass in ('wall','bars')],half-4,half+12)
                    gap=distance-half+1 if distance is not None else 0
                else:
                    im=sprites.orient_spider(im,orientation,o.flipcounter,o.flipping,o.flip_direction,alpha)
                    angle=math.radians(sprites.spider_angle(orientation,o.flipcounter,o.flipping,o.flip_direction,alpha))
                    gap=sprites.support_gap(o,level.tiles)
                x+=math.sin(angle)*gap*scale;y+=math.cos(angle)*gap*scale
            elif kind=='projectile' and not use_original:
                if enhanced:im=pygame.transform.smoothscale(im,(20*scale,8*scale))
                if enhanced and hasattr(o,'body_angle'):
                    from .enhanced import lerp
                    dx,dy=lerp(o.body_previous,o.body_current,alpha)
                else:dx,dy=getattr(o,'dx',0),getattr(o,'dy',0)

                if dx or dy:
                    im=pygame.transform.rotozoom(im,-math.degrees(math.atan2(dy,dx)),math.hypot(dx,dy) if hasattr(o,'body_current') else 1.) if enhanced else pygame.transform.rotate(im,-math.degrees(math.atan2(dy,dx)))
                if o.current_animation=='dying' and not before_impact:
                    im=im.copy();im.set_alpha(max(0,255-o.animations['dying'].i*40))
            elif enhanced and kind in ('wall','bars'):
                c,ss=enhanced.material_matrix(alpha)
                im=pygame.transform.rotozoom(im,-math.degrees(math.atan2(ss,c)),math.hypot(c,ss))
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
            if enhanced and kind=='projectile' and o.current_animation=='dying' and not before_impact:
                age=o.animations['dying'].i
                im=pygame.Surface((32*scale,32*scale),pygame.SRCALPHA)
                if settings['effects']:
                    radius=(3+age*2)*scale
                    pygame.draw.circle(im,(*theme['accent'],max(0,220-age*65)),(16*scale,16*scale),min(14*scale,radius),max(1,scale))
                    pygame.draw.circle(im,(*theme['foreground'],max(0,220-age*70)),(16*scale,16*scale),max(1,3*scale-age*scale))
                qx,qy=getattr(o,'impact_point',(o.x,o.y));rect=im.get_rect(center=(round(qx*scale),round(qy*scale)))
            if enhanced and kind=='lever':
                from .enhanced import closest
                base=(x/scale,y/scale+o.rect.h/2-2)
                contacts=[closest(base,geometry(t)) for t in level.tiles if t.tileclass in ('wall','bars')]
                if contacts:
                    contact=min(contacts,key=lambda p:math.dist(base,p))
                    if math.dist(base,contact)<=30:
                        a=(round(base[0]*scale),round(base[1]*scale));b=(round(contact[0]*scale),round(contact[1]*scale))
                        pygame.draw.line(self.world,(39,38,29),a,b,5*scale)
                        pygame.draw.line(self.world,(163,135,76),a,b,2*scale)
                        pygame.draw.circle(self.world,(202,168,93),b,3*scale)
            if kind=='projectile' and not original and settings['effects'] and o.current_animation=='default':
                dx,dy=getattr(o,'dx',0),getattr(o,'dy',0)
                if dx or dy:
                    norm=max(1,math.hypot(dx,dy))
                    end=(x-dx/norm*20*scale,y-dy/norm*20*scale)
                    pygame.draw.line(self.world,mix(theme['background'],theme['accent'],.35),(x,y),end,6*scale)
                    pygame.draw.line(self.world,theme['accent'],(x,y),end,2*scale)
            if field is not None and not use_original:
                im=lighting.spatial_response(im,rect,field,kind in ('player','spider'),warm)
            if depth and not use_original and kind in ('player','spider','lever'):
                self.world.blit(lighting.shadow(im),rect.move(2*scale,2*scale))
            if not original and kind=='player' and state in ('exit','dying'):im=occlude(im,rect)
            self.world.blit(im,rect)
            if field is not None and kind=='lever':lever_layers.append((im,rect.copy()))
            if field is not None and kind=='spider':spider_layers.append((im,rect.copy()))
            if kind=='player' and y<0:
                pygame.draw.polygon(self.world,theme['accent'],[(x,3*scale),(x-5*scale,12*scale),(x+5*scale,12*scale)])
        for lever,lr in lever_layers:
            for spider,sr in spider_layers:objects.reveal_lever(self.world,lever,lr,spider,sr,scale)
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
                gleam=pygame.transform.scale(gleam,(80*scale,80*scale))
                rect=gleam.get_rect(topleft=((round(qx)-40)*scale,(round(qy)-40)*scale))
                self.world.blit(occlude(gleam,rect),rect)
        if scene['fade'] and not preview and not (resolved and theme.id=='refresh'):
            overlay=pygame.Surface(self.world.get_size());overlay.set_alpha(scene['fade']);self.world.blit(overlay,(0,0))
        return self.world
