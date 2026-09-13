#!/usr/bin/env python3
"""Game-rendered sprite/contact gallery and an animated pose showcase."""
import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--desktop',action='store_true');args=parser.parse_args()
    if args.desktop and os.environ.get('WAYLAND_DISPLAY'):os.environ['SDL_VIDEODRIVER']='wayland'
    elif not args.desktop:os.environ['SDL_VIDEODRIVER']='dummy'
    os.environ['SDL_AUDIODRIVER']='dummy'
    import pygame
    from refresh.app import App
    from refresh import sprites,stages
    from refresh.runtime import Session
    from refresh.ui import font
    out=ROOT/'docs/sprite-review-v2';out.mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='wwisup-sprite-review-') as scratch:
        os.environ['WWISUP_USER_DIR']=scratch
        a=App(argparse.Namespace(theme='refresh',safe_window=True,play=False,stage=None,screen=None,smoke=None,screenshot=None))
        a.s['dialogue']=False;a.s['smooth']=True;a.start_stage(a.catalog.stages[0])
        for _ in range(40):a.session.step({})
        a.draw();pygame.image.save(a.ui.surface,out/'gameplay.png')
        for theme in ('cyberpunk','omarchy','original'):
            a.set_theme(theme);a.draw();pygame.image.save(a.ui.surface,out/(theme+'-gameplay.png'))
        a.set_theme('refresh')
        report={'backend':pygame.display.get_driver(),'sprite_sheets':4,'renderer_size':a.painter.world.get_size()}
        def board(frame):
            canvas=pygame.Surface((1200,800));canvas.fill(a.theme['background'])
            def label(value,x,y,size=20):canvas.blit(font(size).render(value,True,a.theme['foreground']),(x,y))
            label('WHICH WAY IS UP?  /  SPRITE & CONTACT REVIEW',34,27,24)
            phase=frame%16
            for i,side in enumerate((1,0,3,2)):
                x=58+i*293;y=137
                sprite=sprites.orient_spider(sprites.spider(40,40,'walking',phase,4),side)
                canvas.blit(sprite,(x,y))
                wall={1:(x,y+160,160,12),0:(x+160,y,12,160),3:(x,y-12,160,12),2:(x-12,y,12,160)}[side]
                pygame.draw.rect(canvas,a.theme['secondary'],wall)
                label(('Floor','Right wall','Ceiling','Left wall')[i],x,y-52,18)
            for i,state in enumerate(('walking','takeoff','apex','falling','landing','hurt')):
                age=(frame//2)%6 if state in ('landing','hurt','takeoff') else phase
                im=sprites.player(28,33,state,age,3)
                canvas.blit(im,im.get_rect(midbottom=(96+i*195,568)))
                label(state.title(),50+i*195,591,17)
            im=sprites.key(40,40,phase,3);canvas.blit(im,(54,651))
            label('Clockwork compass key',214,675,20)
            label('Grounded feet. Body compression. Jump stretch. Impact recoil.',214,713,16)
            return canvas
        movie=out/'animation-review.mp4'
        encoder=subprocess.Popen(['ffmpeg','-loglevel','error','-y','-f','rawvideo','-pixel_format','rgb24','-video_size','1200x800',
                                  '-framerate','24','-i','-','-an','-c:v','libx264','-crf','19','-pix_fmt','yuv420p','-movflags','+faststart',str(movie)],stdin=subprocess.PIPE)
        try:
            for frame in range(144):
                canvas=board(frame);encoder.stdin.write(pygame.image.tobytes(canvas,'RGB'))
                if frame==2:pygame.image.save(canvas,out/'contact-and-poses.png')
                if args.desktop:
                    pygame.event.pump();a.display.present(canvas);pygame.time.wait(15)
        finally:encoder.stdin.close()
        assert encoder.wait()==0
        # Actual simulation events: jump, landing, damage and a room flip.
        doc=stages.blank();doc['events']=[]
        a.start_stage(stages.Stage('motion-review','Motion review','Review',Path('unused'),doc,False))
        seen=set();costs=[]
        for tick in range(180):
            inputs={}
            if tick in (35,80):inputs['JUMP']=True
            if 80<tick<111:inputs['UP']=True
            if tick==120:a.session.scene['player'].take_damage(5)
            if tick==145:inputs['SPECIAL']=True
            start=time.perf_counter();a.session.step(inputs)
            p=a.session.scene['player'];pose=a.session.motion.pose(p,a.session.tick,inputs)[0];seen.add(pose)
            a.draw();costs.append((time.perf_counter()-start)*1000)
            if pose in ('takeoff','landing','hurt'):
                target=out/(pose+'-in-game.png')
                if not target.exists():pygame.image.save(a.ui.surface,target)
            if args.desktop:pygame.event.pump();pygame.time.wait(10)
        for expected in ('takeoff','rising','apex','falling','landing','hurt'):assert expected in seen,expected
        report.update(observed_poses=sorted(seen),work_ms_median=round(sorted(costs)[90],2),work_ms_p95=round(sorted(costs)[170],2),
                      note='Scripted fixture and debug-triggered damage/rotation; not a campaign playthrough. Timing is a short diagnostic.')
        (out/('native.json' if args.desktop else 'headless.json')).write_text(json.dumps(report,indent=2)+'\n')
        print(json.dumps(report,indent=2));pygame.quit()

if __name__=='__main__':main()
