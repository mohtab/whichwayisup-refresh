#!/usr/bin/env python3
"""Deterministic per-tick audit including RNG, bodies, animation and score."""
import os,sys,json,pathlib,hashlib,tempfile,argparse
ROOT=pathlib.Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT));os.environ.update(SDL_VIDEODRIVER='dummy',SDL_AUDIODRIVER='dummy',PYGAME_HIDE_SUPPORT_PROMPT='1')
import pygame
from refresh.runtime import Session
from refresh.storage import DEFAULTS
p=argparse.ArgumentParser();p.add_argument('--out',required=True);a=p.parse_args();pygame.init();pygame.display.set_mode((1,1))
fields=('x','y','dx','dy','life','current_animation','dead','flipping','flipcounter','flip_direction','on_ground','active','attached','fire_delay','tilex','tiley','orientation','activated_times')
def snapshot(s):
 def body(o):
  d={k:getattr(o,k) for k in fields if hasattr(o,k)}
  d['rect']=list(o.rect) if hasattr(o,'rect') else None
  d['animations']={k:(v.i,v.finished) for k,v in getattr(o,'animations',{}).items()}
  return d
 state=dict(tick=s.tick,result=s.result,score=vars(s.score),rng=s.random_state,fade=s.fade,level=(s.scene['level'].flipping,s.scene['level'].flipcounter,s.scene['level'].orientation),entities=[body(o) for o in s.entities()],inventory=[o.itemclass for o in s.scene['player'].inventory])
 return hashlib.sha256(json.dumps(state,sort_keys=True).encode()).hexdigest()
with tempfile.TemporaryDirectory(prefix='trace-') as profile:
 os.environ['WWISUP_USER_DIR']=profile;output={}
 for path in sorted((ROOT/'docs/campaign-acceptance/replays').glob('*.json')):
  payload=json.loads(path.read_text());s=Session(str(ROOT/'data/levels'/path.stem),dict(DEFAULTS,sound=False,dialogue=payload['dialogue']),seed=payload['seed']);states=[snapshot(s)]
  for command in payload['inputs']:s.step(command);states.append(snapshot(s))
  output[path.stem]=dict(states=states,result=s.result,ticks=s.score.time)
 pathlib.Path(a.out).write_text(json.dumps(output));print({k:(v['result'],v['ticks'],len(v['states'])) for k,v in output.items()})
