"""Exact material and complete-frame contracts for the optional optimization."""
import argparse,json,math,os,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
os.environ.update(SDL_VIDEODRIVER='dummy',SDL_AUDIODRIVER='dummy')
import pygame
from refresh import objects,terrain_sampler,lighting
from refresh.app import App
from refresh.art import Painter

class TerrainSamplerTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.env=patch.dict(os.environ,WWISUP_USER_DIR=self.tmp.name);self.env.start();pygame.init();pygame.display.set_mode((1,1))
 def tearDown(self):self.env.stop();self.tmp.cleanup()
 def test_material_all_quadrants_fractional_scales_and_edges(self):
  if terrain_sampler.kernel() is None:self.skipTest('optional compiler unavailable')
  for i in range(-100,101):
   angle=i*math.pi/49;z=1-(i%7)*.00007;m=(math.cos(angle)*z,math.sin(angle)*z)
   got=objects.attached_material((1040,1040),2,m)
   with patch.object(terrain_sampler,'material',return_value=None):want=objects.attached_material((1040,1040),2,m)
   self.assertEqual(pygame.image.tobytes(got,'RGB'),pygame.image.tobytes(want,'RGB'),i)
 def test_complete_frames_all_turn_ticks_both_directions_and_nonmutation(self):
  a=App(argparse.Namespace(theme='refresh',safe_window=True,play=False,stage=None,screen=None,smoke=None,screenshot=None));a.s.update(dialogue=False);a.start_stage(a.catalog.stages[0]);s=a.session
  for _ in range(40):s.step({})
  fast=Painter();slow=Painter()
  def state():
   return ([(o.x,o.y,tuple(o.rect),o.current_animation,getattr(o,'flipcounter',None),getattr(o,'life',None)) for o in (*s.scene['level'].tiles,*s.scene['objects'])],s.tick,s.random_state,s.score.time,dict(s.previous))
  def compare(alpha):
   before=state();fast.draw(s,a.theme,a.s,alpha)
   with patch.object(terrain_sampler,'material',return_value=None):slow.draw(s,a.theme,a.s,alpha)
   self.assertEqual(pygame.image.tobytes(fast.world,'RGB'),pygame.image.tobytes(slow.world,'RGB'),(s.tick,alpha))
   self.assertEqual(before,state())
  compare(.37)
  for direction in (1,-1,-1):
   s.scene['level'].flip(direction)
   for o in s.scene['objects']:o.flip(direction)
   for tick in range(31):
    s.step({})
    for alpha in (0,.137,.5,.913,1):compare(alpha)
   s.step({});compare(.57)
 def test_normal_pickup_and_terminal_frames(self):
  a=App(argparse.Namespace(theme='refresh',safe_window=True,play=False,stage=None,screen=None,smoke=None,screenshot=None));a.s.update(dialogue=False);a.start_stage(a.catalog.stages[0]);s=a.session
  inputs=json.loads((Path(__file__).resolve().parents[1]/'docs/campaign-acceptance/replays/w0-l0.json').read_text())['inputs']
  fast=Painter();slow=Painter()
  for frame in inputs:
   s.step(frame)
   if s.tick in (1,40,200,1025,1027,1028,1030,1035,1040,1060,1090):
    for alpha in (0,.137,.5,.913,1):
     before=(s.tick,s.random_state,[(o.x,o.y,o.current_animation) for o in s.scene['objects']])
     fast.draw(s,a.theme,a.s,alpha)
     with patch.object(terrain_sampler,'material',return_value=None):slow.draw(s,a.theme,a.s,alpha)
     self.assertEqual(pygame.image.tobytes(fast.world,'RGB'),pygame.image.tobytes(slow.world,'RGB'),(s.tick,alpha))
     self.assertEqual(before,(s.tick,s.random_state,[(o.x,o.y,o.current_animation) for o in s.scene['objects']]))
 def test_full_board_light_shortcut_matches_general_path(self):
  image=pygame.Surface((128,128),pygame.SRCALPHA)
  for y in range(128):
   pygame.draw.line(image,(y,255-y,y//2,y*2),(0,y),(127,y))
  field=pygame.Surface((128,128));field.fill((102,126,145));warm=field.copy();warm.fill((32,70,12))
  before=[pygame.image.tobytes(x,'RGBA') for x in (image,field,warm)]
  # Larger fields with identical sampled pixels force the original general path.
  large=pygame.Surface((130,130));large.blit(field,(0,0));large_warm=large.copy();large_warm.blit(warm,(0,0))
  for glow in (None,warm):
   fast=lighting.spatial_response(image,image.get_rect(),field,warm=glow)
   slow=lighting.spatial_response(image,image.get_rect(),large,warm=large_warm if glow else None)
   self.assertEqual(pygame.image.tobytes(fast,'RGBA'),pygame.image.tobytes(slow,'RGBA'))
  self.assertEqual(before,[pygame.image.tobytes(x,'RGBA') for x in (image,field,warm)])
 def test_portable_fallback(self):
  with patch.object(terrain_sampler,'kernel',return_value=None):
   self.assertIsNone(terrain_sampler.material(objects.material_source(2),(1040,1040),2,(.7,.7)))
