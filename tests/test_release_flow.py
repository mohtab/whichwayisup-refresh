"""Release regressions across devices, progression and large-board views."""
import argparse
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
os.environ.update(SDL_VIDEODRIVER='dummy',SDL_AUDIODRIVER='dummy')
import pygame
from refresh.app import App
from refresh import stages,runs
from refresh.storage import Store,DEFAULTS

class ReleaseFlow(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(prefix='wwisup-release-test-')
        self.env=patch.dict(os.environ,WWISUP_USER_DIR=self.tmp.name);self.env.start()
        self.a=App(argparse.Namespace(theme='refresh',safe_window=True,play=False,stage=None,screen=None,smoke=None,screenshot=None))
        self.a.s['dialogue']=False;self.a.draw()
    def tearDown(self):
        self.env.stop();self.tmp.cleanup()
    def press(self,key):
        self.a.event(pygame.event.Event(pygame.KEYDOWN,key=key,mod=0))
    def choose(self,label):
        self.a.draw();self.a.ui.focus=next(i for i,b in enumerate(self.a.ui.buttons) if b.label==label)
        self.a.ui.activate();self.a.draw()
    def record(self,stage,tempo=1.,dialogue=False):
        self.a.store.records[runs.record_key(stage.document,tempo,dialogue)]={'stage':stage.title,'best_seconds':12.5,'category':runs.category(tempo,dialogue)}
    def test_fullscreen_blocks_controller_mouse_and_direct_resume_until_confirmed(self):
        a=self.a;a.start_stage(a.catalog.stages[0]);a.pause();a.draw()
        old_button=a.ui.buttons[0].rect.center
        self.press(pygame.K_F11)
        a.resume();self.assertEqual(a.screen,'pause')
        vp=a.display.viewport
        a.event(pygame.event.Event(pygame.MOUSEBUTTONDOWN,button=1,pos=(vp.x+old_button[0]*vp.w/1200,vp.y+old_button[1]*vp.h/800)))
        self.assertEqual(a.screen,'pause');self.assertTrue(a.display.deadline)
        a.draw();tick=a.session.tick
        a.event(pygame.event.Event(pygame.JOYBUTTONDOWN,button=0))
        self.assertFalse(a.display.deadline);self.assertEqual(a.screen,'pause')
        a.update(1/24);self.assertEqual(tick,a.session.tick)
        a.event(pygame.event.Event(pygame.JOYBUTTONDOWN,button=7));self.assertEqual(a.screen,'play')
        self.press(pygame.K_F11)
    def test_board_notification_visible_without_mutating_world_and_compact_saves(self):
        a=self.a;a.start_stage(a.catalog.stages[0]);a.s['board_only']=True
        for _ in range(35):a.session.step({})
        a.draw();before=pygame.image.tobytes(a.display.screen,'RGB')
        a.notify('Could not save: disk full');a.draw()
        self.assertNotEqual(before,pygame.image.tobytes(a.display.screen,'RGB'))
        self.assertEqual(a.display.content_size,(1040,1040))
        a.s['compact_hud']=True;a.store.save();a.draw()
        self.assertEqual(a.display.content_size,(1040,1120));self.assertEqual(a.ui.buttons,[])
        self.assertTrue(Store().settings['compact_hud'])
        a.session.scene['dialogue']='Important dialogue';a.draw()
        self.assertEqual(a.display.content_size,(1200,800))
    def test_progress_uses_content_and_preserves_category_specific_bests(self):
        a=self.a;first,second=a.catalog.stages[:2]
        self.record(first,tempo=1.25);self.assertTrue(a.completed(first))
        self.assertIsNone(a.stage_best(first));self.assertEqual(a.continue_stage().id,second.id)
        a.s['tempo']=1.25;self.assertEqual(a.stage_best(first),12.5)
        self.assertFalse(a.completed(second))
        a.store.save_records();a.store=Store();self.assertTrue(a.completed(first))
    def test_campaign_results_and_one_retry_action(self):
        a=self.a;a.start_stage(a.catalog.stages[0]);a.route('lost');a.draw()
        self.assertEqual(sum('Retry' in b.label or 'Try again' in b.label for b in a.ui.buttons),1)
        for stage in a.catalog.stages:
            if stage.original:self.record(stage)
        a.completed_world=a.catalog.stages[-1].world;a.route('ending');a.draw()
        self.assertIn('Replay a favorite',[b.label for b in a.ui.buttons])
        self.choose('Credits');self.assertEqual(a.screen,'credits')
    def test_settings_tabs_keyboard_reset_and_controller_back(self):
        a=self.a;a.start_stage(a.catalog.stages[0]);a.open_settings();a.draw()
        self.assertFalse(a.s['high_contrast'])
        a.ui.focus=len(a.ui.buttons)-3 # Last display setting, before Done and Controls.
        a.ui.activate();a.draw()
        self.assertTrue(a.s['high_contrast']);self.assertTrue(Store().settings['high_contrast'])
        self.choose('Controls')
        a.s['key_left']='j';self.choose('Reset keyboard bindings')
        self.assertEqual(a.s['key_left'],DEFAULTS['key_left'])
        a.event(pygame.event.Event(pygame.JOYBUTTONDOWN,button=1));self.assertEqual(a.screen,'pause')
        a.draw();a.prompt('Title','draft',lambda v:None)
        a.event(pygame.event.Event(pygame.JOYBUTTONDOWN,button=0));self.assertIsNotNone(a.modal)
        a.event(pygame.event.Event(pygame.JOYBUTTONDOWN,button=1));self.assertIsNone(a.modal)
        self.assertEqual(a.screen,'pause')
    def test_failed_completion_save_does_not_commit_progress_and_can_retry(self):
        a=self.a;d=stages.blank();d['entities'][1]['x']=10.5
        stage=stages.Stage(d['id'],d['title'],'Test',Path('unused'),d,False)
        a.start_stage(stage)
        for _ in range(400):
            a.session.step({'RIGHT':True,'DOWN':True})
            if a.session.result is not None:break
        self.assertEqual(a.session.result,3)
        with patch('refresh.app.atomic_json',side_effect=OSError('disk full')):a.finish()
        self.assertFalse(a.completed(stage));self.assertFalse(a.completion_saved)
        a.save_now();self.assertTrue(a.completed(stage));self.assertTrue(a.completion_saved)
        key=runs.record_key(d,1.,False);row=a.store.records[key]
        self.assertTrue((Path(self.tmp.name)/'data/replays'/row['replay_file']).exists())
        self.assertEqual(Store().records[key],row)
    def test_malformed_drop_keeps_app_usable(self):
        a=self.a;a.start_stage(a.catalog.stages[0])
        path=Path(self.tmp.name)/'broken.txt';path.write_text('player\n')
        a.event(pygame.event.Event(pygame.DROPFILE,file=str(path)))
        self.assertEqual(a.screen,'pause');self.assertTrue(a.message);a.draw()

if __name__=='__main__':unittest.main()
