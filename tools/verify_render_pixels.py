#!/usr/bin/env python3
"""Compare real rendered canvases with opaque RGB references, including on Wayland."""
import argparse,json,os,sys,tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--desktop',action='store_true')
    parser.add_argument('--high-contrast',action='store_true')
    parser.add_argument('--output',type=Path,default=ROOT/'docs/release-review/render-pixels.json')
    args=parser.parse_args()
    if args.desktop:
        if os.environ.get('WAYLAND_DISPLAY') and 'SDL_VIDEODRIVER' not in os.environ:
            os.environ.update(SDL_VIDEODRIVER='wayland',WWISUP_AUTO_WAYLAND='1')
    else:os.environ['SDL_VIDEODRIVER']='dummy'
    os.environ['SDL_AUDIODRIVER']='dummy'
    import pygame
    from refresh import __version__
    from refresh.app import App
    with tempfile.TemporaryDirectory(prefix='wwisup-pixels-') as temp:
        os.environ['WWISUP_USER_DIR']=temp
        a=App(argparse.Namespace(theme='omarchy',safe_window=True,play=False,stage=None,screen=None,smoke=None,screenshot=None))
        original_present=a.display.present;checks=[]
        def rgb(image):return pygame.image.frombytes(pygame.image.tobytes(image,'RGB'),image.get_size(),'RGB')
        def checked_present(surface,**kwargs):
            original_present(surface,**kwargs)
            actual=pygame.image.tobytes(a.display.screen,'RGB')
            reference=dict(kwargs)
            reference['layers']=[(rgb(layer[0]),*layer[1:]) for layer in kwargs.get('layers',())]
            original_present(rgb(surface),**reference)
            expected=pygame.image.tobytes(a.display.screen,'RGB')
            if actual!=expected:raise AssertionError('Canvas alpha changed visible RGB pixels: '+label)
            checks.append(label)
        a.display.present=checked_present
        a.s['dialogue']=False
        a.s['high_contrast']=args.high_contrast
        for theme in ('original','refresh','omarchy','system','cyberpunk'):
            a.set_theme(theme)
            for view in ('home','full','board','compact'):
                label=theme+'/'+view
                if view=='home':a.route('home')
                else:
                    a.start_stage(a.catalog.stages[0])
                    for _ in range(40):a.session.step({})
                    a.s.update(board_only=view!='full',compact_hud=view=='compact')
                pygame.event.pump();a.draw()
        report={'version':__version__,'backend':pygame.display.get_driver(),'high_contrast':args.high_contrast,'checks_passed':len(checks),'checks':checks,
                'reference':'RGB-only snapshots of completed canvases; exact final framebuffer comparison.'}
        args.output.parent.mkdir(parents=True,exist_ok=True);args.output.write_text(json.dumps(report,indent=2)+'\n')
        pygame.quit();print(json.dumps(report,indent=2))
if __name__=='__main__':main()
