#!/usr/bin/env python3
"""Dense genuine campaign contact evidence, without simulation state edits."""
import argparse,json,os,pathlib,sys,tempfile,subprocess
ROOT=pathlib.Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
os.environ.update(SDL_VIDEODRIVER='dummy',SDL_AUDIODRIVER='dummy',PYGAME_HIDE_SUPPORT_PROMPT='1')
import pygame
from refresh.app import App
p=argparse.ArgumentParser();p.add_argument('--out',required=True);p.add_argument('--scan',action='store_true');p.add_argument('--events',type=pathlib.Path);p.add_argument('--source-sha');p.add_argument('--tail-ticks',type=int,default=72);a=p.parse_args();out=pathlib.Path(a.out).resolve();out.mkdir(parents=True,exist_ok=True)
with tempfile.TemporaryDirectory(prefix='contacts-') as profile:
 os.environ['WWISUP_USER_DIR']=profile
 app=App(argparse.Namespace(theme='refresh',safe_window=True,play=False,stage=None,screen=None,smoke=None,screenshot=None));app.display.screen=pygame.display.set_mode((1920,1080));app.s.update(dialogue=False,sound=False,board_only=True,compact_hud=True)
 findings=[]
 for path in ([] if a.events else sorted((ROOT/'docs/campaign-acceptance/replays').glob('*.json'))):
  replay=json.loads(path.read_text());app.start_stage(next(s for s in app.catalog.stages if s.id==path.stem));session=app.session;last={};events=[];inventory=0
  for tick,inputs in enumerate(replay['inputs']):
   session.step(inputs)
   if len(session.scene['player'].inventory)>inventory:events.append({'tick':tick+1,'kind':'pickup'});inventory=len(session.scene['player'].inventory)
   for o in session.scene['objects']:
    if o.itemclass=='projectile' and o.current_animation=='dying' and last.get(id(o))=='default':events.append({'tick':tick+1,'kind':'impact','position':[o.x,o.y],'dimensions':list(o.rect.size)})
    last[id(o)]=o.current_animation
  findings.append({'stage':path.stem,'events':events,'result':session.result})
 if a.events:findings=json.loads(a.events.read_text())
 (out/'events.json').write_text(json.dumps(findings,indent=2))
 if not a.scan:
  chosen=[]
  for kind in ('pickup','impact'):
   match=next(( (f,e) for f in findings for e in f['events'] if e['kind']==kind),None)
   if match:chosen.append(match)
  for finding,event in chosen:
   stage=finding['stage'];inputs=json.loads((ROOT/f'docs/campaign-acceptance/replays/{stage}.json').read_text())['inputs'];app.start_stage(next(s for s in app.catalog.stages if s.id==stage));session=app.session
   folder=out/event['kind'];folder.mkdir(exist_ok=True);rows=[]
   for tick,command in enumerate(inputs):
    session.step(command)
    if event['tick']-8<=session.tick<=event['tick']+(a.tail_ticks if event['kind']=='pickup' else 24):
     for alpha in (.0,.5):
      if session.result is not None and app.screen=='play':app.finish()
      app.stepper.accumulator=alpha/24;app.draw();name=f'tick-{session.tick:04d}-{int(alpha*10)}.png';pygame.image.save(app.display.screen,folder/name)
      rows.append({'file':name,'tick':session.tick,'alpha':alpha,'player_animation':session.scene['player'].current_animation,'projectiles':[{'x':o.x,'y':o.y,'state':o.current_animation,'legacy_rect':list(o.rect.size),'visible_body':[20,8] if getattr(session,'rules',None) else [20,10],'impact_point':getattr(o,'impact_point',None),'impact_fraction':getattr(o,'impact_fraction',None)} for o in session.scene['objects'] if o.itemclass=='projectile']})
    if session.tick>event['tick']+(a.tail_ticks if event['kind']=='pickup' else 24):break
   (folder/'frames.json').write_text(json.dumps(rows,indent=2))
   names=sorted(folder.glob('tick-*.png'));listing=folder/'frames.txt';listing.write_text(''.join("file '"+str(n)+"'\nduration 0.020833333\n" for n in names))
   subprocess.run(['ffmpeg','-y','-loglevel','error','-f','concat','-safe','0','-i',str(listing),'-r','48','-c:v','libx264','-pix_fmt','yuv420p',str(folder/'contact.mp4')],check=True)
  (out/'MANIFEST.json').write_text(json.dumps({'commit':a.source_sha or subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),'capture_helper':'tools/capture-contacts.py','resolution':[1920,1080],'method':'Real Session.step campaign inputs; App.draw, two interpolation samples per24Hz tick; SDLdummy isolated profile; no simulation edits or image composites; accelerated, not performance evidence.','events':[{'stage':f['stage'],**e} for f,e in chosen]},indent=2))
 pygame.quit()
