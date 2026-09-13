"""Contact orientation and animation events must not change gameplay."""
import os
import tempfile
import unittest
from types import SimpleNamespace
from unittest.mock import patch
os.environ.update(SDL_VIDEODRIVER='dummy',SDL_AUDIODRIVER='dummy')
import pygame
from refresh import sprites,stages
from refresh.runtime import Session
from refresh.storage import DEFAULTS
from refresh.motion import Motion
from refresh.art import Painter
from refresh.themes import Themes

class SpriteMotionTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(prefix='wwisup-sprite-test-')
        self.env=patch.dict(os.environ,WWISUP_USER_DIR=self.tmp.name);self.env.start()
        pygame.display.init();pygame.font.init();pygame.display.set_mode((520,520))
        self.settings=dict(DEFAULTS,sound=False,dialogue=False)
    def tearDown(self):self.env.stop();self.tmp.cleanup()
    def session(self):return Session(stages.materialize(stages.blank()),self.settings)
    def test_feet_follow_support_in_all_four_orientations(self):
        marker=pygame.Surface((40,40),pygame.SRCALPHA);marker.set_at((20,39),(255,20,180,255))
        for side,point in ((0,(39,19)),(1,(20,39)),(2,(0,20)),(3,(19,0))):
            with self.subTest(side=side):
                image=sprites.orient_spider(marker,side)
                self.assertEqual(tuple(image.get_at(point)),(255,20,180,255))
                real=sprites.orient_spider(sprites.spider(40,40,'walking',0),side)
                bounds=real.get_bounding_rect(min_alpha=96)
                self.assertTrue({0:bounds.right==40,1:bounds.bottom==40,2:bounds.left==0,3:bounds.top==0}[side])
    def test_rotation_tracks_room_without_snapping(self):
        for direction in (1,-1):
            for side in range(4):
                start=sprites.spider_angle(side,1,True,direction,0)
                end=sprites.spider_angle(side,31,True,direction,1)
                self.assertAlmostEqual(start-end,direction*90)
                self.assertEqual(end,sprites.spider_angle(side))
                angles=[sprites.spider_angle(side,n,True,direction,.5) for n in range(1,32)]
                self.assertTrue(all(abs(a-b)<3 for a,b in zip(angles,angles[1:])))
    def test_actual_jump_landing_and_hit_events(self):
        session=self.session()
        for _ in range(35):session.step({})
        poses=[]
        session.step({'JUMP':True})
        for _ in range(32):
            p=session.scene['player'];poses.append(session.motion.pose(p,session.tick,session.driver.inputs)[0])
            session.step({})
        for name in ('takeoff','rising','apex','falling','landing'):
            self.assertIn(name,poses)
        self.assertGreater(session.motion.landing_speed,1)
        p=session.scene['player'];p.take_damage(5);session.step({})
        self.assertEqual(session.motion.pose(p,session.tick,{})[0],'hurt')
        hit=session.motion.hit
        for _ in range(9):session.step({})
        self.assertEqual(session.motion.hit,hit)
        self.assertNotEqual(session.motion.pose(p,session.tick,{})[0],'hurt')
    def test_animation_and_effects_leave_physics_and_replay_identical(self):
        a=self.session();b=self.session();b.motion=SimpleNamespace(observe=lambda *args:None)
        painter=Painter();themes=Themes()
        for tick in range(130):
            inputs={'RIGHT':True} if tick%70<35 else {'LEFT':True}
            if tick%27==0:inputs['JUMP']=True
            a.step(inputs);b.step(inputs)
            for effect in (True,False):
                setting=dict(self.settings,effects=effect)
                painter.draw(a,themes.get(setting),setting,.4)
            pa,pb=a.scene['player'],b.scene['player']
            self.assertEqual((pa.x,pa.y,pa.life,a.score.time),(pb.x,pb.y,pb.life,b.score.time))
        self.assertEqual(a.history,b.history)
    def test_crouches_preserve_scale_and_pause_freezes_pose(self):
        stand=sprites.player(28,33,'default',0).get_bounding_rect(min_alpha=96)
        land=sprites.player(28,33,'landing',2).get_bounding_rect(min_alpha=96)
        self.assertLess(land.height,stand.height*.8)
        self.assertEqual(stand.bottom,land.bottom)
        a=self.session();a.step({'JUMP':True});painter=Painter();theme=Themes().get(self.settings)
        before=(a.tick,a.motion.takeoff,a.motion.landing,a.motion.hit)
        frames=[pygame.image.tobytes(painter.draw(a,theme,self.settings,1).copy(),'RGB') for _ in range(3)]
        self.assertEqual(frames[0],frames[2]);self.assertEqual(before,(a.tick,a.motion.takeoff,a.motion.landing,a.motion.hit))
    def test_long_running_strides_do_not_clip(self):
        for scale in (1,2,3):
            for phase in range(16):
                art=sprites.player(28,33,'walking',phase,scale)
                bounds=art.get_bounding_rect(min_alpha=96)
                self.assertGreater(bounds.left,0)
                self.assertLess(bounds.right,art.get_width())
                self.assertGreater(bounds.top,0)
    def test_atlases_are_transparent_and_all_frames_have_art(self):
        for name,columns,rows in (('explorer-v1.png',6,4),('spider-v1.png',6,4),('compass-key-v1.png',4,4)):
            self.assertTrue(sprites.sheet(name).get_flags()&pygame.SRCALPHA)
            for index in range(columns*rows):
                frame,bounds=sprites.source_frame(name,columns,rows,index)
                self.assertGreater(bounds.width,50);self.assertGreater(bounds.height,50)
                self.assertLessEqual(bounds.width,sprites.sheet(name).get_width()/columns+1)

if __name__=='__main__':unittest.main()
