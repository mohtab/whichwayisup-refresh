#!/usr/bin/env python3
import argparse,datetime,json,os,pathlib,subprocess,sys,tempfile
BASE=pathlib.Path(__file__).resolve().parents[2];ROOT=BASE/'game';parser=argparse.ArgumentParser();parser.add_argument('--out',default='artifacts/baseline/matched-stills');args=parser.parse_args();OUT=BASE/args.out;OUT.mkdir(parents=True,exist_ok=True)
os.environ.update(SDL_VIDEODRIVER='dummy',SDL_AUDIODRIVER='dummy',PYGAME_HIDE_SUPPORT_PROMPT='1');sys.path.insert(0,str(ROOT))
import pygame
from refresh.app import App
with tempfile.TemporaryDirectory(prefix='wwiup-matched-') as profile:
 os.environ['WWISUP_USER_DIR']=profile
 app=App(argparse.Namespace(theme='refresh',safe_window=True,play=False,stage=None,screen=None,smoke=None,screenshot=None));app.display.screen=pygame.display.set_mode((1920,1080))
 app.s.update(dialogue=False,sound=False,board_only=True,compact_hud=True)
 entries=[]
 for n,stage_id,ticks,dialogue,slot in [(1,'w0-l0',70,False,'wide'),(2,'w1-l5',70,False,'action-hazards'),(3,'w1-l0',85,False,'mood-depth'),(4,'w0-l0',70,True,'dialogue')]:
  app.s['dialogue']=dialogue;app.start_stage(next(s for s in app.catalog.stages if s.id==stage_id))
  for _ in range(ticks):app.update(1/24)
  app.draw();name=f'still-{n:02d}.png';pygame.image.save(app.display.screen,OUT/name)
  entries.append(dict(file=name,stage=stage_id,tick=app.session.tick,screen=app.screen,dialogue=bool(app.session.scene['dialogue']),slot=slot,camera='Full square board compact HUD; Refresh dialogue uses fixed right680 square board with352px external dialogue measure',matched_ref=f'ref-{n:02d}'))
 (OUT/'MANIFEST.md').write_text('# Live steady-state stills\n\n'+json.dumps({'commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),'timestamp':datetime.datetime.now(datetime.timezone.utc).isoformat(),'resolution':[1920,1080],'provenance':'Unmodified App.update and App.draw with SDL dummy at requested display resolution. Normal internal-canvas scaling by Display.present. No image postprocessing. Isolated temporary profile.','stills':entries},indent=2)+'\n')
 print(json.dumps(entries));pygame.quit()
