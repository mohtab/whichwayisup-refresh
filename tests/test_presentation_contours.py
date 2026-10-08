"""Connected boundary and content-sized interface contracts."""
import argparse,math,os,tempfile,unittest
from unittest.mock import patch
os.environ.update(SDL_VIDEODRIVER='dummy',SDL_AUDIODRIVER='dummy')
import pygame
from refresh import objects
from refresh.enhanced import corners,transform
from refresh.app import App
from refresh.ui_refresh import BOARD

class PresentationTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.env=patch.dict(os.environ,WWISUP_USER_DIR=self.tmp.name);self.env.start();pygame.init();pygame.display.set_mode((1,1))
 def tearDown(self):self.env.stop();self.tmp.cleanup()
 def test_connected_union_has_no_internal_edges_and_caches_across_rotation(self):
  solids=(corners(20,20,40,40),corners(60,20,40,40),corners(20,60,40,40))
  expected=objects.exposed_edges(solids)
  self.assertEqual(len(expected),6)
  for i in range(32):
   a=i*math.pi/62;m=(math.cos(a)*.9999,math.sin(a)*.9999)
   polygons=tuple(tuple(tuple(v*2 for v in transform(p,m)) for p in poly) for poly in solids)
   recovered=objects.canonical_solids(polygons,2,m)
   self.assertEqual(recovered,solids)
   self.assertEqual(objects.exposed_edges(recovered),expected)
 def test_boundary_material_preserves_exact_occupancy_through_turns(self):
  solids=(corners(120,120,40,40),corners(160,120,40,40))
  for angle in (0,.21,.77,1.57):
   m=(math.cos(angle),math.sin(angle))
   polygons=tuple(tuple(tuple(v*2 for v in transform(p,m)) for p in poly) for poly in solids)
   terrain,shadow=objects.terrain_layer((),(520,520),2,polygons,m)
   occupancy=pygame.Surface((520,520),pygame.SRCALPHA)
   for poly in polygons:pygame.draw.polygon(occupancy,(255,255,255),poly)
   self.assertEqual(pygame.mask.from_surface(terrain).count(),pygame.mask.from_surface(occupancy).count())
   self.assertEqual(pygame.mask.from_surface(terrain).overlap_area(pygame.mask.from_surface(occupancy),(0,0)),pygame.mask.from_surface(occupancy).count())
 def app(self):return App(argparse.Namespace(theme='refresh',safe_window=True,play=False,stage=None,screen=None,smoke=None,screenshot=None))
 def test_long_dialogue_controls_stay_in_group_and_outside_room(self):
  a=self.app();a.start_stage(a.catalog.stages[0]);a.session.scene['dialogue']='A measured line of dialogue. '*60
  a.dialogue_token=None
  with patch.object(a.ui,'panel',wraps=a.ui.panel) as panels:
   a.draw();group=pygame.Rect(panels.call_args_list[-1].args[0])
  self.assertEqual(tuple(a.world_layers[0][1]),BOARD)
  for b in a.ui.buttons:
   self.assertTrue(group.contains(b.rect));self.assertFalse(pygame.Rect(BOARD).colliderect(b.rect))
  self.assertLess(group.bottom,770)
 def test_records_zero_one_six_and_pagination_have_bounded_content(self):
  a=self.app();a.route('records')
  for count in (0,1,6,7):
   a.store.records={str(i):{'stage':str(i),'category':'1x:no-dialogue','best_seconds':40+i} for i in range(count)}
   a.records_page=0;a.draw()
   for b in a.ui.buttons:self.assertLessEqual(b.rect.bottom,752)
   back=next(b for b in a.ui.buttons if b.label=='Back')
   self.assertLess(back.rect.y,500 if count<2 else 715)
   if count==7:
    next(b for b in a.ui.buttons if b.label=='Next').action();a.draw()
    self.assertEqual(a.records_page,1);self.assertLess(next(b.rect.y for b in a.ui.buttons if b.label=='Back'),500)
 def test_system_card_metadata_has_body_size_and_foreground_contrast(self):
  a=self.app();a.set_theme('system');a.route('stages')
  with patch.object(a.ui,'text',wraps=a.ui.text) as text:
   a.draw()
  metadata=[c.args for c in text.call_args_list if str(c.args[0]).startswith(('QUEST FOR','Not yet','Enhanced gameplay'))]
  self.assertTrue(metadata)
  for args in metadata:
   self.assertGreaterEqual(args[3],16)
   from refresh.ui_refresh import card_secondary
   self.assertEqual(args[4],card_secondary(a.theme))
