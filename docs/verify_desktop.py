"""Exercise actual SDL window transitions with temporary user data; no desktop config edits."""
from pathlib import Path
import os
import tempfile
import argparse
import time
import json
import sys
root=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(root))
# This must run outside the sandbox for a real native desktop verification.
with tempfile.TemporaryDirectory(prefix='wwisup-desktop-') as scratch:
    os.environ['WWISUP_USER_DIR']=scratch
    import pygame
    from refresh.app import App
    args=argparse.Namespace(theme='refresh',safe_window=True,play=False,stage=None,screen=None,smoke=None,screenshot=None)
    app=App(args)
    report={'backend':pygame.display.get_driver(),'desktop':pygame.display.get_desktop_sizes(),'transitions':[]}
    def frames(count=12):
        for _ in range(count):
            for event in pygame.event.get():app.event(event)
            app.update(1/60);app.draw()
            pygame.time.wait(16)
    frames()
    for ident in ('original','refresh','omarchy','system','cyberpunk'):
        app.set_theme(ident);frames(3)
        pygame.image.save(app.ui.surface,root/'docs/screenshots'/f'{ident}-desktop.png')
    for _ in range(3):
        app.display.toggle();frames()
        report['transitions'].append({'fullscreen':app.display.fullscreen,'size':app.display.screen.get_size(),'running':app.running})
        assert app.running,'Game received a quit event during fullscreen transition'
        app.display.confirm();app.display.toggle();frames()
        report['transitions'].append({'fullscreen':app.display.fullscreen,'size':app.display.screen.get_size(),'running':app.running})
    app.display.toggle();app.display.deadline=time.monotonic()-1;app.update(0);frames()
    assert not app.display.fullscreen,'Display rollback failed'
    report['rollback']='passed'
    app.start_stage(app.catalog.stages[0]);frames(60)
    app.pause();app.settings_screen('pause');frames()
    app.set_theme('system');app.route('pause');app.resume();frames()
    app.new_editor();frames()
    pygame.image.save(app.ui.surface,root/'docs/screenshots/editor-desktop.png')
    app.editor_test();frames(40);app.pause();app.return_editor();frames()
    report['play_pause_theme_editor']='passed'
    report['running']=app.running
    (root/'docs/desktop-verification.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))
    pygame.quit()
