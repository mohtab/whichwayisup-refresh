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
 def test_exit_keeps_head_torso_and_boots_at_standing_scale(self):
  from refresh import sprites
  source,_=sprites.source_frame('explorer-v1.png',6,4,17)
  regions=((45,0,112,98),(88,110,30,40),(45,190,112,45))
  source_bytes=pygame.image.tobytes(source,'RGBA')
  for phase in range(16):
   pose,_=sprites.exit_frame(phase)
   for region in regions:
    for x in range(region[0],region[0]+region[2]):
     for y in range(region[1],region[1]+region[3]):
      if source.get_at((x,y)).a>=96:self.assertEqual(source.get_at((x,y)),pose.get_at((x,y)),(phase,x,y))
   for scale in (1,2,3):
    stand=sprites.player(28,33,'default',0,scale)
    raised=sprites.player(28,33,'exit',phase,scale)
    self.assertEqual(stand.get_size(),raised.get_size())
    a=stand.get_bounding_rect(min_alpha=96);b=raised.get_bounding_rect(min_alpha=96)
    self.assertEqual((a.top,a.bottom),(b.top,b.bottom))
    self.assertGreater(b.left,0);self.assertLess(b.right,raised.get_width())
  self.assertEqual(source_bytes,pygame.image.tobytes(source,'RGBA'))
 def test_terminal_actor_cannot_overpaint_real_solids(self):
  from refresh import lighting
  a=self.app();a.start_stage(a.catalog.stages[0]);s=a.session
  frames=json.loads((ROOT/'docs/campaign-acceptance/replays/w0-l0.json').read_text())['inputs']
  for f in frames[:1030]:s.step(f)
  self.assertEqual(s.scene['player'].current_animation,'exit')
  real_sprite=a.painter.sprite
  def without_player(kind,*args,**kwargs):
   im=real_sprite(kind,*args,**kwargs)
   return pygame.Surface(im.get_size(),pygame.SRCALPHA) if kind=='player' else im
  # Isolate the body from the deliberately separate contact shadow.
  with patch.object(lighting,'shadow',side_effect=lambda im:pygame.Surface(im.get_size(),pygame.SRCALPHA)):
   for alpha in (0,.25,.5,.75,1):
    actual=a.painter.draw(s,a.theme,a.s,alpha).copy()
    with patch.object(a.painter,'sprite',side_effect=without_player):empty=a.painter.draw(s,a.theme,a.s,alpha).copy()
    # Compare both subtraction directions using the runtime dependency alone.
    # RGB-only surfaces keep unused native display alpha out of the comparison.
    actual_rgb=pygame.image.frombytes(pygame.image.tobytes(actual,'RGB'),actual.get_size(),'RGB')
    empty_rgb=pygame.image.frombytes(pygame.image.tobytes(empty,'RGB'),empty.get_size(),'RGB')
    difference=actual_rgb.copy();difference.blit(empty_rgb,(0,0),special_flags=pygame.BLEND_RGB_SUB)
    reverse=empty_rgb.copy();reverse.blit(actual_rgb,(0,0),special_flags=pygame.BLEND_RGB_SUB)
    difference.blit(reverse,(0,0),special_flags=pygame.BLEND_RGB_ADD)
    mask=pygame.Surface(actual.get_size());mask.fill((0,0,0))
    for tile in s.scene['level'].tiles:
     if tile.tileclass in ('wall','bars'):pygame.draw.polygon(mask,(255,255,255),[(x*2,y*2) for x,y in s.rules.geometry(tile,alpha)])
    difference.blit(mask,(0,0),special_flags=pygame.BLEND_RGB_MULT)
    self.assertFalse(any(pygame.image.tobytes(difference,'RGB')))
 def test_mount_contacts_rotating_union_continuously(self):
  from refresh import objects
  from refresh.enhanced import closest
  s=self.session(ENHANCED)
  for _ in range(40):s.step({})
  for direction in (1,-1,-1):
   level=s.scene['level'];level.flip(direction)
   for o in s.scene['objects']:o.flip(direction)
   previous={}
   for tick in range(33):
    s.step({})
    for alpha in (0,.25,.5,.75,1):
     polygons=[s.rules.geometry(t,alpha) for t in level.tiles if t.tileclass in ('wall','bars')]
     for lever in (o for o in s.scene['objects'] if o.itemclass=='lever'):
      x,y=s.position(lever,alpha)
      if x < -60 or y < -80 or x>580 or y>580:continue
      pivot=(x,y+lever.rect.h*.20)
      mount=objects.lever_mount((x,y),lever.rect.h,[s.rules.base[id(t)] for t in level.tiles if t.tileclass in ('wall','bars')],s.rules.material_matrix(alpha))
      self.assertIsNotNone(mount,(direction,tick,alpha,pivot))
      self.assertLess(min(math.dist(mount,closest(mount,p)) for p in polygons),1e-6)
      if id(lever) in previous:self.assertLess(math.dist(mount,previous[id(lever)]),9,(direction,tick,alpha,pivot,mount,previous[id(lever)]))
      previous[id(lever)]=mount
 def test_enhanced_lever_removes_slab_without_mutating_source(self):
  from refresh import objects,sprites
  source=sprites.prop('lever',40,40,'default',0,2);raw=pygame.image.tobytes(source,'RGBA')
  body=objects.lever_body(source)
  self.assertEqual(raw,pygame.image.tobytes(source,'RGBA'))
  self.assertEqual(pygame.mask.from_surface(body).overlap_area(pygame.mask.Mask((80,9),fill=True),(0,71)),0)
  self.assertGreater(pygame.mask.from_surface(body).count(),100)
 def test_switch_gearbox_has_no_second_rectangular_pedestal(self):
  from refresh import objects,sprites
  for style in ('refresh','cyberpunk'):
   for state in ('default','broken'):
    for phase in range(5):
     source=sprites.prop('lever',40,40,state,phase,2,style)
     before=pygame.image.tobytes(source,'RGBA')
     body=objects.lever_body(source,style)
     # This lower corner formerly survived the rectangular pedestal cuts.
     self.assertEqual(body.get_at((21,67)).a,0,(style,state,phase))
     hub_y=round(80*(.60 if style=='cyberpunk' else .67))
     self.assertEqual(pygame.image.tobytes(body.subsurface((0,0,80,hub_y)),'RGBA'),pygame.image.tobytes(source.subsurface((0,0,80,hub_y)),'RGBA'))
     self.assertEqual(pygame.image.tobytes(source,'RGBA'),before)
