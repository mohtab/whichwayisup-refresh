"""Headless same-state turn benchmark; explicitly not native frame-pacing evidence."""
import argparse,cProfile,io,json,os,pathlib,pstats,statistics,sys,tempfile,time
p=argparse.ArgumentParser();p.add_argument('--game',type=pathlib.Path,default=pathlib.Path(__file__).resolve().parents[1]);p.add_argument('--out',type=pathlib.Path,required=True);args=p.parse_args()
os.environ.update(SDL_VIDEODRIVER='dummy',SDL_AUDIODRIVER='dummy');sys.path.insert(0,str(args.game.resolve()))
from refresh.app import App
with tempfile.TemporaryDirectory(prefix='terrain-profile-') as profile:
 os.environ['WWISUP_USER_DIR']=profile;a=App(argparse.Namespace(theme='refresh',safe_window=True,play=False,stage=None,screen=None,smoke=None,screenshot=None));a.s.update(dialogue=False);a.start_stage(a.catalog.stages[0]);s=a.session
 for _ in range(40):s.step({})
 a.draw();rows=[];profiler=cProfile.Profile();profiler.enable()
 for direction in (1,-1,-1):
  s.scene['level'].flip(direction)
  for o in s.scene['objects']:o.flip(direction)
  for tick in range(31):
   s.step({})
   for alpha in (.13,.57,.93):
    start=time.perf_counter();a.painter.draw(s,a.theme,a.s,alpha);rows.append((time.perf_counter()-start)*1000)
  s.step({})
 profiler.disable();stream=io.StringIO();pstats.Stats(profiler,stream=stream).sort_stats('cumtime').print_stats(30)
 args.out.mkdir(parents=True,exist_ok=True);(args.out/'profile.txt').write_text(stream.getvalue())
 (args.out/'timing.json').write_text(json.dumps(dict(method='Headless Painter.draw; three turns,31ticks each, three exact interpolation samples per tick; cProfile enabled. No present or native pacing measurement.',frames=len(rows),median_ms=statistics.median(rows),p95_ms=sorted(rows)[int(.95*(len(rows)-1))],samples_ms=rows),indent=2))
 print(json.dumps(dict(frames=len(rows),median_ms=statistics.median(rows))))
