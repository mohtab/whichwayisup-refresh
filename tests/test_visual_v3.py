"""Board-only navigation and presentation-only scene depth regressions."""
import argparse
import os
import tempfile
import unittest
from types import SimpleNamespace
from unittest.mock import patch
os.environ.update(SDL_VIDEODRIVER='dummy',SDL_AUDIODRIVER='dummy')
import pygame
from refresh.app import App
from refresh import sprites,lighting

class VisualV3Tests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(prefix='wwisup-visual-test-')
        self.env=patch.dict(os.environ,WWISUP_USER_DIR=self.tmp.name);self.env.start()
        self.app=App(argparse.Namespace(theme='refresh',safe_window=True,play=False,stage=None,screen=None,smoke=None,screenshot=None))
        self.app.s['dialogue']=False;self.app.start_stage(self.app.catalog.stages[0])
    def tearDown(self):self.env.stop();self.tmp.cleanup()
    def key(self,key):self.app.event(pygame.event.Event(pygame.KEYDOWN,key=key,mod=0))
    def test_board_only_fits_tiled_shapes_without_resizing(self):
        a=self.app
        for size in ((360,900),(960,480),(600,600)):
            pygame.display.set_mode(size,pygame.RESIZABLE)
            with patch.object(a.display,'cycle_size') as resize,patch.object(a.display,'toggle') as fullscreen:
                if not a.s['board_only']:self.key(pygame.K_F9)
                a.draw();resize.assert_not_called();fullscreen.assert_not_called()
            self.assertEqual(a.display.screen.get_size(),size)
            self.assertEqual(a.display.viewport.size,(min(size),min(size)))
            self.assertEqual(a.ui.buttons,[])
            self.key(pygame.K_ESCAPE);a.draw()
            self.assertEqual(a.screen,'pause');self.assertIn('Resume',[b.label for b in a.ui.buttons])
            self.assertEqual(a.display.content_size,(1200,800))
            self.key(pygame.K_ESCAPE);a.draw();self.assertEqual(a.display.content_size,(1040,1040))
        self.key(pygame.K_F10);a.draw();self.assertEqual(a.screen,'settings')
        self.key(pygame.K_ESCAPE);self.key(pygame.K_ESCAPE)
        self.key(pygame.K_F9);self.assertFalse(a.s['board_only'])
    def test_dialogue_and_focus_loss_cannot_hide_a_blocked_run(self):
        a=self.app;a.s['board_only']=True;a.session.scene['dialogue']='A visible story message.'
        a.draw();self.assertEqual(a.display.content_size,(1200,800))
        a.session.scene['dialogue']=None;a.draw();self.assertEqual(a.display.content_size,(1040,1040))
        a.event(pygame.event.Event(pygame.WINDOWFOCUSLOST));a.draw()
        self.assertEqual(a.screen,'pause');self.assertEqual(a.display.content_size,(1200,800))
    def test_dhh_falling_animation_and_alpha(self):
        for state in ('walking','falling','landing','hurt'):
            frames=[sprites.player(28,33,state,p,2,'dhh') for p in (0,4)]
            self.assertNotEqual(pygame.image.tobytes(frames[0],'RGBA'),pygame.image.tobytes(frames[1],'RGBA'))
        for name in ('dhh-v2.png','clockwork-props-v1.png'):
            self.assertEqual(sprites.sheet(name).get_at((0,0)).a,0)
        wall=sprites.prop('wall',40,40,'default',0,2)
        self.assertEqual(wall.get_bounding_rect().size,(80,80))
    def test_lighting_does_not_mutate_assets_or_game(self):
        a=self.app;p=a.session.scene['player'];state=(p.x,p.y,p.life,a.session.tick,len(a.session.history))
        image=sprites.player(28,33,'default',0,2);original=pygame.image.tobytes(image,'RGBA')
        shaded=lighting.shade(image,3)
        self.assertEqual(original,pygame.image.tobytes(image,'RGBA'))
        self.assertEqual(image.get_bounding_rect(),shaded.get_bounding_rect())
        frames=[]
        for enabled in (False,True):
            a.s['depth']=enabled;frames.append(pygame.image.tobytes(a.painter.draw(a.session,a.theme,a.s,1),'RGB'))
        self.assertNotEqual(frames[0],frames[1]);self.assertEqual(state,(p.x,p.y,p.life,a.session.tick,len(a.session.history)))
    def test_support_gap_matches_all_four_solid_faces(self):
        spider=SimpleNamespace(rect=pygame.Rect(40,40,40,40),attached=0)
        for side,rect in ((0,(83,40,40,40)),(1,(40,83,40,40)),(2,(-3,40,40,40)),(3,(40,-3,40,40))):
            spider.attached=side;tile=SimpleNamespace(tileclass='wall',rect=pygame.Rect(rect))
            self.assertEqual(sprites.support_gap(spider,[tile]),4)

    def test_lever_activation_starts_a_single_motion_event(self):
        session=self.app.session
        lever=next(o for o in session.scene['objects'] if o.itemclass=='lever')
        lever.activate();session.step({})
        count,changed=session.motion.levers[id(lever)]
        self.assertEqual(count,1);self.assertEqual(changed,session.tick)
        for _ in range(6):session.step({})
        self.assertEqual(session.motion.levers[id(lever)],(count,changed))

if __name__=='__main__':unittest.main()
