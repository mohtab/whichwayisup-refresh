#!/usr/bin/env python3
"""Native/headless visual acceptance: board-only, materials and DHH poses."""
import argparse,json,os,subprocess,sys,tempfile,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
def main():
    parser=argparse.ArgumentParser();parser.add_argument('--desktop',action='store_true');args=parser.parse_args()
    os.environ['SDL_VIDEODRIVER']='wayland' if args.desktop else 'dummy';os.environ['SDL_AUDIODRIVER']='dummy'
    import pygame
    from refresh.app import App
    from refresh import sprites
    from refresh.ui import font
    out=ROOT/'docs/visual-review-v3';out.mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='wwisup-v3-review-') as scratch:
        os.environ['WWISUP_USER_DIR']=scratch
        a=App(argparse.Namespace(theme='omarchy',safe_window=True,play=False,stage=None,screen=None,smoke=None,screenshot=None))
        a.s['dialogue']=False;a.s['board_only']=True;a.s['smooth']=True;a.start_stage(a.catalog.stages[0])
        for _ in range(40):a.session.step({})
        a.draw();pygame.image.save(a.display.screen,out/'board-only.png')
        a.s['board_only']=False;a.draw();pygame.image.save(a.ui.surface,out/'omarchy-gameplay.png')
        a.set_theme('refresh');a.draw();pygame.image.save(a.ui.surface,out/'refresh-gameplay.png')
        a.open_settings();a.draw();pygame.image.save(a.ui.surface,out/'settings.png')
        a.show_help();a.draw();pygame.image.save(a.ui.surface,out/'shortcuts.png')
        def board(frame):
            s=pygame.Surface((1200,800));s.fill((15,27,33))
            def label(text,x,y,size=18):s.blit(font(size).render(text,True,(234,225,206)),(x,y))
            label('CLOCKWORK RUINS / OMARCHY CHARACTER',35,25,25)
            for i in range(6):s.blit(sprites.prop('wall',40,40,'default',i,3),(40+i*130,92))
            s.blit(sprites.prop('spikes',40,40,'default',frame%6,3),(862,92))
            s.blit(sprites.prop('lever',40,40,'broken' if frame%48>35 else 'default',min(4,frame%48//7),3),(1040,92))
            for i,state in enumerate(('walking','takeoff','falling','gliding','landing','hurt')):
                phase=frame%6 if state in ('landing','hurt','takeoff') else frame%16
                im=sprites.player(28,33,state,phase,3,'dhh');s.blit(im,im.get_rect(midbottom=(100+i*195,443)))
                label(state.title(),48+i*195,466)
            for i,side in enumerate((1,0,3,2)):
                x=65+i*220;y=559
                im=sprites.orient_spider(sprites.spider(40,40,'walking',frame%16,3),side)
                s.blit(im,(x,y))
                wall={1:(x,y+120,120,10),0:(x+120,y,10,120),3:(x,y-10,120,10),2:(x-10,y,10,120)}[side]
                pygame.draw.rect(s,(113,151,143),wall)
            bolt=sprites.prop('projectile',20,10,'default',frame%6,5);s.blit(bolt,(1000,600))
            label('F9: board-only play. Esc: pause. F10: settings.',35,746,20)
            return s
        encoder=subprocess.Popen(['ffmpeg','-loglevel','error','-y','-f','rawvideo','-pixel_format','rgb24','-video_size','1200x800','-framerate','24','-i','-','-an','-c:v','libx264','-crf','19','-pix_fmt','yuv420p','-movflags','+faststart',str(out/'visual-review.mp4')],stdin=subprocess.PIPE)
        try:
            for frame in range(144):
                im=board(frame);encoder.stdin.write(pygame.image.tobytes(im,'RGB'))
                if frame==4:pygame.image.save(im,out/'materials-and-motion.png')
        finally:encoder.stdin.close()
        assert encoder.wait()==0
        a.screen='play';a.s['board_only']=True;a.set_theme('omarchy');costs=[]
        for tick in range(180):
            pygame.event.pump()
            start=time.perf_counter();a.session.step({'RIGHT':tick%80<40,'LEFT':tick%80>=40,'JUMP':tick%35==0});a.draw();costs.append((time.perf_counter()-start)*1000)
            if args.desktop:pygame.time.wait(10)
        report=dict(backend=pygame.display.get_driver(),viewport=list(a.display.viewport.size),window=a.display.screen.get_size(),median_ms=round(sorted(costs)[90],2),p95_ms=round(sorted(costs)[170],2))
        if args.desktop:
            clients=json.loads(subprocess.check_output(['hyprctl','clients','-j'],text=True))
            own=next(c for c in clients if c['pid']==os.getpid())
            report.update(tiled=not own['floating'],other_mapped_windows=sum(c.get('mapped',False) and c['pid']!=os.getpid() for c in clients))
            assert not own['floating'],'Board-only unexpectedly floated the game'
        report['note']='Scripted rendering diagnostic, not sustained performance or human playtesting.'
        (out/('native.json' if args.desktop else 'headless.json')).write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2));pygame.quit()
if __name__=='__main__':main()
