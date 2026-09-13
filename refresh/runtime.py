"""Fixed simulation steps, independent of presentation rate."""
from dataclasses import dataclass, field
from pathlib import Path
import sys
import random
import pygame

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'lib'))
import game
from util import Score
from variables import Variables

@dataclass
class Driver:
    inputs: dict = field(default_factory=dict)
    events: list = field(default_factory=list)

class Stepper:
    def __init__(self):
        self.accumulator=0.
        self.overrun=False
    def advance(self, seconds, tempo=1.):
        if seconds>.25:
            self.accumulator=0.
            self.overrun=True
            return 0
        self.accumulator+=max(0.,seconds)*tempo
        ticks=min(8,int((self.accumulator+1e-10)*24))
        self.accumulator-=ticks/24
        return ticks
    @property
    def alpha(self): return min(1., max(0.,self.accumulator*24))
    def reset(self): self.accumulator=0.; self.overrun=False

class Session:
    def __init__(self, stage, settings, seed=0):
        Variables.vdict.update(devmode=False, verbose=False, sound=settings['sound'],
                               dialogue=settings['dialogue'], fullscreen=False)
        self.canvas=pygame.Surface((520,520)).convert()
        self.driver=Driver()
        self.score=Score(0)
        self.stage=stage
        self.seed=seed
        self.tick=0
        self.result=None
        self.previous={}
        self.history=[]
        self.random_state=random.Random(seed).getstate()
        self.simulation=game.steps(self.canvas,stage,score=self.score,driver=self.driver)
        self.scene=None
        self.step({})
        self.history.clear()
        self.tick=0
    def step(self,inputs):
        if self.result is not None:return
        self.previous={id(o):(o.x,o.y) for o in self.entities()}
        self.driver.inputs=dict(inputs)
        outside=random.getstate()
        random.setstate(self.random_state)
        try:
            self.scene=next(self.simulation)
        except StopIteration as stopped:
            self.result=stopped.value
        finally:
            self.random_state=random.getstate()
            random.setstate(outside)
        if len(self.history) < 86400:
            self.history.append({k:v for k,v in inputs.items() if v})
        else:
            self.history_truncated = True
        self.tick+=1
    def entities(self):
        if self.scene is None:return ()
        return (*self.scene['level'].tiles,*self.scene['objects'],*self.scene['particles'])
    def position(self,o,alpha):
        x,y=self.previous.get(id(o),(o.x,o.y))
        return (x+(o.x-x)*alpha,y+(o.y-y)*alpha)
