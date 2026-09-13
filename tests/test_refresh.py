import os
os.environ['SDL_VIDEODRIVER']='dummy'
os.environ['SDL_AUDIODRIVER']='dummy'
import tempfile
TEST_ROOT=tempfile.TemporaryDirectory(prefix='wwisup-tests-')
os.environ['WWISUP_USER_DIR']=TEST_ROOT.name
import unittest
from pathlib import Path
from copy import deepcopy
from unittest.mock import patch
import math
import random
import json
import pygame
pygame.display.init();pygame.font.init();pygame.display.set_mode((1200,800));pygame.mixer.init()
from refresh import stages
from refresh.runtime import Session, Stepper
from refresh.storage import DEFAULTS, Store, atomic_json
from refresh.themes import Themes, color, contrast
from refresh.art import Painter
from refresh.editor import Editor
from level import Level
from frame import sprite
from animation import definition

SETTINGS=dict(DEFAULTS,sound=False,dialogue=False)

class ContentTests(unittest.TestCase):
    def test_all_original_stage_roundtrips(self):
        catalog=stages.Catalog()
        for stage in catalog.stages[:15]:
            with self.subTest(stage=stage.id):
                path=Path(TEST_ROOT.name)/(stage.id+'.txt')
                path.write_text(stages.legacy(stage.document))
                d=stages.parse_legacy(path)
                self.assertEqual(d['tiles'],stage.document['tiles'])
                self.assertEqual(d['events'],stage.document['events'])
                self.assertEqual(sorted(d['entities'],key=str),sorted(stage.document['entities'],key=str))
    def test_untrusted_content(self):
        for value in ('../escape','/tmp/escape','x\ny'):
            d=stages.blank();d['id']=value
            with self.assertRaises(stages.StageError):stages.validate(d)
        for change in ({'x':math.nan},{'x':math.inf},{'x':20},{'x':True},{'type':'python'}):
            d=stages.blank();d['entities'][0].update(change)
            with self.assertRaises(stages.StageError):stages.validate(d)
        d=stages.blank();d['events'][0]['actions']=['python import os']
        with self.assertRaises(stages.StageError):stages.validate(d)
        d=stages.blank();d['tiles'][0]='short'
        with self.assertRaises(stages.StageError):stages.validate(d)
    def test_editor_undo_rotation_save_import(self):
        e=Editor();before=deepcopy(e.document)
        e.paint((36+10*28+1,154+16*28+1));self.assertNotEqual(e.document,before)
        e.go_undo();self.assertEqual(e.document,before)
        e.go_redo();e.go_undo()
        for _ in range(4):e.rotate()
        self.assertEqual(e.document,before)
        path=e.save();self.assertEqual(stages.read(path),e.document)
        export=e.export();target=stages.import_stage(export)
        self.assertTrue(target.exists());self.assertEqual(stages.read(target),e.document)
    def test_save_corruption_and_separation(self):
        s=Store();atomic_json(s.path,{'tempo':999,'fps':0,'window':['bad'],'sound':'yes'})
        checked=Store()
        self.assertEqual(checked.settings['tempo'],1.)
        self.assertEqual(checked.settings['fps'],60)
        self.assertIs(checked.settings['sound'],True)
        self.assertNotIn('.wwisup',str(checked.path))

class RuntimeTests(unittest.TestCase):
    def test_rate_independence_and_tempo(self):
        for tempo in (.75,1.,1.25,1.5):
            totals=[]
            for fps in (30,60,120,144,240):
                s=Stepper();ticks=sum(s.advance(1/fps,tempo) for _ in range(fps*10))
                totals.append(ticks)
            self.assertEqual(totals,[round(240*tempo)]*5)
        clock=Stepper();self.assertEqual(clock.advance(2),0);self.assertTrue(clock.overrun)
    def test_scene_outcome_independent_of_refresh(self):
        path=stages.materialize(stages.blank());outcomes=[]
        for fps in (30,60,144,240):
            session=Session(path,SETTINGS);clock=Stepper()
            for _ in range(fps*5):
                for tick in range(clock.advance(1/fps)):
                    session.step({'RIGHT':True,'JUMP':session.tick%25==0,'UP':session.tick%25<10})
            p=session.scene['player']
            outcomes.append((p.x,p.y,p.life,session.score.time,session.tick))
        self.assertEqual(outcomes,[outcomes[0]]*len(outcomes))
    def test_complete_user_stage_through_real_trigger(self):
        d=stages.blank();d['entities'][1]['x']=10.5
        s=Session(stages.materialize(d),SETTINGS)
        for _ in range(400):
            s.step({'RIGHT':True,'DOWN':True})
            if s.result is not None:break
        self.assertEqual(s.result,3)
        self.assertEqual(s.score.levels,1)
    def test_original_stages_and_rotations(self):
        for stage in stages.Catalog().stages[:15]:
            with self.subTest(stage=stage.id):
                s=Session(stage.engine_path,SETTINGS)
                for i in range(160):
                    s.step({'SPECIAL':i in (30,110),'RIGHT':i%80<40,'JUMP':i%20==0,'UP':i%20<8})
                    if s.result is not None:break
                self.assertIsNotNone(s.scene)
                self.assertTrue(math.isfinite(s.scene['player'].x))
    def test_spatial_matches_full_scan(self):
        rng=random.Random(2)
        for stage in stages.Catalog().stages[:15]:
            level=Level(pygame.display.get_surface(),stage.engine_path)
            for rotation in range(4):
                for i in range(80):
                    rect=pygame.Rect(rng.randrange(520),rng.randrange(520),rng.randrange(10,50),rng.randrange(10,50))
                    dx,dy=rng.uniform(-15,15),rng.uniform(-20,20)
                    actual=level.collide(rect,dy,dx)
                    with patch.object(level,'candidates',return_value=level.active_tiles):expected=level.collide(rect,dy,dx)
                    self.assertEqual(actual,expected,(stage.id,rotation,rect))
                    x,y=rng.uniform(0,520),rng.uniform(0,520)
                    self.assertEqual(level.ground_check(x,y),any(t.rect.collidepoint(x,y) for t in level.active_tiles))
                level.flip()
                for _ in range(32):level.update()
    def test_theme_rendering_never_changes_physics(self):
        s=Session(stages.materialize(stages.blank()),SETTINGS)
        for _ in range(30):s.step({})
        painter=Painter();themes=Themes()
        objects=s.entities()
        before=[(o.x,o.y,getattr(o,'rect',None).copy() if hasattr(o,'rect') else None) for o in objects]
        for ident in ('original','refresh','omarchy','system','cyberpunk'):
            settings=dict(SETTINGS,theme=ident)
            for _ in range(5):painter.draw(s,themes.get(settings),settings,.5)
        after=[(o.x,o.y,getattr(o,'rect',None).copy() if hasattr(o,'rect') else None) for o in objects]
        self.assertEqual(before,after)
    def test_asset_cache_stays_warm(self):
        path=stages.materialize(stages.blank())
        Session(path,SETTINGS)
        with patch('pygame.image.load',side_effect=AssertionError('Unexpected warm image load')):
            s=Session(path,SETTINGS)
            for _ in range(30):s.step({})

class ThemeTests(unittest.TestCase):
    def test_theme_manifest_export(self):
        t=Themes()
        for pack in t.packs.values():
            self.assertGreaterEqual(contrast(pack.readable(pack['panel']),pack['panel']),4.5)
        p=t.export(t.get(SETTINGS));self.assertTrue(p.exists())
        self.assertEqual(t.read(p).palette,t.get(SETTINGS).palette)
        with self.assertRaises(ValueError):color('red')

if __name__=='__main__':unittest.main()
