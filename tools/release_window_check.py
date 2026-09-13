#!/usr/bin/env python3
"""Native fullscreen/focus/menu recovery using isolated saves and synthetic input."""
import argparse
import json
import os
from pathlib import Path
import sys
import tempfile
import time
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--desktop',action='store_true')
    parser.add_argument('--output',type=Path,default=ROOT/'docs/release-review/window-check.json')
    args=parser.parse_args()
    if not args.desktop:os.environ['SDL_VIDEODRIVER']='dummy'
    elif os.environ.get('WAYLAND_DISPLAY') and 'SDL_VIDEODRIVER' not in os.environ:
        os.environ.update(SDL_VIDEODRIVER='wayland',WWISUP_AUTO_WAYLAND='1')
    os.environ['SDL_AUDIODRIVER']='dummy'
    import pygame
    from refresh.app import App
    from refresh import __version__
    with tempfile.TemporaryDirectory(prefix='wwisup-window-') as temp:
        os.environ['WWISUP_USER_DIR']=temp
        a=App(argparse.Namespace(theme='refresh',safe_window=True,play=False,stage=None,screen=None,smoke=None,screenshot=None))
        report={'version':__version__,'backend':pygame.display.get_driver(),'desktop_sizes':pygame.display.get_desktop_sizes(),
                'controllers_detected':pygame.joystick.get_count(),'checks':[],
                'limitations':['Controller actions are synthetic; no physical hardware acceptance.',
                               'No physical suspend or monitor movement performed. Audio is dummy.']}
        def frames(count=8):
            for _ in range(count):
                for e in pygame.event.get():a.event(e)
                a.update(1/60);a.draw();pygame.time.wait(16)
        def key(code):a.event(pygame.event.Event(pygame.KEYDOWN,key=code,mod=0));a.draw()
        try:
            frames();a.s['dialogue']=False;a.start_stage(a.catalog.stages[0]);frames(45)
            for attempt in range(3):
                key(pygame.K_F11);frames()
                assert a.display.fullscreen and a.screen=='pause'
                tick=a.session.tick;frames();assert a.session.tick==tick
                if attempt==0:key(pygame.K_RETURN)
                elif attempt==1:a.event(pygame.event.Event(pygame.JOYBUTTONDOWN,button=0))
                else:
                    a.draw();button=next(b for b in a.ui.buttons if b.label.startswith('Keep /'))
                    vp=a.display.viewport
                    pos=(vp.x+button.rect.centerx*vp.w/1200,vp.y+button.rect.centery*vp.h/800)
                    a.event(pygame.event.Event(pygame.MOUSEBUTTONDOWN,button=1,pos=pos))
                assert not a.display.deadline and a.screen=='pause'
                key(pygame.K_F11);frames();assert not a.display.fullscreen
                a.resume();frames();report['checks'].append('fullscreen round trip '+str(attempt+1))
            key(pygame.K_F11);a.display.deadline=time.monotonic()-1;frames()
            assert not a.display.fullscreen and a.screen=='pause';report['checks'].append('timeout rollback')
            a.resume();a.held.add(pygame.K_RIGHT);a.event(pygame.event.Event(pygame.WINDOWFOCUSLOST))
            assert a.screen=='pause' and not a.held;report['checks'].append('synthetic focus-loss pause/input clearing')
            a.open_settings();frames();a.back();a.resume();a.s.update(board_only=True,compact_hud=True);frames()
            assert a.display.content_size==(1040,1120);report['checks'].append('settings recovery and compact HUD')
            args.output.parent.mkdir(parents=True,exist_ok=True)
            pygame.image.save(a.display.screen,args.output.with_suffix('.png'))
            report['window_size']=a.display.screen.get_size();report['passed']=True
        finally:pygame.quit()
        args.output.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
if __name__=='__main__':main()
