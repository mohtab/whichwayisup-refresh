#!/usr/bin/env python3
"""Disclosed live-engine stress fixtures; supplements genuine campaign evidence."""
import os,sys,pathlib,argparse,tempfile,json,subprocess
ROOT=pathlib.Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT));os.environ.update(SDL_VIDEODRIVER='dummy',SDL_AUDIODRIVER='dummy',PYGAME_HIDE_SUPPORT_PROMPT='1')
import pygame
from refresh.app import App
from refresh import stages
from projectile import Projectile
p=argparse.ArgumentParser();p.add_argument('--out',required=True);args=p.parse_args();out=pathlib.Path(args.out);out.mkdir(parents=True,exist_ok=True);reports=[]
with tempfile.TemporaryDirectory(prefix='contact-fixtures-') as profile:
 os.environ['WWISUP_USER_DIR']=profile
 a=App(argparse.Namespace(theme='refresh',safe_window=True,play=False,stage=None,screen=None,smoke=None,screenshot=None));a.display.screen=pygame.display.set_mode((1920,1080));a.s.update(dialogue=False,sound=False,board_only=True,compact_hud=True)
 for name,px,y,speed,rotate in [('fast-wall-shield',380,420,150,False),('player-before-wall',180,420,150,False),('glancing',380,116,150,False),('miss',380,114,150,False),('rotation-active',380,200,0,True)]:
  d=stages.blank();d['title']='Collision study';grid=[list(' '*20) for _ in range(20)]
  for row in range(10,18):grid[row][13]='W'
  grid[18]=list('W'*20);d['tiles']=[''.join(row) for row in grid];d['entities']=[dict(type='player',x=7+px/40,y=17.5)];d['events']=[]
  stage=stages.Stage(d['id'],d['title'],'Live stress fixture',pathlib.Path('unused'),d,False);a.start_stage(stage,True)
  for _ in range(40):a.session.step({})
  shot=Projectile(a.session.canvas,227 if rotate else 80,y,speed,0);a.session.scene['objects'].append(shot)
  if rotate:
   a.session.scene['level'].flip(1)
   for o in a.session.scene['objects']:o.flip(1)
  frames=[];folder=out/name;folder.mkdir(exist_ok=True)
  for tick in range(34 if rotate else 8):
   a.session.step({})
   for alpha in (0.,.25,.5,.75,1.):
    if rotate and tick not in (0,1,14,29,30,31,32):continue
    a.stepper.accumulator=alpha/24;a.draw();file=f'{tick:02d}-{int(alpha*100):03d}.png';pygame.image.save(a.display.screen,folder/file)
    frames.append(dict(file=file,tick=a.session.tick,alpha=alpha,position=[shot.x,shot.y],state=shot.current_animation,impact=getattr(shot,'impact_point',None),fraction=getattr(shot,'impact_fraction',None),life=a.session.scene['player'].life))
  reports.append(dict(name=name,fixture=dict(player_x=px,projectile_y=y,velocity=speed,rotation=rotate,wall=[240,120,40,320],visible_body=[20,8]),frames=frames))
 (out/'MANIFEST.json').write_text(json.dumps(dict(commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),resolution=[1920,1080],method='Explicit authored stage and initial Projectile injection, then actual Session.step/App.draw only. Rotation fixture invokes normal Level.flip/Object.flip at setup. These are live stress fixtures, NOT campaign play or proof of campaign completion. No composite imagery. SDLdummy isolated profile.',fixtures=reports),indent=2))
 pygame.quit()
