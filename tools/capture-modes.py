#!/usr/bin/env python3
"""Real routes and campaign completion across themes, with a disclosed custom palette."""
import argparse,os,sys,pathlib,tempfile,json,subprocess,dataclasses
ROOT=pathlib.Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT));os.environ.update(SDL_VIDEODRIVER='dummy',SDL_AUDIODRIVER='dummy',PYGAME_HIDE_SUPPORT_PROMPT='1')
import pygame
from refresh.app import App
p=argparse.ArgumentParser();p.add_argument('--out',required=True);args=p.parse_args();out=pathlib.Path(args.out);out.mkdir(parents=True,exist_ok=True);rows=[]
with tempfile.TemporaryDirectory(prefix='mode-evidence-') as profile:
 os.environ['WWISUP_USER_DIR']=profile
 a=App(argparse.Namespace(theme='refresh',safe_window=True,play=False,stage=None,screen=None,smoke=None,screenshot=None));a.display.screen=pygame.display.set_mode((1920,1080));a.s.update(sound=False,dialogue=False)
 custom=dataclasses.replace(a.themes.packs['cyberpunk'],id='copper-dusk',name='Copper dusk',palette=dict(a.themes.packs['cyberpunk'].palette,accent=(225,167,104),secondary=(95,176,185)))
 a.themes.packs[custom.id]=custom
 def save(name):
  a.message_until=0;a.draw();pygame.image.save(a.display.screen,out/(name+'.png'))
  rows.append(dict(file=name+'.png',theme=a.theme.id,screen=a.screen,rules=a.session.rules_id if a.session else None,focus=a.ui.focus,buttons=[dict(label=b.label,rect=list(b.rect)) for b in a.ui.buttons]))
 inputs=json.loads((ROOT/'docs/campaign-acceptance/replays/w0-l0.json').read_text())['inputs']
 for theme in ('refresh','original','omarchy','system','cyberpunk','copper-dusk'):
  a.route('home');a.set_theme(theme);a.s.update(board_only=False,compact_hud=False)
  for preset in ('story','speedrun'):a.preset(preset);save(theme+'-home-'+preset)
  a.route('stages');a.page=0;save(theme+'-library');a.page=1;save(theme+'-library-page2');a.page=0
  a.new_editor();save(theme+'-studio');a.editor.document['title']='Contact workshop';a.editor_save();a.route('stages');a.page=1;save(theme+'-custom-stage');a.page=0
  a.settings_screen('home')
  for tab in ('Display','Gameplay','Controls','Audio','Advanced'):a.settings_tab=tab;a.ui.focus=5;save(theme+'-settings-'+tab.lower())
  a.s['dialogue']=False;a.start_stage(a.catalog.stages[0])
  for i,command in enumerate(inputs):
   a.session.step(command)
   if i==70:
    save(theme+'-full');a.s.update(board_only=True,compact_hud=True);save(theme+'-compact');a.s.update(board_only=False)
    a.pause();save(theme+'-pause');a.resume()
   if a.session.result is not None:break
  assert a.session.result==3,(theme,a.session.result)
  a.finish();save(theme+'-complete');a.route('records');save(theme+'-records')
 (out/'MANIFEST.json').write_text(json.dumps(dict(commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),resolution=[1920,1080],method='Actual App routes/draw and genuine w0-l0 campaign input completion for each theme; isolated profile; custom palette is an in-memory copy with disclosed colors, custom stage is saved through editor. No fabricated outcome. SDLdummy accelerated, not performance evidence.',custom_palette=custom.palette,captures=rows),indent=2))
 pygame.quit()
