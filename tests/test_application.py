import os
os.environ['SDL_VIDEODRIVER']='dummy';os.environ['SDL_AUDIODRIVER']='dummy'
import unittest
import tempfile
import argparse
from pathlib import Path
from unittest.mock import patch
import pygame
from refresh.app import App

class ApplicationTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(prefix='wwisup-app-test-')
        self.env=patch.dict(os.environ,WWISUP_USER_DIR=self.tmp.name)
        self.env.start()
        self.app=App(argparse.Namespace(theme='refresh',safe_window=True,play=False,stage=None,screen=None,smoke=None,screenshot=None))
        self.app.draw()
    def tearDown(self):
        self.env.stop();self.tmp.cleanup()
    def click(self,label):
        button=next(b for b in self.app.ui.buttons if b.label==label)
        viewport=self.app.display.viewport
        x=viewport.x+button.rect.centerx*viewport.w/1200
        y=viewport.y+button.rect.centery*viewport.h/800
        self.app.event(pygame.event.Event(pygame.MOUSEBUTTONDOWN,button=1,pos=(x,y)))
        self.app.draw()
    def test_navigation_settings_play_pause_and_studio(self):
        self.click('Customize');self.assertEqual(self.app.screen,'settings')
        self.click('1×');self.assertEqual(self.app.s['tempo'],1.25)
        self.click('Done');self.assertEqual(self.app.screen,'home')
        self.click('Choose a stage');self.assertEqual(self.app.screen,'stages')
        self.click('Stage 1  /  w0-l0');self.assertEqual(self.app.screen,'play')
        self.app.event(pygame.event.Event(pygame.KEYDOWN,key=pygame.K_ESCAPE,mod=0))
        self.app.draw();self.assertEqual(self.app.screen,'pause')
        self.click('Resume');self.assertEqual(self.app.screen,'play')
        self.app.event(pygame.event.Event(pygame.WINDOWFOCUSLOST))
        self.assertEqual(self.app.screen,'pause')
        self.app.new_editor();self.app.editor.paint((320,603));self.app.leave_editor()
        self.app.resume_draft();self.assertEqual(self.app.screen,'editor')
        self.assertTrue(self.app.editor.dirty)
    def test_fullscreen_rollback_and_pressed_input_once(self):
        self.app.display.toggle();self.assertTrue(self.app.display.fullscreen)
        self.app.display.deadline=1;self.app.update(0)
        self.assertFalse(self.app.display.fullscreen)
        self.app.start_stage(self.app.catalog.stages[0])
        self.app.event(pygame.event.Event(pygame.KEYDOWN,key=pygame.K_z,mod=0))
        first=self.app.controls();second=self.app.controls()
        self.assertIn('JUMP',first);self.assertNotIn('JUMP',second);self.assertIn('UP',second)
        self.app.event(pygame.event.Event(pygame.KEYUP,key=pygame.K_z))
        self.assertNotIn('UP',self.app.controls())

if __name__=='__main__':unittest.main()
