#!/usr/bin/env python3
"""Exercise presentation/navigation over time using an isolated user directory.

Example: python tools/release_soak.py --duration 120 --output /tmp/soak.json
Add --desktop to exercise the active SDL desktop backend (opens one window).
This diagnostic does not verify campaign completion or physical device behavior.
"""
import argparse
from collections import Counter
import hashlib
import json
import math
import os
from pathlib import Path
import statistics
import sys
import tempfile
import time
import traceback

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))


def source_digest():
    digest=hashlib.sha256()
    for path in sorted((ROOT/'refresh').glob('*.py')):
        digest.update(path.name.encode());digest.update(path.read_bytes())
    return digest.hexdigest()


def rss_mib():
    """Current resident pages, not the monotonically increasing RSS high-water mark."""
    try:return int(Path('/proc/self/statm').read_text().split()[1])*os.sysconf('SC_PAGE_SIZE')/1024**2
    except (OSError,ValueError,IndexError):return None


def distribution(values):
    if not values:return {'samples':0}
    ordered=sorted(values)
    return {'samples':len(values),'median_ms':round(statistics.median(values),3),
            'p95_ms':round(ordered[math.ceil(.95*len(ordered))-1],3),'max_ms':round(ordered[-1],3)}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--duration',type=float,default=120,help='Wall-clock seconds; 120 or more covers repeated full cycles')
    parser.add_argument('--warmup',type=float,help='Seconds excluded from memory drift analysis (default half duration, capped at 60)')
    parser.add_argument('--fps',type=int,default=60,help='Target frame rate, including real pacing')
    parser.add_argument('--desktop',action='store_true',help='Open a desktop window using SDL auto-selection')
    parser.add_argument('--output',type=Path,help='JSON result path')
    args=parser.parse_args()
    if not math.isfinite(args.duration) or args.duration<=0:parser.error('--duration must be finite and positive')
    if args.fps<1 or args.fps>240:parser.error('--fps must be between 1 and 240')
    warmup=min(60,args.duration/2) if args.warmup is None else args.warmup
    if not math.isfinite(warmup) or not 0<=warmup<args.duration:parser.error('--warmup must be between zero and duration')
    output=args.output or ROOT/'docs/release-review'/('soak-desktop.json' if args.desktop else 'soak-headless.json')
    if not args.desktop:os.environ['SDL_VIDEODRIVER']='dummy'
    elif os.environ.get('SDL_VIDEODRIVER')=='dummy':os.environ.pop('SDL_VIDEODRIVER')
    if args.desktop and os.environ.get('WAYLAND_DISPLAY') and not os.environ.get('SDL_VIDEODRIVER'):
        os.environ['SDL_VIDEODRIVER']='wayland';os.environ['WWISUP_AUTO_WAYLAND']='1'
    os.environ['SDL_AUDIODRIVER']='dummy'
    os.environ['PYGAME_HIDE_SUPPORT_PROMPT']='1'
    initial_digest=source_digest()
    import pygame
    from refresh import __version__
    from refresh.app import App

    report={'schema':1,'version':__version__,'mode':'desktop' if args.desktop else 'headless',
            'requested_seconds':args.duration,'warmup_seconds':warmup,'target_fps':args.fps,
            'source_sha256_start':initial_digest,'started_utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),
            'limitations':['Synthetic input only; no physical controller, suspend/resume or multiple-monitor test.',
                          'Audio uses SDL dummy driver.','Movement and retries do not establish stage solvability.',
                          'Frame CPU work excludes pacing; headless timing does not measure desktop compositor performance.']}
    costs=[];intervals=[];memory=[];coverage=Counter();windows=set();themes=set();views=set()
    scenario_costs={};error=None;start=None;retries=0;transitions=0
    try:
        with tempfile.TemporaryDirectory(prefix='wwisup-release-soak-') as scratch:
            os.environ['WWISUP_USER_DIR']=scratch
            app=App(argparse.Namespace(theme='refresh',safe_window=True,play=False,stage=None,screen=None,smoke=None,screenshot=None))
            app.s.update(dialogue=False,sound=False,music=False,fps=args.fps)
            app.audio_player.apply(app.s)
            report.update(sdl_driver=pygame.display.get_driver(),pygame=pygame.version.ver,sdl=list(pygame.get_sdl_version()))
            clock=pygame.time.Clock();start=time.monotonic();last_sample=-1;last_scenario=-1;last_phase=-1
            choices=('refresh','cyberpunk','omarchy','original','system')
            shapes=((360,900),(960,480),(600,600),(1200,800),(800,533))
            campaign=[stage for stage in app.catalog.stages if stage.original]
            while app.running and time.monotonic()-start<args.duration:
                dt=clock.tick(args.fps)/1000;work=time.perf_counter();elapsed=time.monotonic()-start
                scenario=int(elapsed//6);phase=int(elapsed%6)
                for event in pygame.event.get():app.event(event)
                if scenario!=last_scenario:
                    name=choices[scenario%len(choices)];view=scenario%3
                    app.set_theme(name)
                    app.s.update(board_only=view!=0,compact_hud=view==1,smooth=bool(scenario%2),
                                 effects=bool(scenario%2),depth=True,integer_scale=bool(scenario%2))
                    pygame.display.set_mode(shapes[scenario%len(shapes)],pygame.RESIZABLE)
                    app.start_stage(campaign[scenario%len(campaign)])
                    themes.add(name);views.add(('full','compact','board')[view])
                    windows.add(pygame.display.get_surface().get_size());last_scenario=scenario;last_phase=-1
                    scenario_costs[scenario]={'theme':name,'view':('full','compact','board')[view],'costs':[]}
                if phase!=last_phase:
                    if phase==3:app.pause();coverage['pause_calls']+=1
                    elif phase==4:
                        app.settings_tab=('Display','Audio','Controls','Gameplay','Advanced')[scenario%5]
                        app.settings_screen('pause');coverage['settings_visits']+=1
                    elif phase==5:
                        app.back();app.resume();coverage['resume_calls']+=1
                    transitions+=1;last_phase=phase
                if app.screen=='play':
                    app.held={pygame.K_RIGHT if int(elapsed)%4<2 else pygame.K_LEFT}
                    if int(elapsed*3)%3==0:app.held.add(pygame.K_SPACE);app.pending.add('jump')
                    if int(elapsed*2)%5==0:app.pending.add('interact')
                app.update(dt);app.draw()
                coverage['frames_'+app.screen]+=1
                if app.screen in ('lost','complete','ending') and phase<3:
                    app.restart();retries+=1
                cost=(time.perf_counter()-work)*1000
                costs.append(cost);intervals.append(dt*1000);scenario_costs[scenario]['costs'].append(cost)
                if int(elapsed)!=last_sample:
                    memory.append({'seconds':round(elapsed,3),'rss_mib':rss_mib()});last_sample=int(elapsed)
                    if last_sample and last_sample%30==0:
                        print(json.dumps({'progress_seconds':last_sample,'frames':len(costs),'rss_mib':memory[-1]['rss_mib']}),flush=True)
            report['elapsed_seconds']=round(time.monotonic()-start,3)
            report['completed_requested_duration']=time.monotonic()-start>=args.duration
    except Exception:
        error=traceback.format_exc();report['error']=error
        if start is not None:report['elapsed_seconds']=round(time.monotonic()-start,3)
    finally:
        pygame.quit()
        report.update(cpu_work=distribution(costs),frame_interval=distribution(intervals),memory_samples=memory,
                      coverage=dict(coverage),themes=sorted(themes),views=sorted(views),window_sizes=sorted(windows),
                      natural_result_retries=retries,phase_transitions=transitions,source_sha256_end=source_digest())
        report['source_changed_during_run']=report['source_sha256_end']!=initial_digest
        if costs:
            report['cpu_frames_over_target_budget']=sum(cost>1000/args.fps for cost in costs)
            report['achieved_frames_per_second']=round(len(costs)/max(.001,report.get('elapsed_seconds',args.duration)),2)
        report['scenarios']=[dict(index=index,theme=row['theme'],view=row['view'],cpu_work=distribution(row['costs'])) for index,row in scenario_costs.items()]
        steady=[row for row in memory if row['seconds']>=warmup and row['rss_mib'] is not None]
        if len(steady)>=4:
            count=max(1,len(steady)//5)
            early=statistics.median(row['rss_mib'] for row in steady[:count]);late=statistics.median(row['rss_mib'] for row in steady[-count:])
            report['post_warmup_memory']={'samples':len(steady),'early_median_mib':round(early,2),'late_median_mib':round(late,2),
                'median_delta_mib':round(late-early,2),'range_mib':round(max(row['rss_mib'] for row in steady)-min(row['rss_mib'] for row in steady),2),
                'interpretation':'Compare repeated runs and longer durations; finite sampling cannot prove absence of leaks.'}
        output.parent.mkdir(parents=True,exist_ok=True);output.write_text(json.dumps(report,indent=2)+'\n')
        print(json.dumps({'output':str(output),'elapsed_seconds':report.get('elapsed_seconds'),
                          'cpu_work':report['cpu_work'],'post_warmup_memory':report.get('post_warmup_memory'),
                          'source_changed_during_run':report['source_changed_during_run'],'error':error},indent=2))
    return 0 if not error and report.get('completed_requested_duration') else 1


if __name__=='__main__':raise SystemExit(main())
