"""Presentation-only motion events. No simulation objects, clocks or RNG are modified."""
from dataclasses import dataclass,field

@dataclass
class Motion:
    grounded: bool | None = None
    life: int | None = None
    dy: float = 0.
    takeoff: int = -1000
    landing: int = -1000
    hit: int = -1000
    landing_speed: float = 0.
    pickup_tick: int = -1000
    pickup_pos: tuple = (0.,0.)
    inventory_count: int = 0
    levers: dict = field(default_factory=dict)

    def observe(self, scene, tick):
        player=scene['player']
        for item in scene['objects']:
            if item.itemclass!='lever':continue
            count=item.activated_times
            previous,changed=self.levers.get(id(item),(count,-1000))
            self.levers[id(item)]=(count,tick if count!=previous else changed)
        if self.grounded is not None and not player.flipping and not scene['level'].flipping:
            if self.grounded and not player.on_ground and player.dy < -1:
                self.takeoff=tick
            if not self.grounded and player.on_ground and self.dy > 1:
                self.landing=tick
                self.landing_speed=self.dy
        if self.life is not None and player.life < self.life:self.hit=tick
        if len(player.inventory)>self.inventory_count:
            self.pickup_tick=tick
            item=player.inventory[-1];self.pickup_pos=(item.x,item.y)
        self.inventory_count=len(player.inventory)
        self.grounded=player.on_ground
        self.life=player.life
        self.dy=player.dy

    def pose(self, player, tick, inputs):
        state=player.current_animation
        if state in ('gone','dying','exit'):return state,0
        if tick-self.hit<8:return 'hurt',max(0,tick-self.hit)
        if not player.flipping:
            if not player.on_ground:
                if tick-self.takeoff<3:return 'takeoff',max(0,tick-self.takeoff)
                if player.dy < -2:return 'rising',0
                if abs(player.dy)<=2:return 'apex',0
                return ('gliding' if inputs.get('UP') else 'falling'),0
            land_age=tick-self.landing
            if land_age<6 and (abs(player.dx)<1 or land_age<3):return 'landing',max(0,land_age)
        return ('walking' if abs(player.dx)>.1 else 'default'),0
