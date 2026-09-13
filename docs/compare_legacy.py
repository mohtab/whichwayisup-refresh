"""Read-only trace comparison against a supplied pre-refresh checkout."""
import os
os.environ['SDL_VIDEODRIVER']='dummy';os.environ['SDL_AUDIODRIVER']='dummy'
import sys,random,json
from pathlib import Path
root=Path(sys.argv[1]);sys.path.insert(0,str(root/'lib'))
import pygame,game
from variables import Variables
pygame.display.init();pygame.mixer.init();screen=pygame.display.set_mode((520,520))
Variables.vdict.update(devmode=False,sound=False,dialogue=False,verbose=False)
frames=0;rows=[]
class Clock:
 def tick(self,fps):
  global frames
  caller=sys._getframe(1).f_locals
  if 'simulation' in caller:caller=caller['simulation'].gi_frame.f_locals
  p=caller['player']
  rows.append([frames,round(p.x,6),round(p.y,6),p.life,caller['score'].time,caller['level'].orientation])
  frames+=1
  if frames>=220:pygame.event.post(pygame.event.Event(pygame.QUIT))
  return 42
pygame.time.Clock=Clock
def inputs(joystick=None):
 return ({'RIGHT':True} if frames%80<40 else {'LEFT':True}) | ({'JUMP':True,'UP':True} if frames%30==0 else {}) | ({'SPECIAL':True} if frames in (50,150) else {})
game.parse_inputs=inputs
random.seed(0)
game.run(screen,'w0-l0')
Path(sys.argv[2]).write_text(json.dumps(rows))
