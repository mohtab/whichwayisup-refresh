#!/usr/bin/env python3
import argparse,hashlib,json,os,pathlib,sys,tempfile
BASE=pathlib.Path(__file__).resolve().parents[2];sys.path.insert(0,str(BASE/'game'))
os.environ.update(SDL_VIDEODRIVER='dummy',SDL_AUDIODRIVER='dummy',PYGAME_HIDE_SUPPORT_PROMPT='1')
import pygame
from refresh.app import App
with tempfile.TemporaryDirectory(prefix='wwiup-contract-') as profile:
 os.environ['WWISUP_USER_DIR']=profile
 a=App(argparse.Namespace(theme='refresh',safe_window=True,play=True,stage=None,screen=None,smoke=None,screenshot=None));a.s['dialogue']=False;a.start_stage(a.catalog.stages[0])
 for _ in range(70):a.update(1/24)
 def state():
  s=a.session
  return hashlib.sha256(repr((s.tick,s.result,s.score.time,s.random_state,s.history,[(type(o).__name__,o.x,o.y,o.current_animation,o.get_orientation()) for o in s.entities()])).encode()).hexdigest()
 initial=state();rows=[]
 for theme,depth in [('refresh',True),('refresh',False),('cyberpunk',True),('original',False),('refresh',True)]:
  a.set_theme(theme);a.s['depth']=depth;a.draw();digest=state();assert digest==initial
  rows.append(dict(theme=theme,depth=depth,simulation_hash=digest,display_hash=hashlib.sha256(pygame.image.tobytes(a.display.screen,'RGB')).hexdigest()))
 assert len({r['display_hash'] for r in rows})>=4
 (BASE/'artifacts/stage-b/renderer-contract.json').write_text(json.dumps({'method':'Fixed live session; switch themed material/sprite family and software depth/light flag, draw through App without simulation update; hash tick/result/time/RNG/history/entity positions/states/orientations before and after.','samples':rows},indent=2)+'\n')
 pygame.quit();print('Renderer swaps preserve simulation state; four distinct rendered hashes.')
