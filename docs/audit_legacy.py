import os
os.environ['SDL_VIDEODRIVER'] = 'dummy'
os.environ['SDL_AUDIODRIVER'] = 'dummy'
import argparse
parser = argparse.ArgumentParser()
parser.add_argument("--prefix", default="refresh")
args = parser.parse_args()
import sys, tempfile, cProfile, pstats, io, json, random, time
from pathlib import Path
root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(root / 'lib'))
import pygame, util, game
from variables import Variables
pygame.display.init()
screen = pygame.display.set_mode((520,520))
pygame.mixer.init()
frames = 0
class FastClock:
    def tick(self, fps):
        global frames
        frames += 1
        if frames >= 240:
            pygame.event.post(pygame.event.Event(pygame.QUIT))
        if frames > 300:
            raise RuntimeError('frame guard exceeded')
        return 42
pygame.time.Clock = FastClock
def scripted_inputs(joystick=None):
    inputs = {'ANALOG': 1.0}
    if frames % 80 < 40: inputs['RIGHT'] = True
    else: inputs['LEFT'] = True
    if frames % 30 == 0: inputs['JUMP'] = True
    if frames % 30 < 10: inputs['UP'] = True
    if frames in (50, 150): inputs['SPECIAL'] = True
    return inputs
game.parse_inputs = scripted_inputs
levels=[]
for world in game.WORLDS:
    levels += [line.split()[1] for line in (root/'data/levels'/f'{world}.txt').read_text().splitlines() if line.startswith('level ')]
load_count = 0
original_load = pygame.image.load
def counted_load(*args, **kwargs):
    global load_count
    load_count += 1
    return original_load(*args, **kwargs)
pygame.image.load = counted_load
prof = cProfile.Profile()
rows=[]
with tempfile.TemporaryDirectory(prefix='wwisup-plan-') as config:
    util.get_config_path = lambda: config
    util.parse_config()
    Variables.vdict.update(sound=False, dialogue=False, devmode=False)
    for name in levels:
        frames=0
        pygame.event.clear()
        random.seed(0)
        before=load_count
        started=time.perf_counter()
        try:
            result=prof.runcall(game.run, screen, name)
            rows.append(dict(level=name, frames=frames, exit=result, seconds=round(time.perf_counter()-started,4), image_loads=load_count-before))
        except Exception as e:
            rows.append(dict(level=name, frames=frames,error=repr(e)))
report = {'method':'Headless SDL dummy video/audio; capped at 240 loop iterations per stage; clock sleep removed; synthetic movement/jumps and debug rotations at iterations 50/150; fixed random seed. No completed-playthrough or actual display-performance claim.', 'python':sys.version, 'pygame':pygame.version.ver, 'levels':rows, 'image_loads':load_count, 'game_log':Variables.vdict.get('log','')}
(root/'docs'/f'{args.prefix}-audit.json').write_text(json.dumps(report,indent=2)+'\n')
buffer=io.StringIO()
pstats.Stats(prof,stream=buffer).strip_dirs().sort_stats('cumulative').print_stats(30)
(root/'docs'/f'{args.prefix}-profile.txt').write_text(buffer.getvalue())
print(json.dumps(report,indent=2))
print(buffer.getvalue())
pygame.quit()
