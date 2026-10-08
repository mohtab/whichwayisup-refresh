import sys,os,pathlib,argparse,tempfile,json,subprocess
root=pathlib.Path(__file__).resolve().parents[1];b=root.parent;sys.path.insert(0,str(root));os.environ.update(SDL_VIDEODRIVER='dummy',SDL_AUDIODRIVER='dummy')
import pygame
from refresh.app import App
parser=argparse.ArgumentParser();parser.add_argument('--out',required=True);args=parser.parse_args();out=b/args.out;out.mkdir(parents=True,exist_ok=True)
with tempfile.TemporaryDirectory() as p:
 os.environ['WWISUP_USER_DIR']=p;a=App(argparse.Namespace(theme='refresh',safe_window=True,play=False,stage=None,screen=None,smoke=None,screenshot=None));a.display.screen=pygame.display.set_mode((1920,1080));a.s.update(dialogue=False,board_only=True,compact_hud=True);a.start_stage(a.catalog.stages[0]);inputs=json.loads((root/'docs/campaign-acceptance/replays/w0-l0.json').read_text())['inputs'];a.controls=lambda:inputs[a.session.tick] if a.session.tick<len(inputs) else {};rows=[];seen=False;rotation_frame=0;last=None
 for n in range(2400):
  a.update(1/60);rotating=any(getattr(t,'flipping',False) for t in a.session.scene['level'].tiles)
  if rotating:
   if not seen and last is not None:pygame.image.save(last,out/'before.png')
   seen=True
   if rotation_frame%6==0:
    a.draw();name=f'phase-{rotation_frame:03d}.png';pygame.image.save(a.display.screen,out/name);rows.append(dict(file=name,tick=a.session.tick,interpolation=a.stepper.alpha))
   rotation_frame+=1
  elif seen:
   a.draw();pygame.image.save(a.display.screen,out/'after.png');break
  elif a.session.tick>205:a.draw();last=a.display.screen.copy()
 (out/'MANIFEST.json').write_text(json.dumps(dict(commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=root,text=True).strip(),method='Original replay via real App.update fixed1/60 and App.draw; SDLdummy1920x1080; isolated profile; firstgenuine rotation sampled every6renderframes, before/after. No position edits. Accelerated evidence, not FPS measurement.',rotation_render_frames=rotation_frame,frames=rows),indent=2));print(len(rows),rotation_frame);pygame.quit()
