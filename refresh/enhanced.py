"""Opt-in connected geometry and finite continuous projectile contacts.

No global overrides: one rules object belongs to one generator/session. Ordinary
body movement, input, room timing and endpoint tile coordinates remain inherited.
"""
import math
from object import DynamicObject

PIVOT=(120.,120.)
BODY=(20.,8.)

def lerp(a,b,t):return tuple(x+(y-x)*t for x,y in zip(a,b))
def matrix(angle):return math.cos(angle),math.sin(angle)
def transform(p,m):
    c,s=m;x,y=p[0]-120,p[1]-120
    return 120+c*x-s*y,120+s*x+c*y

def corners(x,y,w,h,m=(1.,0.)):
    c,s=m
    return tuple((x+c*dx-s*dy,y+s*dx+c*dy) for dx,dy in ((-w/2,-h/2),(w/2,-h/2),(w/2,h/2),(-w/2,h/2)))

def axes(poly):
    for a,b in zip(poly,poly[1:]+poly[:1]):
        x,y=b[0]-a[0],b[1]-a[1];n=math.hypot(x,y)
        if n>1e-12:yield -y/n,x/n

def separation(a,b):
    gap=-math.inf;normal=(1.,0.)
    for nx,ny in (*axes(a),*axes(b)):
        aa=[x*nx+y*ny for x,y in a];bb=[x*nx+y*ny for x,y in b]
        left,right=min(bb)-max(aa),min(aa)-max(bb)
        if left>gap:gap=left;normal=(-nx,-ny)
        if right>gap:gap=right;normal=(nx,ny)
    return max(0.,gap),normal

def closest(point,poly):
    best=None;distance=math.inf
    for a,b in zip(poly,poly[1:]+poly[:1]):
        dx,dy=b[0]-a[0],b[1]-a[1];den=dx*dx+dy*dy
        t=max(0.,min(1.,((point[0]-a[0])*dx+(point[1]-a[1])*dy)/den)) if den else 0
        q=(a[0]+dx*t,a[1]+dy*t);d=math.dist(point,q)
        if d<distance:distance=d;best=q
    return best

def ray_contact(origin,direction,polygons,minimum=0.,maximum=math.inf):
    hits=[];dx,dy=direction
    for poly in polygons:
        for a,b in zip(poly,poly[1:]+poly[:1]):
            ex,ey=b[0]-a[0],b[1]-a[1];den=dx*ey-dy*ex
            if abs(den)<1e-10:continue
            ax,ay=a[0]-origin[0],a[1]-origin[1]
            t=(ax*ey-ay*ex)/den;u=(ax*dy-ay*dx)/den
            if minimum<=t<=maximum and 0<=u<=1:hits.append(t)
    return min(hits) if hits else None

def bounds(polys):
    points=[p for poly in polys for p in poly]
    return min(p[0] for p in points),min(p[1] for p in points),max(p[0] for p in points),max(p[1] for p in points)

def roots(a,b,c):
    if abs(a)<1e-12:
        return (-c/b,) if abs(b)>1e-12 else ()
    discriminant=b*b-4*a*c
    if discriminant<0:return ()
    q=-.5*(b+math.copysign(math.sqrt(max(0.,discriminant)),b))
    return (q/a,c/q) if abs(q)>1e-15 else (-b/(2*a),)

def contact_point(a,b):
    pairs=[(p,closest(p,b)) for p in a]+[(closest(p,a),p) for p in b]
    distance=min(math.dist(p,q) for p,q in pairs)
    near=[lerp(p,q,.5) for p,q in pairs if math.dist(p,q)<=distance+1e-5]
    return tuple(sum(p[i] for p in near)/len(near) for i in (0,1))

def sweep(a0,a1,b0,b1):
    """Exact event times for convex polygons with linearly moving vertices.

First contact occurs when a vertex meets an edge (or initial overlap). Each
moving vertex/edge collinearity equation is quadratic. Enumerating its roots
and verifying SAT overlap avoids stepping, tunneling, or iteration cutoffs.
This matches the same affine interpolation used for visible turning corners.
    """
    ax,ay,ar,ab=bounds((a0,a1));bx,by,br,bb=bounds((b0,b1))
    if ar<bx or br<ax or ab<by or bb<ay:return None
    def cross(a,b):return a[0]*b[1]-a[1]*b[0]
    def sub(a,b):return a[0]-b[0],a[1]-b[1]
    times={0.,1.}
    for v0,v1,e0,e1 in ((a0,a1,b0,b1),(b0,b1,a0,a1)):
        for p0,p1 in zip(v0,v1):
            for i in range(len(e0)):
                j=(i+1)%len(e0)
                q0=sub(p0,e0[i]);q1=sub(sub(p1,e1[i]),q0)
                r0=sub(e0[j],e0[i]);r1=sub(sub(e1[j],e1[i]),r0)
                aa=cross(q1,r1);bb=cross(q0,r1)+cross(q1,r0);cc=cross(q0,r0)
                candidates=roots(aa,bb,cc)
                if max(abs(aa),abs(bb),abs(cc))<1e-10:
                    # Persistent collinearity: endpoints can meet along the line.
                    for k in (i,j):
                        d0=sub(p0,e0[k]);d1=sub(sub(p1,e1[k]),d0)
                        candidates+=tuple(-d0[n]/d1[n] for n in (0,1) if abs(d1[n])>1e-12)
                times.update(max(0.,min(1.,t)) for t in candidates if -1e-10<=t<=1+1e-10)
    for t in sorted(times):
        a=tuple(lerp(x,y,t) for x,y in zip(a0,a1));b=tuple(lerp(x,y,t) for x,y in zip(b0,b1))
        gap,normal=separation(a,b)
        if gap<=1e-6:return t,contact_point(a,b),normal
    return None

class EnhancedRules:
    def bind(self,level,player):
        self.tick=0
        self.level=level;self.player=player;self.base={};self.previous_matrix=self.current_matrix=(1.,0.)
        self.previous_polygons={};self.polygons={};self.player_previous=(player.x,player.y)
        self.after_terrain();self.previous_polygons=self.polygons.copy()
    def before_tick(self):
        self.tick+=1
        self.previous_matrix=self.current_matrix
        self.previous_polygons=self.polygons.copy()
        self.player_previous=(self.player.x,self.player.y)
    def after_terrain(self):
        level=self.level;angle=level.orientation*math.pi/2
        if level.flipping and level.tiles:
            direction=level.tiles[0].flip_direction
            angle-=direction*(31-level.flipcounter)*math.pi/62
        self.current_matrix=matrix(angle)
        alive={id(t) for t in level.tiles}
        self.base={k:v for k,v in self.base.items() if k in alive}
        self.polygons={}
        for tile in level.tiles:
            key=id(tile)
            if key not in self.base:
                self.base[key]=tuple(transform(p,(self.current_matrix[0],-self.current_matrix[1])) for p in corners(tile.x,tile.y,tile.rect.w,tile.rect.h))
            if tile.tileclass=='spikes':
                # Gravity-facing hazards keep endpoint footprint and upright art.
                self.polygons[key]=corners(tile.x,tile.y,tile.rect.w,tile.rect.h)
            else:self.polygons[key]=tuple(transform(p,self.current_matrix) for p in self.base[key])
    def geometry(self,tile,alpha=1.):
        key=id(tile);end=self.polygons[key];start=self.previous_polygons.get(key,end)
        return tuple(lerp(a,b,alpha) for a,b in zip(start,end))
    def material_matrix(self,alpha):return lerp(self.previous_matrix,self.current_matrix,alpha)
    def update_projectile(self,o):
        if o.current_animation!='default':
            # Retain death-animation timing, but a spent shot stays at its contact.
            from visibleobject import VisibleObject
            o.flipping=False;VisibleObject.update(o);o.dx=o.dy=0
            return None
        start=(o.x,o.y);velocity=(o.dx,o.dy)
        DynamicObject.update(o,self.level)
        if o.dx==0 and o.dy==0 and o.saveddx is not None:
            o.dx,o.dy=o.saveddx,o.saveddy;o.saveddx=None
        end=(o.x,o.y)
        direction=(o.dx,o.dy) if o.dx or o.dy else velocity
        angle=math.atan2(direction[1],direction[0])
        previous_angle=getattr(o,'body_angle',angle)
        c0,s0=self.previous_matrix;c1,s1=self.current_matrix
        delta=math.atan2(c0*s1-s0*c1,c0*c1+s0*s1)
        if abs(delta)>1e-10:angle=previous_angle+delta
        o.body_angle=angle;o.body_previous=matrix(previous_angle);o.body_current=matrix(angle)
        a0=corners(*start,*BODY,o.body_previous);a1=corners(*end,*BODY,o.body_current)
        hits=[]
        for tile in self.level.tiles:
            key=id(tile);b1=self.polygons[key];b0=self.previous_polygons.get(key,b1)
            hit=sweep(a0,a1,b0,b1)
            if hit is not None:hits.append((*hit,'wall'))
        # Preserve a finite playfield, testing edges as surfaces, not center limits.
        for b in (corners(-1000,260,2000,3000),corners(1520,260,2000,3000),corners(260,-1000,1040,2000),corners(260,1520,1040,2000)):
            hit=sweep(a0,a1,b,b)
            if hit is not None:hits.append((*hit,'wall'))
        p=self.player
        b0=corners(*self.player_previous,p.rect.w,p.rect.h);b1=corners(p.x,p.y,p.rect.w,p.rect.h)
        hit=sweep(a0,a1,b0,b1)
        if hit is not None:hits.append((*hit,'player'))
        if not hits:return None
        time,point,normal,target=min(hits,key=lambda h:(round(h[0],8),h[3]!='wall'))
        o.x,o.y=lerp(start,end,time);o.impact_point=point;o.impact_normal=normal;o.impact_fraction=time;o.impact_rule_tick=self.tick
        o.die();o.dx=o.dy=0;o.saveddx=None;o.flipping=False
        return p.take_damage(o.damage,*point) if target=='player' else None
