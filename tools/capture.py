#!/usr/bin/env python3
"""Capture uncomposited live Pygame frames with an isolated player profile."""
import argparse, datetime, json, os, pathlib, subprocess, sys, tempfile
p=argparse.ArgumentParser();p.add_argument('--out',default='artifacts/baseline');p.add_argument('--stills-only',action='store_true');a=p.parse_args()
BASE=pathlib.Path(__file__).resolve().parents[2];ROOT=pathlib.Path(__file__).resolve().parents[1];OUT=BASE/a.out
for name in ('stills','walkthrough-frames'): (OUT/name).mkdir(parents=True,exist_ok=True)
os.environ.update(SDL_VIDEODRIVER='dummy',SDL_AUDIODRIVER='dummy',PYGAME_HIDE_SUPPORT_PROMPT='1')
sys.path.insert(0,str(ROOT))
import pygame
from refresh.app import App
sha=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
with tempfile.TemporaryDirectory(prefix='wwiup-capture-') as profile:
 os.environ['WWISUP_USER_DIR']=profile
 app=App(argparse.Namespace(theme='refresh',safe_window=True,play=False,stage=None,screen=None,smoke=None,screenshot=None))
 app.display.screen=pygame.display.set_mode((1920,1080));app.s.update(dialogue=False,sound=False,board_only=False,compact_hud=False)
 def save(name):
  app.draw();pygame.image.save(app.display.screen,OUT/'stills'/name)
 save('still-01-home.png')
 app.start_stage(app.catalog.stages[0])
 for _ in range(70):app.update(1/24)
 save('still-02-full-gameplay.png')
 app.s.update(board_only=True,compact_hud=True);save('still-03-compact-gameplay.png')
 app.settings_screen('home');save('still-04-settings.png')
 manifest={'commit':sha,'timestamp':datetime.datetime.now(datetime.timezone.utc).isoformat(),'resolution':[1920,1080],'capture':'Unmodified App.draw display surface, SDL dummy driver. Game internal UI 1200x800 and board 1040x1040; normal Display.present fits these to 1920x1080. No post-render enlargement, compositing, or retouching. Not physical desktop evidence.','profile':'temporary isolated WWISUP_USER_DIR, destroyed on exit','stills':['home','Refresh full gameplay w0-l0','Refresh compact HUD gameplay w0-l0','Display settings'],'refs':'Matching pending Stage A reference lock.'}
 (OUT/'stills'/'MANIFEST.md').write_text('# Live runtime baseline\n\n'+json.dumps(manifest,indent=2)+'\n')
 print('STILLS_READY',OUT/'stills',flush=True)
 if not a.stills_only:
  replay=json.loads((ROOT/'docs/campaign-acceptance/replays/w0-l0.json').read_text())
  app.route('home');app.s.update(board_only=False,compact_hud=False)
  video=subprocess.Popen(['ffmpeg','-y','-loglevel','error','-f','rawvideo','-pixel_format','rgb24','-video_size','1920x1080','-framerate','30','-i','-','-c:v','libx264','-preset','ultrafast','-crf','20','-pix_fmt','yuv420p',str(OUT/'walkthrough.mp4')],stdin=subprocess.PIPE)
  screens=[]
  for frame in range(2250):
   if frame==120:app.settings_screen('home')
   if frame==145:app.ui.move(1)
   if frame==160:app.ui.activate()
   if frame==180:app.ui.focus=5;app.ui.activate()
   if frame==210:
    next(b for b in app.ui.buttons if b.label=='Done').action()
   if frame==240:
    app.s['dialogue']=True;app.start_stage(app.catalog.stages[0])
   if frame==420:app.pause()
   if frame==600:
    app.s['dialogue']=False;app.start_stage(app.catalog.stages[0]);app.controls=lambda: replay['inputs'][app.session.tick] if app.session.tick<len(replay['inputs']) else {}
   if frame==1050:app.s.update(board_only=True,compact_hud=True)
   if frame==1900:app.s.update(board_only=False,compact_hud=False)
   pygame.event.pump();app.update(1/30);app.draw()
   video.stdin.write(pygame.image.tobytes(app.display.screen,'RGB'))
   if frame%225==112:
    pygame.image.save(app.display.screen,OUT/'walkthrough-frames'/f'frame-{frame:04d}.png');screens.append({'frame':frame,'screen':app.screen,'tick':app.session.tick if app.session else None})
  video.stdin.close();assert video.wait()==0
  (OUT/'walkthrough.json').write_text(json.dumps({'commit':sha,'duration_seconds':75,'fps':30,'frames':2250,'method':'Live App.update and App.draw, fixed timestep, scripted settings/routes plus original campaign replay inputs. Encoded in accelerated wall time; no simulation state edits. Audio not assessed.','samples':screens,'final_screen':app.screen,'result':app.session.result},indent=2)+'\n')
  print('VIDEO_READY',app.screen,app.session.result,flush=True)
 pygame.quit()
