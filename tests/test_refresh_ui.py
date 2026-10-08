"""Presentation geometry and interaction contract for Refresh UI."""
import os,argparse,tempfile,unittest
from unittest.mock import patch
os.environ.update(SDL_VIDEODRIVER='dummy',SDL_AUDIODRIVER='dummy')
import pygame
from refresh.app import App
from refresh.ui import font
from refresh.ui_refresh import BOARD,DIALOGUE_WIDTH

class RefreshUITests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.env=patch.dict(os.environ,WWISUP_USER_DIR=self.tmp.name);self.env.start()
        self.app=App(argparse.Namespace(theme='refresh',safe_window=True,play=False,stage=None,screen=None,smoke=None,screenshot=None))
    def tearDown(self):self.env.stop();self.tmp.cleanup()
    def assert_buttons(self):
        buttons=self.app.ui.buttons
        for i,b in enumerate(buttons):
            self.assertGreaterEqual(b.rect.h,44,b.label)
            self.assertTrue(pygame.Rect(0,0,1200,800).contains(b.rect),b.label)
            for other in buttons[i+1:]:self.assertFalse(b.rect.colliderect(other.rect),(b.label,other.label))
    def test_home_settings_actions_have_nonoverlapping_accessible_hitboxes(self):
        self.app.draw();self.assertEqual(self.app.ui.buttons[0].label,'Play');self.assert_buttons()
        self.app.settings_screen('home')
        for tab in ('Display','Audio','Controls','Gameplay','Advanced'):
            self.app.settings_tab=tab;self.app.draw();self.assert_buttons()
    def test_world_remains_fixed_and_dialogue_pages_retain_all_copy(self):
        a=self.app;a.s.update(dialogue=False,board_only=False);a.start_stage(a.catalog.stages[0]);a.draw()
        self.assertEqual(tuple(a.world_layers[0][1]),BOARD)
        text=('The brass wheel turns while the explorer waits. '*16)+'X'*160
        a.session.scene['dialogue']=text;a.dialogue_token=None;a.draw()
        self.assertEqual(tuple(a.world_layers[0][1]),BOARD)
        lines=a.dialogue_lines();self.assertTrue(all(font(20).size(line)[0]<=DIALOGUE_WIDTH for line in lines))
        seen=[]
        while True:
            seen.extend(lines[a.dialogue_page*6:(a.dialogue_page+1)*6])
            if not a.advance_dialogue():break
        self.assertEqual(''.join(seen).replace(' ',''),text.replace(' ',''))
        a.pause();a.draw();self.assertEqual(a.world_layers,[]);self.assert_buttons()
    def test_pause_settings_done_returns_and_selection_is_not_focus(self):
        a=self.app;a.start_stage(a.catalog.stages[0]);a.pause();a.settings_screen('pause');a.ui.focus=6;a.draw()
        self.assertEqual(a.settings_tab,'Display')
        selected=a.ui.surface.subsurface((30,144,228,60)).copy()
        a.ui.focus=0;a.draw();self.assertFalse(pygame.image.tobytes(selected,'RGB')==pygame.image.tobytes(a.ui.surface.subsurface((30,144,228,60)),'RGB'))
        next(b for b in a.ui.buttons if b.label=='Done').action();self.assertEqual(a.screen,'pause')

    def test_cached_materials_preserve_source_and_primary_readability(self):
        from refresh.ui import frame_source,metal_panel
        from refresh.themes import contrast
        source=frame_source();before=pygame.image.tobytes(source,'RGBA')
        for size in ((208,44),(420,324),(1200,800)):
            panel=metal_panel(size,(25,43,53),(180,150,90))
            self.assertEqual(panel.get_size(),size)
            self.assertGreater(panel.get_at((size[0]//2,size[1]//2)).a,250)
        primary=metal_panel((430,50),(198,152,105),(230,180,120))
        self.assertGreater(contrast(primary.get_at((215,25))[:3],(10,13,18)),4.5)
        self.assertTrue(pygame.image.tobytes(source,'RGBA')==before)

    def test_surround_is_opaque_and_repeated_present_does_not_accumulate_alpha(self):
        from refresh.chamber import surround
        image=surround((640,480));self.assertIsNone(image.get_alpha())
        target=pygame.Surface((640,480));target.fill((180,25,75));target.blit(image,(0,0))
        first=pygame.image.tobytes(target,'RGB');target.blit(image,(0,0))
        self.assertTrue(first==pygame.image.tobytes(target,'RGB'))

    def test_initial_loading_does_not_count_as_play_but_long_frame_guard_remains(self):
        a=self.app;a.s['dialogue']=False;a.start_stage(a.catalog.stages[0]);a.args.smoke=.06
        class FakeTime:
            now=0.
        fake=FakeTime()
        class Clock:
            def __init__(self):self.last=fake.now
            def tick(self,fps):
                fake.now+=.016;elapsed=fake.now-self.last;self.last=fake.now;return round(elapsed*1000)
        draws=[]
        def draw():
            if not draws:fake.now+=.4
            draws.append(fake.now)
        with patch('refresh.app.pygame.time.Clock',Clock),patch('refresh.app.time.monotonic',lambda:fake.now),patch.object(a,'draw',draw),patch('refresh.app.pygame.quit'):
            # This shared test process reuses cached Font objects in later cases;
            # the real one-shot application still shuts pygame down normally.
            a.run()
        self.assertEqual(a.screen,'play');self.assertGreater(a.session.tick,0)
        a.update(.3);self.assertEqual(a.screen,'pause');self.assertIn('long frame',a.message)

    def test_frame_grain_and_corners_do_not_stretch_with_control_width(self):
        from refresh.ui import metal_panel
        small=metal_panel((208,48),(25,43,53),(180,150,90))
        wide=metal_panel((606,48),(25,43,53),(180,150,90))
        for rect in ((0,0,20,20),(20,0,160,12)):
            self.assertTrue(pygame.image.tobytes(small.subsurface(rect),'RGBA')==pygame.image.tobytes(wide.subsurface(rect),'RGBA'))

    def test_terminal_world_is_visible_without_mutating_fade_or_showing_active_hud(self):
        a=self.app;a.s.update(dialogue=False,board_only=False);a.start_stage(a.catalog.stages[0])
        for _ in range(70):a.update(1/24)
        a.screen='complete';a.session.scene['fade']=255
        tick=a.session.tick
        for saved in (True,False):
            a.completion_saved=saved
            with patch.object(a.ui,'text',wraps=a.ui.text) as text:
                a.draw()
                copy=' '.join(str(c.args[0]) for c in text.call_args_list)
                self.assertNotIn('Find the key',copy);self.assertNotIn('RUN TIME',copy)
            board=a.ui.surface.subsurface(BOARD)
            self.assertGreater(sum(pygame.transform.average_color(board)[:3]),45)
            self.assertEqual(a.session.scene['fade'],255);self.assertEqual(a.session.tick,tick)
            self.assertEqual(a.ui.buttons[0].label,'Next stage');self.assert_buttons()
        a.set_theme('original');a.painter.configure(a.theme,a.s)
        image=a.painter.draw(a.session,a.theme,a.s,resolved=True)
        self.assertEqual(pygame.transform.average_color(image)[:3],(0,0,0))
