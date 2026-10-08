#!/usr/bin/env python3
"""Unmodified Original world pixel regression using campaign input."""
import os,sys,pathlib,argparse,json,tempfile,subprocess
ROOT=pathlib.Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT));os.environ.update(SDL_VIDEODRIVER='dummy',SDL_AUDIODRIVER='dummy',PYGAME_HIDE_SUPPORT_PROMPT='1')
import pygame
from refresh.app import App
p=argparse.ArgumentParser();p.add_argument('--out',required=True);p.add_argument('--source-sha');args=p.parse_args();out=pathlib.Path(args.out);out.mkdir(parents=True,exist_ok=True)
with tempfile.TemporaryDirectory(prefix='original-pixels-') as profile:
 os.environ['WWISUP_USER_DIR']=profile;a=App(argparse.Namespace(theme='original',safe_window=True,play=False,stage=None,screen=None,smoke=None,screenshot=None));a.s.update(dialogue=False,sound=False);a.start_stage(a.catalog.stages[0]);inputs=json.loads((ROOT/'docs/campaign-acceptance/replays/w0-l0.json').read_text())['inputs']
 for i,command in enumerate(inputs):
  a.session.step(command)
  if a.session.tick in (70,228,240,1027,1030,1050):
   pygame.image.save(a.painter.draw(a.session,a.theme,a.s,.5),out/f'tick-{a.session.tick}.png')
 (out/'MANIFEST.json').write_text(json.dumps(dict(commit=args.source_sha or subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),method='Original Painter output1040square from real campaign replay at alpha0.5; no image changes; includes movement, rotation, pickup and terminal animation. Isolated profile.'),indent=2))
 pygame.quit()
