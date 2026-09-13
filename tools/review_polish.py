#!/usr/bin/env python3
"""Render the local review gallery and exercise SDL with temporary player data."""
import argparse
import json
import os
from pathlib import Path
import statistics
import sys
import tempfile
import time
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--desktop',action='store_true')
    args=parser.parse_args()
    if not args.desktop:os.environ['SDL_VIDEODRIVER']='dummy'
    elif os.environ.get('WAYLAND_DISPLAY'):os.environ['SDL_VIDEODRIVER']='wayland'
    os.environ['SDL_AUDIODRIVER']='dummy'
    import pygame
    from refresh.app import App,THEME_ORDER
    from refresh import stages
    out=ROOT/'docs/polish-review';out.mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='wwisup-review-') as scratch:
        os.environ['WWISUP_USER_DIR']=scratch
        app=App(argparse.Namespace(theme='refresh',safe_window=True,play=False,stage=None,screen=None,smoke=None,screenshot=None))
        report={'backend':pygame.display.get_driver(),'desktop':pygame.display.get_desktop_sizes(),
                'audio':'dummy (native audio not assessed)','screens':[],'window_sizes':[]}
        def draw():
            for event in pygame.event.get():app.event(event)
            app.draw()
            if args.desktop:pygame.time.wait(20)
        for screen in ('home','settings','credits','help','records','stages','editor','play','pause','lost','complete'):
            if screen=='editor':app.new_editor()
            if screen=='play':
                app.preset('speedrun');app.start_stage(app.catalog.stages[0])
                for _ in range(38):app.session.step({})
            if screen=='complete':
                doc=stages.blank();doc['entities'][1]['x']=10.5
                app.start_stage(stages.Stage(doc['id'],doc['title'],'Review',Path('unused'),doc,False))
                for _ in range(400):
                    app.session.step({'RIGHT':True,'DOWN':True})
                    if app.session.result is not None:break
                assert app.session.result==3
                app.finish()
            else:app.route(screen)
            draw();pygame.image.save(app.ui.surface,out/(screen+'.png'));report['screens'].append(screen)
        app.message_until=0
        app.route('records');draw();pygame.image.save(app.ui.surface,out/'records-populated.png')
        for ident in THEME_ORDER:
            app.set_theme(ident);app.route('home');draw()
            pygame.image.save(app.ui.surface,out/(ident+'-home.png'))
        app.set_theme('refresh');app.route('home')
        for _ in range(4):
            app.display.cycle_size()
            for _ in range(12 if args.desktop else 1):draw()
            actual=app.display.screen.get_size();report['window_sizes'].append(actual)
            if args.desktop:
                assert all(abs(a-b)<=2 for a,b in zip(actual,app.display.windowed)),(actual,app.display.windowed)
        for _ in range(3):
            app.display.toggle();draw();assert app.display.fullscreen
            app.display.confirm();app.display.toggle();draw();assert not app.display.fullscreen
        app.display.toggle();app.display.deadline=time.monotonic()-1;app.update(0);draw()
        assert not app.display.fullscreen
        report['fullscreen_roundtrips']=3;report['rollback']='passed'
        app.start_stage(app.catalog.stages[0]);draw()
        app.pause();app.settings_screen('pause');tick=app.session.tick
        for _ in range(40):app.update(1/60);draw()
        assert app.session.tick==tick
        report['paused_settings']='passed'
        app.resume();app.s['dialogue']=False
        costs=[]
        for _ in range(180):
            start=time.perf_counter();app.update(1/60);app.draw();costs.append((time.perf_counter()-start)*1000)
        report['work_ms']={'median':round(statistics.median(costs),2),'p95':round(sorted(costs)[170],2),
                           'note':'180 scripted frames, no frame limiter; not a sustained FPS claim'}
        # Sprite atlas and animation are code-rendered game outputs.
        atlas=pygame.Surface((1024,384));atlas.fill(app.theme['background'])
        for row,state in enumerate(('walking','rising','falling','gliding')):
            for col in range(16):
                sprite=app.painter.sprite('player',32,44,state,col,'guy')
                atlas.blit(pygame.transform.scale(sprite,(64,88)),(col*64,row*96))
        pygame.image.save(atlas,out/'movement-atlas.png')
        report['running']=app.running
        (out/('native-report.json' if args.desktop else 'headless-report.json')).write_text(json.dumps(report,indent=2)+'\n')
        print(json.dumps(report,indent=2))
        pygame.quit()

if __name__=='__main__':main()
