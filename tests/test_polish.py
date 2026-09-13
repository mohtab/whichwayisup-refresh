"""Simulated gamer workflows; not a substitute for external human playtesting."""
import argparse
from copy import deepcopy
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
os.environ.update(SDL_VIDEODRIVER='dummy',SDL_AUDIODRIVER='dummy')
import pygame
from refresh.app import App
from refresh import stages,runs
from refresh.runtime import Session
from refresh.storage import DEFAULTS
from refresh.ui import font,wrapped_lines

class GamerProfiles(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(prefix='wwisup-profiles-')
        self.env=patch.dict(os.environ,WWISUP_USER_DIR=self.tmp.name);self.env.start()
        self.app=App(argparse.Namespace(theme='refresh',safe_window=True,play=False,stage=None,screen=None,smoke=None,screenshot=None))
        self.app.draw()
    def tearDown(self):
        self.app.audio_player.apply(dict(self.app.s,music=False))
        self.env.stop();self.tmp.cleanup()
    def key(self,key,mod=0):
        self.app.event(pygame.event.Event(pygame.KEYDOWN,key=key,mod=mod))
        self.app.event(pygame.event.Event(pygame.KEYUP,key=key))
        self.app.draw()
    def choose(self,label):
        a=self.app;a.draw()
        a.ui.focus=next(i for i,b in enumerate(a.ui.buttons) if b.label==label)
        self.key(pygame.K_RETURN)
    def test_first_time_keyboard_player(self):
        a=self.app
        self.key(pygame.K_F1);self.assertEqual(a.screen,'help')
        self.key(pygame.K_ESCAPE);self.assertEqual(a.screen,'home')
        self.choose('Play / Stage 1')
        for _ in range(50):a.update(1/24)
        text=a.session.scene['dialogue'];self.assertTrue(text)
        self.key(pygame.K_z)
        for _ in range(3):a.update(1/24)
        self.assertNotEqual(a.session.scene['dialogue'],text,'Full dialogue must advance on one press')
        self.key(pygame.K_F10);self.assertEqual(a.screen,'settings')
        tick=a.session.tick
        for _ in range(80):a.update(1/60)
        self.assertEqual(a.session.tick,tick)
        self.key(pygame.K_F10);self.assertEqual(a.screen,'pause')
        self.key(pygame.K_p);self.assertEqual(a.screen,'play')
        before=a.theme.id;self.key(pygame.K_F6);self.assertNotEqual(a.theme.id,before)
        self.key(pygame.K_F6,pygame.KMOD_SHIFT);self.assertEqual(a.theme.id,before)
        self.key(pygame.K_F2);self.assertEqual(a.screen,'pause')
        self.assertFalse(a.display.fullscreen)
        self.key(pygame.K_s,pygame.KMOD_CTRL)
        self.assertTrue((Path(self.tmp.name)/'data/practice-replay.json').exists())
    def easy_stage(self):
        d=stages.blank();d['entities'][1]['x']=10.5
        return stages.Stage(d['id'],d['title'],'Test',Path('unused.json'),d,False)
    def complete(self):
        a=self.app
        for _ in range(400):
            a.session.step({'RIGHT':True,'DOWN':True})
            if a.session.result is not None:break
        self.assertEqual(a.session.result,3);a.finish();a.draw()
    def test_speedrunner_pb_retry_rules_and_replay(self):
        a=self.app;a.preset('speedrun');stage=self.easy_stage();a.start_stage(stage)
        self.complete();self.assertTrue(a.new_best)
        key=runs.record_key(stage.document,1.,False)
        best=deepcopy(a.store.records[key])
        replay=json.loads((Path(self.tmp.name)/'data/last-completion-replay.json').read_text())
        result=runs.verify(replay,stage.document,DEFAULTS)
        self.assertEqual(result['ticks'],best['legacy_ticks'])
        a.s.update(tempo=1.5,dialogue=True)
        self.key(pygame.K_r)
        self.assertEqual((a.run_tempo,a.run_dialogue),(1.,False))
        self.complete();self.assertFalse(a.new_best)
        self.assertEqual(a.store.records[key],best)
        self.assertNotEqual(key,runs.record_key(stage.document,1.,True))
        a.route('records');a.draw();self.assertTrue(a.ui.buttons)
    def test_creator_keyboard_save_undo_export_and_playtest(self):
        a=self.app;a.new_editor();before=deepcopy(a.editor.document)
        self.key(pygame.K_UP);self.key(pygame.K_SPACE)
        self.assertNotEqual(before,a.editor.document)
        self.key(pygame.K_z,pygame.KMOD_CTRL);self.assertEqual(before,a.editor.document)
        self.key(pygame.K_y,pygame.KMOD_CTRL);self.assertNotEqual(before,a.editor.document)
        self.key(pygame.K_s,pygame.KMOD_CTRL);self.assertTrue(a.editor.path.exists())
        self.key(pygame.K_s,pygame.KMOD_CTRL|pygame.KMOD_SHIFT)
        self.assertTrue(list((Path(self.tmp.name)/'data/exports').glob('*.json')))
        self.key(pygame.K_F5);self.assertEqual(a.screen,'play');self.assertTrue(a.playtest)
        self.key(pygame.K_ESCAPE);self.choose('Back to studio');self.assertEqual(a.screen,'editor')
    def test_accessibility_audio_and_binding_conflicts(self):
        a=self.app;a.s['effects']=False
        self.key(pygame.K_m);self.assertTrue(a.audio_player.channel.get_busy())
        self.key(pygame.K_m);self.assertFalse(a.audio_player.channel.get_busy())
        a.remap('left');self.key(pygame.K_SPACE);self.assertIsNotNone(a.modal)
        self.key(pygame.K_r);self.assertIsNotNone(a.modal)
        self.key(pygame.K_j);self.assertIsNone(a.modal);self.assertEqual(a.s['key_left'],'j')
        a.start_stage(self.easy_stage());a.held.add(pygame.K_j)
        a.event(pygame.event.Event(pygame.WINDOWFOCUSLOST))
        self.assertEqual(a.screen,'pause');self.assertFalse(a.held)
    def test_preview_cannot_change_active_run(self):
        stage=self.easy_stage();a=self.app;a.s['dialogue']=False;a.start_stage(stage)
        control=Session(stage.engine_path,dict(DEFAULTS,sound=False,dialogue=False))
        for n in range(65):
            inputs={'RIGHT':n>40}
            a.session.step(inputs)
            for _ in range(4):a.preview.step({'LEFT':True})
            control.step(inputs)
        left=a.session.scene;right=control.scene
        self.assertEqual((left['player'].x,left['player'].y,left['fade'],left['score'].time),
                         (right['player'].x,right['player'].y,right['fade'],right['score'].time))
    def test_long_multiline_copy_and_dialogue_pagination(self):
        self.assertEqual(wrapped_lines('First\nSecond',500,18),['First','Second'])
        lines=wrapped_lines('W'*100,160,18)
        self.assertTrue(all(font(18).size(line)[0]<=160 for line in lines))
        a=self.app;a.start_stage(self.easy_stage());a.session.scene['dialogue']='A long stage message. '*30
        self.assertTrue(a.advance_dialogue());self.assertEqual(a.dialogue_page,1)
        a.draw()
        a.route('credits');a.draw()
        with patch.object(a.ui,'text',wraps=a.ui.text) as text:
            a.route('home');a.draw()
            self.assertFalse(any('Hectigo' in str(c) for c in text.call_args_list))
    def test_save_failure_remains_playable_and_no_stale_activation(self):
        a=self.app;a.start_stage(self.easy_stage())
        with patch('refresh.app.atomic_json',side_effect=OSError('test disk full')):
            a.save_now()
        self.assertIn('Could not save',a.message);self.assertEqual(a.screen,'play')
        a.pause();a.draw();a.ui.focus=0;a.ui.activate();self.assertEqual(a.screen,'play')
        a.ui.activate();self.assertEqual(a.screen,'play')
    def test_replays_reject_forged_time_and_inputs(self):
        a=self.app;a.preset('speedrun');stage=self.easy_stage();a.start_stage(stage);self.complete()
        payload=runs.replay(stage.document,a.session,1.,False,0,True)
        for mutate in (lambda p:p.update(ticks=p['ticks']+1),lambda p:p['inputs'].append({'SPECIAL':True}),
                       lambda p:p.update(stage_hash='0'*64),lambda p:p.update(complete=False)):
            altered=deepcopy(payload);mutate(altered)
            with self.assertRaises(ValueError):runs.verify(altered,stage.document,DEFAULTS)
    def test_animation_has_distinct_run_rise_and_fall_poses(self):
        a=self.app;p=a.painter;p.configure(a.theme,a.s)
        frames=[pygame.image.tobytes(p.sprite('player',32,44,'walking',i,'guy'),'RGBA') for i in range(16)]
        self.assertGreaterEqual(len(set(frames)),8)
        rise=pygame.image.tobytes(p.sprite('player',32,44,'rising',0,'guy'),'RGBA')
        fall=pygame.image.tobytes(p.sprite('player',32,44,'falling',0,'guy'),'RGBA')
        self.assertNotEqual(rise,fall)


class DesktopScopeTests(unittest.TestCase):
    def test_resize_targets_own_pid_and_address_only(self):
        from refresh.desktop import resize_own_window
        clients=[dict(pid=os.getpid()+1,address='0x111',title='Other app',mapped=True),
                 dict(pid=os.getpid(),address='0x222',title='Which Way Is Up? — Omarchy Refresh',mapped=True,floating=False)]
        with patch.dict(os.environ,HYPRLAND_INSTANCE_SIGNATURE='test'),patch('refresh.desktop.shutil.which',return_value='/usr/bin/hyprctl'),patch('refresh.desktop.subprocess.run') as run:
            run.return_value.stdout=json.dumps(clients)
            self.assertTrue(resize_own_window((800,533)))
            commands=[c.args[0] for c in run.call_args_list]
            self.assertEqual(len(commands),4)
            for command in commands[1:]:
                self.assertIn('address:0x222',str(command));self.assertNotIn('0x111',str(command))
            clients[1]['pid']+=10;run.return_value.stdout=json.dumps(clients);run.reset_mock()
            self.assertFalse(resize_own_window((800,533)))
            self.assertEqual(run.call_count,1)


class RecoveryTests(unittest.TestCase):
    def test_bad_record_fields_are_backed_up_and_do_not_crash_menus(self):
        from refresh.storage import Store
        with tempfile.TemporaryDirectory() as folder,patch.dict(os.environ,WWISUP_USER_DIR=folder):
            path=Path(folder)/'data/records.json';path.parent.mkdir()
            path.write_text(json.dumps({'bad':{'best_seconds':float('nan'),'stage':'bad'},'broken':False,
                                       'good':{'best_seconds':1.5,'stage':'Good'}}))
            store=Store()
            self.assertEqual(list(store.records),['good'])
            self.assertTrue(path.with_suffix('.invalid-backup').exists())

if __name__=='__main__':unittest.main()
