#!/usr/bin/env python3
"""Native UI-state evidence; fixtures are disclosed separately from live replay."""
import argparse,os,pathlib,sys,tempfile,json,subprocess,time
p=argparse.ArgumentParser();p.add_argument('--out',required=True);args=p.parse_args()
ROOT=pathlib.Path(__file__).resolve().parents[1];BASE=ROOT.parent;out=BASE/args.out;out.mkdir(parents=True,exist_ok=True)
os.environ.update(SDL_VIDEODRIVER='dummy',SDL_AUDIODRIVER='dummy');sys.path.insert(0,str(ROOT))
import pygame
from refresh.app import App
sha=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip();rows=[]
with tempfile.TemporaryDirectory() as profile:
 os.environ['WWISUP_USER_DIR']=profile;a=App(argparse.Namespace(theme='refresh',safe_window=True,play=False,stage=None,screen=None,smoke=None,screenshot=None));a.display.screen=pygame.display.set_mode((1920,1080));a.s.update(board_only=False,dialogue=False)
 def save(name,method='Real navigation/render; no gameplay state edits'):
  a.message_until=0;a.draw();pygame.image.save(a.display.screen,out/(name+'.png'));rows.append(dict(file=name+'.png',method=method,screen=a.screen,theme=a.theme.id,resolution=list(a.display.screen.get_size()),tick=a.session.tick if a.session else None))
 save('home-empty');a.route('records');save('records-empty');a.route('stages');save('stages')
 a.settings_screen('home')
 for tab in ('Display','Audio','Controls','Gameplay','Advanced'):
  a.settings_tab=tab;a.ui.focus=6;save('settings-'+tab.lower())
 a.remap('jump');save('remap');a.modal=None
 a.display.deadline=time.monotonic()+15;save('fullscreen-confirm','Confirmation overlay fixture with deadline; no desktop fullscreen mode change');a.display.deadline=None
 a.start_stage(a.catalog.stages[0])
 for _ in range(70):a.update(1/24)
 save('full-play');a.pause();save('pause');a.show_help();save('help');a.route('play')
 # Long strings are presentation fixtures, never advertised as real live play.
 originals=[line[len('dialogue '):] for f in (ROOT/'data/levels').glob('*.txt') for line in f.read_text().splitlines() if line.startswith('dialogue ')]
 a.session.scene['dialogue']=max(originals,key=len);a.dialogue_token=None;save('dialogue-longest-original','Longest shipped dialogue copied into presentation fixture; simulation frozen')
 a.session.scene['dialogue']=('The wheel turns and the explorer waits for the chamber to settle. '*9)+'UnbrokenWord'*18;a.dialogue_token=None
 video=subprocess.Popen(['ffmpeg','-y','-loglevel','error','-f','rawvideo','-pixel_format','rgb24','-video_size','1920x1080','-framerate','30','-i','-','-c:v','libx264','-preset','ultrafast','-crf','20','-pix_fmt','yuv420p',str(out/'dialogue-interaction.mp4')],stdin=subprocess.PIPE)
 for frame in range(360):
  if frame in (60,120):a.event(pygame.event.Event(pygame.KEYDOWN,key=pygame.K_z,mod=0))
  if frame in (180,270):a.event(pygame.event.Event(pygame.KEYDOWN,key=pygame.K_ESCAPE,mod=0))
  a.draw();video.stdin.write(pygame.image.tobytes(a.display.screen,'RGB'))
 video.stdin.close();assert video.wait()==0
 a.dialogue_page=0
 pages=[]
 while True:
  save('dialogue-custom-page-'+str(a.dialogue_page+1),'Long custom dialogue/unbroken-word presentation fixture; simulation frozen')
  pages.extend(a.dialogue_lines()[a.dialogue_page*6:(a.dialogue_page+1)*6])
  if not a.advance_dialogue():break
 a.session.scene['dialogue']='';a.screen='lost';save('lost','Loss presentation fixture; no claim this run failed');a.route('play')
 a.s.update(effects=False,high_contrast=True);save('reduced-effects-high-contrast');a.s.update(effects=True,high_contrast=False)
 a.start_stage(a.catalog.stages[0]);replay=json.loads((ROOT/'docs/campaign-acceptance/replays/w0-l0.json').read_text())['inputs'];a.controls=lambda:replay[a.session.tick] if a.session.tick<len(replay) else {}
 for _ in range(2400):
  a.update(1/24)
  if a.screen=='complete':break
 assert a.screen=='complete';save('complete','Genuine original w0-l0 replay completion via App.update/finish')
 a.completion_saved=False;save('complete-save-failed','Save failure presentation fixture after genuine completion');a.completion_saved=True
 a.route('home');save('home-continue');a.route('records');save('records-populated')
 a.completed_world=a.active_stage.world;a.route('ending');save('campaign-results','Campaign-results branch fixture after one genuine stage completion; actual stored counts retained')
 for theme in ('original','cyberpunk'):
  a.set_theme(theme);a.route('home');save(theme+'-home');a.settings_screen('home');a.settings_tab='Display';save(theme+'-settings');a.start_stage(a.catalog.stages[0]);a.s['board_only']=False
  for _ in range(70):a.update(1/24)
  save(theme+'-play')
 a.set_theme('refresh');a.route('home');a.display.screen=pygame.display.set_mode((800,533));save('small-window-home')
 (out/'MANIFEST.json').write_text(json.dumps(dict(commit=sha,resolution=[1920,1080],backend='SDL dummy',profile='temporary isolated',captures=rows,longtext_lines=pages,physical_controller=False),indent=2))
 pygame.quit()
