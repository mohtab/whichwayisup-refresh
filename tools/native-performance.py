"""Real-time native diagnostic; leaves game source and user profile untouched."""
import os,sys,pathlib,tempfile,argparse,json,time,statistics,subprocess
root=pathlib.Path(__file__).resolve().parents[1];sys.path.insert(0,str(root));os.chdir(root)
os.environ.update(SDL_VIDEODRIVER='wayland',WWISUP_AUTO_WAYLAND='1',SDL_AUDIODRIVER='dummy')
import pygame
from refresh.app import App
parser=argparse.ArgumentParser();parser.add_argument('--out',required=True);args=parser.parse_args();out=root.parent/args.out;out.mkdir(exist_ok=True,parents=True)
with tempfile.TemporaryDirectory(prefix='wwiup-native-perf-') as profile:
 os.environ['WWISUP_USER_DIR']=profile;a=App(argparse.Namespace(theme='refresh',safe_window=True,play=False,stage=None,screen=None,smoke=None,screenshot=None));a.display.screen=pygame.display.set_mode((1920,1080));pygame.display.set_caption('Which Way Is Up? - isolated native performance diagnostic');a.s.update(dialogue=False,board_only=False,fps=60)
 a.start_stage(a.catalog.stages[0]);inputs=json.loads((root/'docs/campaign-acceptance/replays/w0-l0.json').read_text())['inputs'];a.controls=lambda:inputs[a.session.tick] if a.session.tick<len(inputs) else {}
 present=a.display.present;painter=a.painter.draw;current={}
 def timed_present(*args,**kwargs):
  t=time.perf_counter();result=present(*args,**kwargs);current['present_ms']=(time.perf_counter()-t)*1000;return result
 def timed_painter(*args,**kwargs):
  t=time.perf_counter();result=painter(*args,**kwargs);current['painter_ms']=(time.perf_counter()-t)*1000;return result
 a.display.present=timed_present;a.painter.draw=timed_painter
 samples=[];start=time.perf_counter();clock=pygame.time.Clock();pauses=[];rotation_first=None;rotation_image=None
 a.draw();startup_draw_ms=(time.perf_counter()-start)*1000;clock=pygame.time.Clock();start=time.perf_counter()
 while time.perf_counter()-start<60 and a.running:
  dt=clock.tick(60)/1000;frame_start=time.perf_counter()
  for e in pygame.event.get():a.event(e)
  before=a.session.tick;u=time.perf_counter();a.update(dt);update_ms=(time.perf_counter()-u)*1000
  rotating=any(getattr(t,'flipping',False) for t in a.session.scene['level'].tiles)
  d=time.perf_counter();a.draw();draw_ms=(time.perf_counter()-d)*1000
  row=dict(elapsed=time.perf_counter()-start,dt_ms=dt*1000,update_ms=update_ms,draw_ms=draw_ms,cost_ms=(time.perf_counter()-frame_start)*1000,tick=a.session.tick,ticks_advanced=a.session.tick-before,rotating=rotating,screen=a.screen,**current);samples.append(row)
  if rotating and rotation_first is None:rotation_first=row;rotation_image=a.display.screen.copy()
  if a.screen=='pause':pauses.append(dict(tick=a.session.tick,message=a.message));break
  if a.screen=='complete':break
 def distribution(rows,key):
  values=sorted(r[key] for r in rows)
  return dict(n=len(values),median=statistics.median(values),p95=values[int((len(values)-1)*.95)],maximum=max(values)) if values else None
 report=dict(commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=root,text=True).strip(),startup_draw_ms=startup_draw_ms,clock_reset_after_startup=True,backend=pygame.display.get_driver(),window_size=a.display.screen.get_size(),desktop_sizes=pygame.display.get_desktop_sizes(),method='Real wall-clock pygame Clock.tick60; normal App.update dt and24Hz simulation; actual native draw/present; original replay inputs; isolated temporary profile; full UI. No accelerated capture.',elapsed=time.perf_counter()-start,final_screen=a.screen,result=a.session.result,sim_tick=a.session.tick,first_rotation=rotation_first,pauses=pauses,distributions={mode:{k:distribution([r for r in samples if r['rotating']==rotate],k) for k in ('dt_ms','update_ms','draw_ms','painter_ms','present_ms','cost_ms')} for mode,rotate in [('steady',False),('rotation',True)]},samples=samples)
 if rotation_image is not None:pygame.image.save(rotation_image,out/'first-rotation.png')
 pygame.image.save(a.display.screen,out/'final.png');(out/'performance.json').write_text(json.dumps(report,indent=2));print(json.dumps({k:v for k,v in report.items() if k!='samples'},indent=2));pygame.quit()
