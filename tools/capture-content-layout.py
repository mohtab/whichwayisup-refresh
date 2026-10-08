#!/usr/bin/env python3
"""Disclosed content extremes, separate from genuine play evidence."""
import argparse,json,os,pathlib,subprocess,sys,tempfile
p=argparse.ArgumentParser();p.add_argument('--out',required=True);args=p.parse_args()
ROOT=pathlib.Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT));out=pathlib.Path(args.out);out.mkdir(parents=True,exist_ok=True)
os.environ.update(SDL_VIDEODRIVER='dummy',SDL_AUDIODRIVER='dummy',PYGAME_HIDE_SUPPORT_PROMPT='1')
import pygame
from refresh.app import App
rows=[]
with tempfile.TemporaryDirectory(prefix='content-layout-') as profile:
 os.environ['WWISUP_USER_DIR']=profile
 a=App(argparse.Namespace(theme='refresh',safe_window=True,play=False,stage=None,screen=None,smoke=None,screenshot=None));a.display.screen=pygame.display.set_mode((1920,1080));a.s.update(sound=False,board_only=False)
 def save(name,method):
  a.message_until=0;a.draw();pygame.image.save(a.display.screen,out/(name+'.png'));rows.append(dict(file=name+'.png',method=method,screen=a.screen,theme=a.theme.id))
 for count in (0,1,6,7):
  a.store.records={str(i):dict(stage='Stage '+str(i+1),category='1x:no-dialogue',rules='enhanced-connected-v1',best_seconds=36.958+i) for i in range(count)}
  a.route('records');a.records_page=0;save('records-'+str(count),'Synthetic local-record row-count fixture, not earned results')
  if count==7:a.records_page=1;save('records-page2','Synthetic pagination fixture')
 a.s['dialogue']=False;a.start_stage(a.catalog.stages[0])
 for _ in range(70):a.update(1/24)
 for count in (1,6,9):
  a.session.scene['dialogue']='\n'.join('The chamber turns.' for _ in range(count));a.dialogue_token=None
  save('dialogue-'+str(count),'Synthetic dialogue line-count fixture, simulation frozen')
  if count>6:a.advance_dialogue();save('dialogue-page2','Synthetic dialogue pagination fixture')
 a.route('home');a.set_theme('system');a.new_editor();a.editor.document['title']='A very long custom chamber name for checking the stage library';a.editor_save();a.route('stages');a.page=1;save('system-long-custom','Saved temporary long-name custom stage through actual editor')
 (out/'MANIFEST.json').write_text(json.dumps(dict(commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),resolution=[1920,1080],captures=rows),indent=2)+'\n')
 pygame.quit()
