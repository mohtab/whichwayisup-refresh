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
    out=ROOT/'docs/cyberpunk-review-v4';out.mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='wwisup-v3-review-') as scratch:
        os.environ['WWISUP_USER_DIR']=scratch
        a=App(argparse.Namespace(theme='cyberpunk',safe_window=True,play=False,stage=None,screen=None,smoke=None,screenshot=None))
        a.s['dialogue']=False;a.s['board_only']=True;a.s['smooth']=True;a.start_stage(a.catalog.stages[0])
        for _ in range(40):a.session.step({})
        a.draw();pygame.image.save(a.display.screen,out/'board-only.png')
        a.s['board_only']=False;a.draw();pygame.image.save(a.ui.surface,out/'cyberpunk-gameplay.png')
        a.set_theme('refresh');a.draw();pygame.image.save(a.ui.surface,out/'refresh-gameplay.png')
        a.open_settings();a.draw();pygame.image.save(a.ui.surface,out/'settings.png')
        a.show_help();a.draw();pygame.image.save(a.ui.surface,out/'shortcuts.png')
        a.set_theme('omarchy');a.screen='play';a.s['board_only']=True;a.draw();pygame.image.save(a.display.screen,out/'omarchy-logo.png')
        a.set_theme('cyberpunk')
        from refresh import branding
        def board(frame):
            s=pygame.Surface((1200,800));s.fill((10,10,27))
            def label(text,x,y,size=18):s.blit(font(size).render(text,True,(236,229,248)),(x,y))
            label('NEON CIRCUIT / CYBERPUNK SPRITE REVIEW',35,25,25)
            for i,kind in enumerate(('wall','spikes','bars','lever','blob','key','other_pants','cake')):
                art=sprites.prop(kind,40,40,'default',frame%6,3,'cyberpunk')
                s.blit(art,art.get_rect(center=(85+i*146,160)))
                label(kind.replace('other_pants','armor').title(),30+i*146,236,15)
            for i,state in enumerate(('walking','takeoff','falling','gliding','landing','hurt')):
                phase=frame%6 if state in ('landing','hurt','takeoff') else frame%16
                im=sprites.player(28,33,state,phase,3,'guy','cyberpunk');s.blit(im,im.get_rect(midbottom=(100+i*195,451)))
                label(state.title(),48+i*195,472)
            for i,side in enumerate((1,0,3,2)):
                x=45+i*205;y=564
                im=sprites.orient_spider(sprites.spider(40,40,'walking',frame%16,3,'cyberpunk'),side)
                s.blit(im,(x,y))
                wall={1:(x,y+120,120,6),0:(x+120,y,6,120),3:(x,y-6,120,6),2:(x-6,y,6,120)}[side]
                pygame.draw.rect(s,(68,239,228),wall)
            bolt=sprites.prop('projectile',20,10,'default',frame%6,4,'cyberpunk');s.blit(bolt,(870,610))
            logo=branding.collectible(40,40,frame%32,3);s.blit(logo,(1035,560))
            label('Omarchy emblem',1002,710,15)
            label('Distinct materials. Complete poses. Same collision rules.',35,756,18)
            return s
        encoder=subprocess.Popen(['ffmpeg','-loglevel','error','-y','-f','rawvideo','-pixel_format','rgb24','-video_size','1200x800','-framerate','24','-i','-','-an','-c:v','libx264','-crf','19','-pix_fmt','yuv420p','-movflags','+faststart',str(out/'visual-review.mp4')],stdin=subprocess.PIPE)
        try:
            for frame in range(144):
                im=board(frame);encoder.stdin.write(pygame.image.tobytes(im,'RGB'))
                if frame==4:pygame.image.save(im,out/'cyberpunk-and-logo.png')
        finally:encoder.stdin.close()
        assert encoder.wait()==0
        a.screen='play';a.s['board_only']=True;a.set_theme('cyberpunk');costs=[]
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
