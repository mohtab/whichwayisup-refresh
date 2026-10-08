"""Independent contracts for isolated run rules, connected terrain and swept shots."""
import argparse,json,math,os,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
os.environ.update(SDL_VIDEODRIVER='dummy',SDL_AUDIODRIVER='dummy')
import pygame
from refresh.runtime import Session
from refresh.storage import DEFAULTS
from refresh.rules import LEGACY,ENHANCED
from refresh.enhanced import corners,matrix,sweep
from refresh import runs,stages
from refresh.app import App
ROOT=Path(__file__).resolve().parents[1]

class EnhancedTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.env=patch.dict(os.environ,WWISUP_USER_DIR=self.tmp.name);self.env.start();pygame.init();pygame.display.set_mode((1,1))
 def tearDown(self):self.env.stop();self.tmp.cleanup()
 def session(self,rules=LEGACY):return Session('w0-l0',dict(DEFAULTS,sound=False,dialogue=False),rules=rules)
 def app(self):
  a=App(argparse.Namespace(theme='refresh',safe_window=True,play=False,stage=None,screen=None,smoke=None,screenshot=None));a.s.update(dialogue=False,sound=False);return a
 def test_fast_finite_body_and_misses(self):
  wall=corners(110,50,20,100)
  hit=sweep(corners(0,50,20,8),corners(200,50,20,8),wall,wall)
  self.assertAlmostEqual(hit[0],.45,places=6);self.assertAlmostEqual(hit[1][0],100)
  self.assertIsNone(sweep(corners(0,105,20,8),corners(200,105,20,8),wall,wall))
  self.assertIsNotNone(sweep(corners(0,103.9,20,8),corners(200,103.9,20,8),wall,wall))
 def test_rotating_surface_contacts_body_without_invisible_corner(self):
  a=corners(146,120,4,4);b0=corners(120,120,40,40);b1=corners(120,120,40,40,matrix(math.pi/4))
  hit=sweep(a,a,b0,b1);self.assertIsNotNone(hit);self.assertGreater(hit[0],0);self.assertLess(hit[0],1)
  miss=corners(147,147,2,2);self.assertIsNone(sweep(miss,miss,b0,b1))
 def test_wall_player_earliest_contact_and_shielding(self):
  from types import SimpleNamespace
  from projectile import Projectile
  from refresh.enhanced import EnhancedRules
  for px,expect_damage in ((160,False),(60,True)):
   s=self.session(ENHANCED);r=s.rules;p=r.player;p.x=px;p.y=100;p.rect.center=(px,100);r.player_previous=(px,100)
   tile=SimpleNamespace(tileclass='wall',x=110,y=100,rect=pygame.Rect(100,50,20,100))
   r.level.tiles=[tile];r.base={};r.level.orientation=0;r.level.flipping=False;r.after_terrain();r.previous_polygons=r.polygons.copy()
   shot=Projectile(s.canvas,0,100,200,0);shot.x=20;shot.active=True;life=p.life;r.update_projectile(shot)
   self.assertEqual(p.life<life,expect_damage);self.assertEqual(shot.current_animation,'dying');self.assertLess(shot.x,px)
   if not expect_damage:self.assertAlmostEqual(shot.impact_point[0],100,places=5);self.assertAlmostEqual(shot.x,90,places=5)
   pos=(shot.x,shot.y);r.update_projectile(shot);self.assertEqual((shot.x,shot.y),pos)
 def test_three_turns_both_directions_centers_and_last_interval(self):
  s=self.session(ENHANCED)
  for _ in range(40):s.step({})
  for direction in (1,-1,-1):
   level=s.scene['level'];level.flip(direction)
   for o in s.scene['objects']:o.flip(direction)
   for tick in range(31):
    s.step({})
    for tile in level.tiles:
     if tile.tileclass=='spikes':continue
     for alpha in (0,.25,.5,1):
      poly=s.rules.geometry(tile,alpha);center=tuple(sum(p[i] for p in poly)/4 for i in (0,1));expected=s.position(tile,alpha)
      self.assertAlmostEqual(center[0],expected[0],places=7);self.assertAlmostEqual(center[1],expected[1],places=7)
   self.assertFalse(level.flipping);self.assertNotEqual(s.rules.previous_matrix,s.rules.current_matrix)
   endpoint=s.rules.current_matrix;s.step({});self.assertEqual(s.rules.previous_matrix,endpoint)
 def test_default_old_replay_and_distinct_storage(self):
  s=self.session();self.assertEqual(s.rules_id,LEGACY)
  path=ROOT/'docs/campaign-acceptance/replays/w0-l0.json';payload=json.loads(path.read_text());document=stages.parse_legacy(ROOT/'data/levels/w0-l0.txt')
  payload.pop('rules');self.assertTrue(runs.verify(payload,document,DEFAULTS)['verified_locally'])
  self.assertNotEqual(runs.record_key(document,1,False,LEGACY),runs.record_key(document,1,False,ENHANCED))
  with self.assertRaises(AttributeError):s.rules_id=ENHANCED
 def test_interleaved_sessions_do_not_leak(self):
  frames=json.loads((ROOT/'docs/campaign-acceptance/replays/w0-l0.json').read_text())['inputs'][:400]
  baseline=self.session();expected=[]
  def state(s):return ([(o.x,o.y,getattr(o,'life',None),o.current_animation) for o in s.scene['objects']],s.random_state,s.score.time)
  for f in frames:baseline.step(f);expected.append(state(baseline))
  legacy=self.session();enhanced=self.session(ENHANCED)
  for f,want in zip(frames,expected):enhanced.step(f);legacy.step(f);self.assertEqual(state(legacy),want)
  again=self.session()
  for f in frames:again.step(f)
  self.assertEqual(state(again),expected[-1])
 def test_theme_pending_retry_and_original_start(self):
  a=self.app();a.start_stage(a.catalog.stages[0]);self.assertEqual(a.session.rules_id,ENHANCED)
  a.set_theme('original');a.draw();self.assertEqual(a.theme.id,'refresh');self.assertIn('Next stage',a.rules_notice())
  a.restart();self.assertEqual(a.session.rules_id,ENHANCED)
  a.start_stage(a.catalog.stages[0]);self.assertEqual(a.session.rules_id,LEGACY);self.assertEqual(a.theme.id,'original')
  a.set_theme('cyberpunk');a.draw();self.assertEqual(a.session.rules_id,LEGACY)
 def test_pickup_render_repeatability_and_nonmutation(self):
  a=self.app();a.start_stage(a.catalog.stages[0]);s=a.session
  frames=json.loads((ROOT/'docs/campaign-acceptance/replays/w0-l0.json').read_text())['inputs']
  for f in frames[:1031]:s.step(f)
  state=[(o.x,o.y,tuple(getattr(o,'rect',())),getattr(o,'current_animation',None)) for o in s.entities()];rng=s.random_state
  first=pygame.image.tobytes(a.painter.draw(s,a.theme,a.s,.5),'RGB');second=pygame.image.tobytes(a.painter.draw(s,a.theme,a.s,.5),'RGB')
  self.assertEqual(first,second);self.assertEqual(state,[(o.x,o.y,tuple(getattr(o,'rect',())),getattr(o,'current_animation',None)) for o in s.entities()]);self.assertEqual(rng,s.random_state)
 def test_all_menu_modes_focus_and_hitboxes(self):
  a=self.app()
  for theme in ('original','refresh','omarchy','system','cyberpunk'):
   a.route('home');a.set_theme(theme)
   for route in ('home','stages','records','settings','editor'):
    if route=='settings':a.settings_screen('home')
    elif route=='editor':a.new_editor()
    else:a.route(route)
    tabs=('Display','Gameplay','Advanced','Audio','Controls') if route=='settings' else (None,)
    for tab in tabs:
     if tab:a.settings_tab=tab
     a.draw();buttons=a.ui.buttons;self.assertTrue(buttons)
     for i,b in enumerate(buttons):
      self.assertTrue(a.ui.surface.get_rect().contains(b.rect),(theme,route,b.label,b.rect))
      for other in buttons[i+1:]:self.assertFalse(b.rect.colliderect(other.rect),(theme,route,b.label,other.label))
     a.ui.focus=0;a.ui.move(1);self.assertEqual(a.ui.focus,1%len(buttons))
