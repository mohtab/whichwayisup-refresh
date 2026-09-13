"""Desktop application for the Which Way Is Up? homage."""
import argparse
from collections import deque
import json
import hashlib
import logging
import os
from pathlib import Path
import time
import traceback

import pygame
from .storage import Store, user_path, atomic_json, DEFAULTS
from .themes import Themes, color
from .runtime import Session, Stepper
from .art import Painter
from .ui import UI, font, wrapped_lines
from .audio import Audio
from . import runs, __version__
from .display import Display
from .editor import Editor
from . import stages
from variables import Variables

THEME_ORDER=('original','refresh','omarchy','system','cyberpunk')

class App:
    def __init__(self,args):
        self.args=args;self.store=Store();self.s=self.store.settings
        if args.theme:self.s['theme']=args.theme
        if args.safe_window:self.s['fullscreen']=False
        try:pygame.display.init()
        except pygame.error:
            if not os.environ.get('WWISUP_AUTO_WAYLAND'):raise
            pygame.display.quit();os.environ['SDL_VIDEODRIVER']='x11';pygame.display.init()
            logging.warning('Native Wayland initialization failed; using XWayland')
        pygame.font.init();pygame.joystick.init()
        self.audio=True
        try:pygame.mixer.init()
        except pygame.error:
            self.audio=False
            logging.exception('Audio unavailable; continuing silently')
        self.audio_player=Audio(self.audio)
        self.audio_player.apply(self.s)
        self.display=Display(self.s)
        logging.info('Display %s; pygame %s; SDL %s; desktop %s',pygame.display.get_driver(),pygame.version.ver,pygame.get_sdl_version(),pygame.display.get_desktop_sizes())
        self.themes=Themes();self.themes.poll_system();self.theme=self.themes.get(self.s)
        self.painter=Painter();self.painter.configure(self.theme,self.s)
        self.ui=UI();self.catalog=stages.Catalog()
        self.screen='home';self.return_screen='home';self.running=True
        self.focused=True;self.held=set();self.pending=set();self.joys={}
        self.stepper=Stepper();self.preview_clock=Stepper()
        self.session=None;self.active_stage=None;self.run_tempo=1.;self.playtest=False
        self.editor=None;self.page=0;self.modal=None;self.message='';self.message_until=0
        self.help_return='home';self.records_page=0;self.attempts=0;self.pauses=0
        self.settings_tab='Display';self.input_device='keyboard';self.completed_world=None
        self.run_dialogue=True;self.previous_best=None;self.new_best=False;self.completion_saved=False
        self.dialogue_token=None;self.dialogue_page=0
        self.last_poll=0.;self.last_autosave=0.;self.axis_ready=True
        self.costs=deque(maxlen=600);self.frame_count=0;self.world_layers=[]
        self.reload_joysticks()
        self.preview=self.make_preview()
        self.stage_index=next((i for i,stage in enumerate(self.catalog.stages) if stage.id==self.s['stage']),0)
        if args.stage:
            self.stage_index=next((i for i,v in enumerate(self.catalog.stages) if v.id==args.stage),0)
        if args.play:self.start_stage(self.catalog.stages[self.stage_index])
        if args.screen:self.screen=args.screen
        if self.screen=='editor':self.editor=Editor()
    def make_preview(self):
        settings=dict(self.s,sound=False,dialogue=False)
        session=Session(str(stages.ROOT/'data/levels/w0-l0'),settings)
        for _ in range(35):session.step({})
        return session
    def reload_joysticks(self):
        self.joys={}
        for i in range(pygame.joystick.get_count()):
            try:
                joy=pygame.joystick.Joystick(i);joy.init();self.joys[joy.get_instance_id()]=joy
            except pygame.error:logging.exception('Controller unavailable')
    def completed(self,stage):
        prefix=stages.fingerprint(stage.document)+':'+runs.RULES+':'
        return any(key.startswith(prefix) for key in self.store.records)
    def stage_best(self,stage):
        return self.store.records.get(runs.record_key(stage.document,self.s['tempo'],self.s['dialogue']),{}).get('best_seconds')
    def continue_stage(self):
        originals=[stage for stage in self.catalog.stages if stage.original]
        selected=self.catalog.stages[self.stage_index]
        if not self.completed(selected):return selected
        return next((stage for stage in originals if not self.completed(stage)),selected)
    def short_name(self,stage):
        return stages.display_name(stage).split(' · ')[-1] if stage.original else stage.title
    def reset_bindings(self):
        for action in ('left','right','jump','interact'):
            self.s['key_'+action]=DEFAULTS['key_'+action]
        self.store.save();self.notify('Keyboard bindings reset.')
    def set_view(self):
        current='compact' if self.s['board_only'] and self.s['compact_hud'] else 'board' if self.s['board_only'] else 'full'
        view={'full':'compact','compact':'board','board':'full'}[current]
        self.s.update(board_only=view!='full',compact_hud=view=='compact');self.store.save()
    def back(self):
        if self.screen=='pause':self.resume()
        elif self.screen=='editor':self.leave_editor()
        elif self.screen=='settings':self.route(self.return_screen)
        elif self.screen=='help':self.route(self.help_return)
        else:self.route('home')
    def notify(self,message):self.message=str(message);self.message_until=time.monotonic()+7
    def route(self,screen):
        self.screen=screen;self.ui.focus=0;self.ui.buttons=[];self.held.clear();self.pending.clear();self.stepper.reset()
    def set_theme(self,ident):
        self.s['theme']=ident;self.s['accent']=''
        self.theme=self.themes.get(self.s);self.painter.configure(self.theme,self.s);self.store.save()
    def setting(self,key,values):
        current=self.s.get(key)
        self.s[key]=values[(values.index(current)+1)%len(values)] if current in values else values[0]
        self.theme=self.themes.get(self.s)
        self.audio_player.apply(self.s)
        if self.session:self.session.settings.update(sound=self.s['sound'] and self.audio,sfx_volume=self.s['sfx_volume'])
        self.store.save()
    def prompt(self,title,value,callback):
        self.modal={'title':title,'value':str(value),'callback':callback,'select_all':True}
        pygame.key.start_text_input()
    def submit_prompt(self):
        modal=self.modal
        try:modal['callback'](modal['value'])
        except (ValueError,OSError) as e:self.notify(e);return
        self.modal=None;pygame.key.stop_text_input()
    def import_prompt(self):self.prompt('Path to a stage JSON or legacy TXT file','',self.import_file)
    def import_file(self,value):
        path=stages.import_stage(Path(value.strip()).expanduser())
        self.catalog.refresh();self.notify('Imported '+path.name);self.page=(len(self.catalog.stages)-1)//12
    def set_accent(self,value):
        if value:color(value)
        self.s['accent']=value;self.theme=self.themes.get(self.s);self.store.save()
    def export_theme(self):
        path=self.themes.export(self.theme);self.notify('Saved '+str(path))
    def remap(self,action):
        self.modal={'title':'Press a key for '+action,'binding':action}
    def start_stage(self,stage,playtest=False):
        self.attempts=self.attempts+1 if self.active_stage and self.active_stage.id==stage.id else 1
        self.active_stage=stage;self.run_tempo=self.s['tempo'];self.playtest=playtest
        self.run_dialogue=self.s['dialogue'];self.pauses=0;self.new_best=False;self.completed_world=None;self.completion_saved=False
        self.previous_best=self.store.records.get(runs.record_key(stage.document,self.run_tempo,self.run_dialogue),{}).get('best_seconds')
        self.dialogue_token=None;self.dialogue_page=0
        settings=dict(self.s,sound=self.s['sound'] and self.audio)
        self.session=Session(stage.engine_path,settings)
        self.s['stage']=stage.id
        self.stage_index=next((i for i,v in enumerate(self.catalog.stages) if v.id==stage.id),self.stage_index)
        if not playtest:self.store.save()
        self.route('play')
    def pause(self):
        if self.screen=='play':self.pauses+=1;self.route('pause')
    def resume(self):
        if self.session and self.session.result is None and not self.display.deadline:
            self.session.settings.update(sound=self.s['sound'] and self.audio,sfx_volume=self.s['sfx_volume'])
            self.route('play')
    def restart(self):
        if self.active_stage:
            # Retry the same category even when next-run settings were changed.
            tempo,dialogue=self.run_tempo,self.run_dialogue
            self.start_stage(self.active_stage,self.playtest)
            self.run_tempo=tempo;self.run_dialogue=dialogue
            self.session.settings['dialogue']=dialogue
            self.previous_best=self.store.records.get(runs.record_key(self.active_stage.document,tempo,dialogue),{}).get('best_seconds')
    def new_editor(self,document=None):
        if self.editor and self.editor.dirty:self.editor.save(draft=True)
        self.editor=Editor(document);self.route('editor')
    def leave_editor(self):
        if self.editor:self.editor.save(draft=True)
        self.route('stages')
    def editor_save(self):
        try:
            path=self.editor.save();self.catalog.refresh();self.notify('Stage saved: '+path.name)
        except (ValueError,OSError) as e:self.notify(e)
    def editor_export(self):
        try:self.notify('Exported '+str(self.editor.export()))
        except (ValueError,OSError) as e:self.notify(e)
    def editor_test(self):
        try:
            d=stages.validate(self.editor.document)
            stage=stages.Stage(d['id'],d['title'],'Studio playtest',Path('unused.json'),d,False)
            self.editor.save(draft=True);self.start_stage(stage,True)
        except (ValueError,OSError) as e:self.notify(e)
    def return_editor(self):self.route('editor')
    def finish(self):
        result=self.session.result
        if result==3:
            seconds=self.session.score.time/24/self.run_tempo
            key=runs.record_key(self.active_stage.document,self.run_tempo,self.run_dialogue)
            self.new_best=self.previous_best is None or seconds<self.previous_best
            if not self.playtest:
                replay=runs.replay(self.active_stage.document,self.session,self.run_tempo,self.run_dialogue,self.pauses,True)
                try:
                    updated=dict(self.store.records)
                    if self.new_best:
                        replay_name=hashlib.sha256(json.dumps(replay,sort_keys=True).encode()).hexdigest()+'.json'
                        updated[key]={'stage':self.active_stage.title,'best_seconds':seconds,
                            'legacy_ticks':self.session.score.time,'tempo':self.run_tempo,'rules':runs.RULES,
                            'category':runs.category(self.run_tempo,self.run_dialogue),'pauses':self.pauses,'replay_file':replay_name}
                        atomic_json(user_path('data')/'replays'/replay_name,replay)
                    atomic_json(self.store.records_path,updated)
                    self.store.records=updated
                    self.completion_saved=True
                    atomic_json(user_path('data')/'last-completion-replay.json',replay)
                except OSError as e:self.notify('Finished, but saving failed: '+str(e))
            if self.active_stage.original and not self.playtest:
                group=[stage for stage in self.catalog.stages if stage.original and stage.world==self.active_stage.world]
                if all(self.completed(stage) for stage in group):self.completed_world=self.active_stage.world
            self.route('complete')
        elif result==1:self.route('lost')
        else:self.route('pause')
    def save_now(self):
        if self.screen=='editor':self.editor_save();return
        try:
            if not self.display.fullscreen:self.s['window']=list(self.display.screen.get_size())
            self.store.save()
            if self.screen=='complete' and not self.playtest and not self.completion_saved:
                self.finish()
                if not self.completion_saved:return
            if self.session and self.screen in ('play','pause','lost','complete'):
                payload=runs.replay(self.active_stage.document,self.session,self.run_tempo,self.run_dialogue,self.pauses,self.session.result==3)
                atomic_json(user_path('data')/'practice-replay.json',payload)
                self.notify('Settings and practice replay saved. Replays are input recordings, not resume checkpoints.')
            else:self.notify('Settings saved. Completed runs save automatically.')
        except OSError as e:self.notify('Could not save: '+str(e))
    def cycle_theme(self,direction=1):
        choices=list(self.themes.packs)
        index=choices.index(self.theme.id)
        self.set_theme(choices[(index+direction)%len(choices)])
        self.notify('Theme: '+self.theme.name)
    def show_help(self):
        if self.screen=='help':self.route(self.help_return);return
        self.pause();self.help_return=self.screen;self.route('help')
    def open_settings(self):
        if self.screen=='settings':self.route(self.return_screen);return
        self.pause();self.settings_screen(self.screen)
    def preset(self,profile):
        self.s.update(profile=profile,dialogue=profile=='story',tempo=1.)
        self.store.save();self.notify(('Speedrun: dialogue skipped, 1× tempo.' if profile=='speedrun' else 'Story: dialogue on, 1× tempo.')+' Applies to your next stage.')
    def dialogue_lines(self):
        text=self.session.scene['dialogue'] or ''
        if text!=self.dialogue_token:self.dialogue_token=text;self.dialogue_page=0
        if self.active_stage.original:
            replacements={
                'You there with the controls, just lay your hand on the arrow keys.':f"Move with {self.s['key_left'].upper()} / {self.s['key_right'].upper()}, or A / D.",
                "I jump with the up arrow or Z. Hold it longer, and I'll jump higher.":f"Jump with {self.s['key_jump'].upper()}, Space or Up. Hold jump to slow your fall.",
                'Collect stuff and pull levers with the down arrow. Got it now?':f"Use {self.s['key_interact'].upper()}, S or E to collect items and pull levers."}
            text=replacements.get(text,text)
        return wrapped_lines(text,392,18)
    def advance_dialogue(self):
        if not self.session or not self.session.scene['dialogue']:return False
        lines=self.dialogue_lines()
        if (self.dialogue_page+1)*6<len(lines):self.dialogue_page+=1;return True
        return False
    def next_stage(self):
        if self.playtest:self.return_editor();return
        index=next((i for i,s in enumerate(self.catalog.stages) if s.id==self.active_stage.id),0)
        if index+1<len(self.catalog.stages) and self.catalog.stages[index+1].original==self.active_stage.original:self.start_stage(self.catalog.stages[index+1])
        else:self.route('stages')
    def action_for(self,key):
        maps={'left':('a',),'right':('d',),'jump':('up','space'),'interact':('s','e')}
        for action,defaults in maps.items():
            custom=self.s['key_'+action]
            try:keys={pygame.key.key_code(name) for name in (*defaults,custom)}
            except ValueError:keys={pygame.key.key_code(name) for name in defaults}
            if key in keys:return action
        return None
    def controls(self):
        actions={self.action_for(k) for k in self.held}
        for joy in self.joys.values():
            try:
                if joy.get_numaxes()>0:
                    axis=joy.get_axis(0)
                    if axis<-.2:actions.add('left')
                    if axis>.2:actions.add('right')
                if joy.get_numhats()>0:
                    hat=joy.get_hat(0)
                    if hat[0]<0:actions.add('left')
                    if hat[0]>0:actions.add('right')
                if joy.get_numbuttons()>0 and joy.get_button(0):actions.add('jump')
            except pygame.error:pass
        inputs={}
        if 'left' in actions:inputs['LEFT']=True
        if 'right' in actions:inputs['RIGHT']=True
        if 'jump' in actions:inputs['UP']=True
        if 'jump' in self.pending:inputs['JUMP']=True
        if 'interact' in self.pending:inputs['DOWN']=True
        self.pending.clear()
        return inputs
    def event(self,event):
        if event.type in (pygame.JOYBUTTONDOWN,pygame.JOYHATMOTION):self.input_device='controller'
        elif event.type==pygame.JOYAXISMOTION and abs(event.value)>.3:self.input_device='controller'
        elif event.type in (pygame.KEYDOWN,pygame.MOUSEBUTTONDOWN):self.input_device='keyboard'
        if event.type==pygame.QUIT:
            logging.info('Received QUIT on %s',self.screen);self.running=False;return
        if event.type==pygame.WINDOWFOCUSLOST:
            self.focused=False;self.held.clear();self.pending.clear();self.pause();return
        if event.type==pygame.WINDOWFOCUSGAINED:self.focused=True;return
        if event.type in (pygame.JOYDEVICEADDED,pygame.JOYDEVICEREMOVED):
            if event.type==pygame.JOYDEVICEREMOVED:self.pause()
            self.reload_joysticks();return
        if self.display.deadline:
            # Every input device is scoped to the confirmation until it is resolved.
            if event.type==pygame.KEYDOWN and not getattr(event,'repeat',False):
                if event.key==pygame.K_RETURN:self.display.confirm()
                elif event.key in (pygame.K_ESCAPE,pygame.K_F11):self.display.toggle()
            elif event.type==pygame.JOYBUTTONDOWN:
                if event.button==0:self.display.confirm()
                elif event.button==1:self.display.toggle()
            elif event.type==pygame.MOUSEBUTTONDOWN and event.button==1:
                pos=self.display.map(event.pos)
                for button in self.ui.buttons:
                    if button.rect.collidepoint(pos):
                        if button.label.startswith('Keep /'):self.display.confirm()
                        elif button.label.startswith('Revert /'):self.display.toggle()
                        break
            return
        if event.type==pygame.DROPFILE:
            self.pause()
            try:self.import_file(event.file);self.route('stages')
            except (ValueError,OSError) as e:self.notify(e)
            return
        if self.modal:
            if event.type==pygame.JOYBUTTONDOWN and event.button==1:
                self.modal=None;pygame.key.stop_text_input();return
            if event.type==pygame.KEYDOWN:
                if event.key==pygame.K_ESCAPE:self.modal=None;pygame.key.stop_text_input();return
                if 'binding' in self.modal:
                    name=pygame.key.name(event.key)
                    reserved=(pygame.K_F1,pygame.K_F2,pygame.K_F5,pygame.K_F6,pygame.K_F9,pygame.K_F10,pygame.K_F11,pygame.K_TAB,pygame.K_RETURN,pygame.K_p,pygame.K_r,pygame.K_m)
                    if event.key in reserved:self.notify('Choose a key other than a menu or fullscreen shortcut.');return
                    action=self.modal['binding']
                    conflicts={self.s['key_'+a] for a in ('left','right','jump','interact') if a!=action}
                    aliases={'left':('a',),'right':('d',),'jump':('up','space'),'interact':('s','e')}
                    conflicts.update(k for a,keys in aliases.items() if a!=action for k in keys)
                    if name in conflicts:
                        self.notify('That key is already assigned to another action.');return
                    self.s['key_'+action]=name;self.store.save();self.modal=None;return
                if event.key==pygame.K_RETURN:self.submit_prompt();return
                if event.key==pygame.K_BACKSPACE:
                    self.modal['value']='' if self.modal['select_all'] else self.modal['value'][:-1]
                    self.modal['select_all']=False
                if event.key==pygame.K_a and event.mod & pygame.KMOD_CTRL:self.modal['select_all']=True
            elif event.type==pygame.TEXTINPUT and 'value' in self.modal:
                if self.modal['select_all']:self.modal['value']='';self.modal['select_all']=False
                self.modal['value']=(self.modal['value']+event.text)[:500]
            return
        if event.type==pygame.KEYDOWN:
            if getattr(event,'repeat',False):return
            if self.display.deadline:
                if event.key==pygame.K_RETURN:self.display.confirm();return
                if event.key in (pygame.K_ESCAPE,pygame.K_F11):self.display.toggle();return
                return
            if event.key==pygame.K_F1:self.show_help();return
            if event.key==pygame.K_F2:
                self.pause()
                try:
                    size=self.display.cycle_size();self.store.save();self.notify(f'Window preset: {size[0]} × {size[1]} (F2 cycles sizes).')
                except pygame.error as e:self.notify('Resize failed: '+str(e))
                return
            if event.key==pygame.K_F6:self.cycle_theme(-1 if event.mod & pygame.KMOD_SHIFT else 1);return
            if event.key==pygame.K_F9:self.setting('board_only',[False,True]);return
            if event.key==pygame.K_F10:self.open_settings();return
            if event.mod & pygame.KMOD_CTRL and event.key==pygame.K_s:
                if self.screen=='editor' and event.mod & pygame.KMOD_SHIFT:self.editor_export()
                else:self.save_now()
                return
            if event.key==pygame.K_m:self.setting('music',[False,True]);self.notify('Music '+('on' if self.s['music'] else 'off'));return
            if event.key==pygame.K_r and self.screen in ('play','pause','lost','complete'):self.restart();return
            if event.key==pygame.K_p and self.screen=='pause':self.resume();return
            if event.key==pygame.K_F11:
                try:self.display.toggle()
                except pygame.error as e:self.notify('Display change failed: '+str(e))
                self.pause();return
            if self.screen=='play':
                if event.key in (pygame.K_ESCAPE,pygame.K_p):self.pause();return
                if event.key==pygame.K_r:self.restart();return
                self.held.add(event.key)
                action=self.action_for(event.key)
                if action:
                    if action in ('jump','interact') and self.advance_dialogue():self.held.discard(event.key);return
                    self.pending.add(action)
                return
            if self.screen=='editor' and self.editor.key(event,self):return
            if self.screen=='editor' and event.mod & pygame.KMOD_CTRL:
                if event.key==pygame.K_z:self.editor.go_undo()
                if event.key==pygame.K_y:self.editor.go_redo()
                if event.key==pygame.K_s:self.editor_save()
                return
            if event.key==pygame.K_ESCAPE:
                self.back()
            elif event.key in (pygame.K_TAB,pygame.K_DOWN):self.ui.move(-1 if event.mod & pygame.KMOD_SHIFT else 1)
            elif event.key==pygame.K_UP:self.ui.move(-1)
            elif event.key in (pygame.K_RETURN,pygame.K_SPACE):self.ui.activate()
        elif event.type==pygame.KEYUP:self.held.discard(event.key)
        elif event.type==pygame.MOUSEMOTION:
            self.ui.mouse=self.display.map(event.pos)
            if self.screen=='editor' and self.editor.tool in ('W','S','B','erase'):
                if event.buttons[0] or event.buttons[2]:self.editor.paint(self.ui.mouse,event.buttons[2])
        elif event.type==pygame.MOUSEBUTTONDOWN:
            pos=self.display.map(event.pos)
            if self.screen=='editor' and event.button in (1,3) and self.editor.paint(pos,event.button==3):return
            if event.button==1:self.ui.click(pos)
        elif event.type==pygame.JOYBUTTONDOWN:
            if self.screen=='play':
                if event.button==0:
                    if not self.advance_dialogue():self.pending.add('jump')
                elif event.button==1:
                    if not self.advance_dialogue():self.pending.add('interact')
                elif event.button in (6,7):self.pause()
            elif event.button==0:self.ui.activate()
            elif event.button==1:self.back()
            elif event.button in (6,7) and self.screen=='pause':self.resume()
        elif event.type==pygame.JOYHATMOTION and self.screen!='play':
            if event.value[1]:self.ui.move(-event.value[1])
            elif event.value[0]:self.ui.move(event.value[0])
        elif event.type==pygame.JOYAXISMOTION and event.axis==1 and self.screen!='play':
            if abs(event.value)<.3:self.axis_ready=True
            elif self.axis_ready and abs(event.value)>.6:self.ui.move(1 if event.value>0 else -1);self.axis_ready=False
    def update(self,dt):
        now=time.monotonic()
        if self.display.check():self.notify('Fullscreen reverted to windowed mode.')
        if now-self.last_poll>2:
            self.last_poll=now
            self.themes.poll_system()
        if self.screen!='play':self.theme=self.themes.get(self.s)
        if self.editor and self.editor.dirty and now-self.last_autosave>20:
            self.last_autosave=now
            try:self.editor.save(draft=True)
            except OSError as e:self.notify('Draft autosave failed: '+str(e))
        if self.screen=='play':
            if self.display.deadline or self.modal:self.stepper.reset();return
            count=self.stepper.advance(dt,self.run_tempo)
            if self.stepper.overrun:self.pause();self.notify('Paused after a long frame. Press Resume when ready.');return
            for _ in range(count):
                self.session.step(self.controls())
                if self.session.result is not None:self.finish();break
        elif self.screen in ('home','settings'):
            Variables.vdict.update(sound=False,dialogue=False)
            for _ in range(self.preview_clock.advance(min(dt,.1))):
                n=self.preview.tick
                inp={'RIGHT':True} if n%160<80 else {'LEFT':True}
                if n%24==0:inp['JUMP']=True
                if n%24<12:inp['UP']=True
                self.preview.step(inp)
                if self.preview.result is not None or self.preview.tick>1400:self.preview=self.make_preview()
    def blit_world(self,session,rect,preview=False):
        alpha=self.preview_clock.alpha if preview else self.stepper.alpha
        image=self.painter.draw(session,self.theme,self.s,alpha if self.screen=='play' or preview else 1,preview)
        if self.screen in ('home','play') and not self.modal and not self.display.deadline:
            self.world_layers.append((image.copy(),rect,self.s['smooth'] and self.theme.style!='original',
                                      self.s['integer_scale'] and self.theme.style=='original',self.painter.scale))
        transform=pygame.transform.smoothscale if self.s['smooth'] and self.theme.style!='original' else pygame.transform.scale
        self.ui.surface.blit(transform(image,(rect[2],rect[3])),rect[:2])
        pygame.draw.rect(self.ui.surface,self.theme['accent'],rect,1,border_radius=2)
    def settings_screen(self,back):self.return_screen=back;self.route('settings')
    def draw_home(self):
        u=self.ui;t=self.theme
        u.header('REFRESH / '+__version__)
        u.text('TURN THE WORLD. FIND YOUR LINE.',40,115,14,t['accent'])
        u.text('Which way',36,151,65)
        u.text('is up?',36,225,65)
        u.wrap('A little gravity. A lot of possibility.',40,321,510,23)
        u.wrap('Find the key. Flip the room. Then do it faster. A Linux favorite, revisited by Mohtab Arabiat.',40,369,480,18,t['muted'])
        u.fit('YOUR NEXT RUN / '+self.continue_stage().world.upper(),40,448,515,12,t['accent'])
        stage=self.continue_stage()
        started=bool([key for key in self.store.records if key!='legacy_import'])
        u.button(('Continue / ' if started else 'Play / ')+self.short_name(stage),(40,481,268,53),lambda:self.start_stage(stage),primary=True)
        u.button('Choose a stage',(322,481,242,53),lambda:self.route('stages'))
        u.button('Story',(40,548,126,38),lambda:self.preset('story'),selected=self.s['dialogue'] and self.s['tempo']==1.)
        u.button('Speedrun',(178,548,146,38),lambda:self.preset('speedrun'),selected=not self.s['dialogue'] and self.s['tempo']==1.)
        u.button('Personal bests',(336,548,228,38),lambda:self.route('records'))
        for i,(label,action) in enumerate((('Customize',lambda:self.settings_screen('home')),('Stage studio',lambda:self.new_editor()),('Credits',lambda:self.route('credits')))):
            u.button(label,(40+i*178,601,168,40),action)
        self.blit_world(self.preview,(634,115,518,518),True)
        originals=[stage for stage in self.catalog.stages if stage.original]
        done=sum(self.completed(stage) for stage in originals)
        u.text(f'{done} / {len(originals)} STAGES COMPLETE   /   BUILD YOUR OWN',652,645,12,t['muted'])
        for i,ident in enumerate(THEME_ORDER):
            pack=self.themes.packs[ident]
            u.button(pack.name,(40+i*226,687,214,45),lambda v=ident:self.set_theme(v),selected=self.s['theme']==ident)
        u.button('Quit',(1066,27,86,31),lambda:setattr(self,'running',False))


    def draw_stages(self):
        u=self.ui;t=self.theme;u.header('CAMPAIGNS / YOUR STAGES')
        u.text('Every world starts with a stage.',40,101,34)
        groups=[(world,[v for v in self.catalog.stages if v.original and v.world==world]) for world in stages.WORLD_NAMES]
        for i,(world,group) in enumerate(groups):
            count=sum(self.completed(v) for v in group)
            u.fit(f'{world}  {count}/{len(group)}',40+i*378,153,355,15,t['accent'])
        subset=self.catalog.stages[self.page*12:self.page*12+12]
        for i,stage in enumerate(subset):
            x=40+(i%3)*378;y=192+(i//3)*111
            u.panel((x,y,362,99))
            u.fit(stage.world.upper(),x+14,y+9,330,11,t['muted'])
            u.button(self.short_name(stage),(x+12,y+28,236,37),lambda v=stage:self.start_stage(v))
            u.button('Remix',(x+258,y+28,92,37),lambda v=stage:self.new_editor(v.document))
            best=self.stage_best(stage)
            status='Complete' if self.completed(stage) else 'Not yet completed'
            if best is not None:status+='  /  PB '+runs.clock_text(best)
            u.fit(status,x+14,y+75,333,12,t['accent'] if self.completed(stage) else t['muted'])
        u.button('Back',(40,676,130,44),lambda:self.route('home'))
        u.button('New stage',(184,676,170,44),lambda:self.new_editor(),primary=True)
        u.button('Import file',(368,676,170,44),self.import_prompt)
        u.button('Resume draft',(552,676,166,44),self.resume_draft)
        if self.page>0:u.button('Previous',(760,676,170,44),lambda:setattr(self,'page',self.page-1))
        if (self.page+1)*12<len(self.catalog.stages):u.button('Next',(944,676,170,44),lambda:setattr(self,'page',self.page+1))
        u.fit('PBs: '+runs.category(self.s['tempo'],self.s['dialogue'])+'  /  Drop a stage JSON or TXT here to import.',40,737,1100,14,t['muted'])
    def resume_draft(self):
        paths=sorted((user_path('data')/'drafts').glob('*.json'),key=lambda p:p.stat().st_mtime,reverse=True)
        if not paths:self.notify('No saved draft yet. Create a stage in the studio.');return
        try:
            d=json.loads(paths[0].read_text())
            checked=json.loads(json.dumps(d))
            # A deleted spawn is an unfinished edit, not a reason to discard a draft.
            checked['entities']=[e for e in checked['entities'] if e['type']!='player']
            checked['entities'].insert(0,dict(type='player',x=9.5,y=18.5))
            stages.validate(checked)
            self.new_editor();self.editor.document=d;self.editor.dirty=True
        except (ValueError,OSError,KeyError,TypeError) as e:self.notify('Draft cannot be opened: '+str(e));return
        self.notify('Restored draft: '+d['title'])
    def reload_catalog(self):self.catalog.refresh();self.page=min(self.page,(len(self.catalog.stages)-1)//12);self.notify('; '.join(self.catalog.errors) or 'Stage library refreshed.')
    def draw_settings(self):
        u=self.ui;t=self.theme;u.header('SETTINGS / SAVED AUTOMATICALLY')
        u.text('Find your rhythm.',40,104,36)
        for i,tab in enumerate(('Display','Audio','Controls','Gameplay','Advanced')):
            u.button(tab,(40+i*226,170,214,44),lambda value=tab:setattr(self,'settings_tab',value),selected=self.settings_tab==tab)
        theme_ids=list(THEME_ORDER)+[k for k in self.themes.packs if k not in THEME_ORDER]
        on=lambda key:'On' if self.s[key] else 'Off'
        toggle=lambda key:lambda:self.setting(key,[False,True])
        view='Compact HUD' if self.s['board_only'] and self.s['compact_hud'] else 'Board only' if self.s['board_only'] else 'Full interface'
        rows={
            'Display':[
                ('World design',t.name,lambda:self.setting('theme',theme_ids)),
                ('Character',{'theme':'Theme default','original':'Original Guy','guy':'Explorer','dhh':'DHH cameo'}[self.s['character']],lambda:self.setting('character',['theme','original','guy','dhh'])),
                ('Play layout',view,self.set_view),
                ('Display refresh',str(self.s['fps'])+' FPS',lambda:self.setting('fps',[30,60,120,144,240])),
                ('World scaling','Smooth' if self.s['smooth'] else 'Crisp',toggle('smooth')),
                ('Original board integer fit',on('integer_scale'),toggle('integer_scale')),
                ('High-contrast sprites',on('high_contrast'),toggle('high_contrast'))],
            'Audio':[
                ('Ambient music',on('music'),toggle('music')),
                ('Music volume',str(self.s['music_volume'])+'%',lambda:self.setting('music_volume',[0,25,50,75,100])),
                ('Sound effects',on('sound'),toggle('sound')),
                ('Effects volume',str(self.s['sfx_volume'])+'%',lambda:self.setting('sfx_volume',[0,25,50,75,100]))],
            'Gameplay':[
                ('Run preset','Story' if self.s['dialogue'] else 'Speedrun',lambda:self.preset('speedrun' if self.s['dialogue'] else 'story')),
                ('Tempo / next stage',f"{self.s['tempo']:g}×",lambda:self.setting('tempo',[.75,1.,1.25,1.5])),
                ('Dialogue / next stage',on('dialogue'),toggle('dialogue')),
                ('Extra effects','On' if self.s['effects'] else 'Reduced',toggle('effects')),
                ('Scene depth',on('depth'),toggle('depth'))],
            'Advanced':[
                ('Accent color',self.s['accent'] or 'Theme default',lambda:self.prompt('Accent hex color (#rrggbb); blank resets',self.s['accent'],self.set_accent)),
                ('Theme file','Save theme pack',self.export_theme),
                ('Restore theme color','Reset accent',lambda:self.set_accent(''))],
            'Controls':[(action.title(),self.s['key_'+action].upper(),lambda v=action:self.remap(v)) for action in ('left','right','jump','interact')]
        }[self.settings_tab]
        for i,(label,value,action) in enumerate(rows):
            y=250+i*(50 if self.settings_tab=='Display' else 57)
            u.text(label,65,y+10,19,t['muted'])
            u.button(value,(624,y,508,43),action)
        if self.settings_tab=='Controls':
            u.button('Reset keyboard bindings',(65,489,420,43),self.reset_bindings)
            u.wrap('Controller: stick or D-pad to move. Button 1 jumps / confirms; Button 2 interacts / goes back. Buttons 7 or 8 pause / resume.',65,554,1050,18,t['muted'])
        elif self.settings_tab=='Gameplay':
            u.wrap('Tempo and dialogue apply to the next stage. Retry keeps the current run rules. Reduced effects preserves essential character motion.',65,573,1040,17,t['muted'])
        elif self.settings_tab=='Display':
            u.fit('F9 switches board / full view. Integer fit applies to Original; small windows use a fractional fit.',65,618,1050,16,t['muted'])
            u.fit('High contrast adds bright player and enemy outlines to modern artwork.',65,644,1050,16,t['muted'])
        elif self.settings_tab=='Audio':
            u.wrap('Music and sound effects have independent volume controls.' if self.audio else 'No audio device detected. Play continues silently.',65,521,1050,18,t['muted'])
        elif self.settings_tab=='Advanced':
            u.wrap('Theme packs are editable palette files. Your saved designs appear in World design. Original artwork keeps its own palette.',65,472,1050,18,t['muted'])
        u.button('Done',(40,687,190,44),lambda:self.route(self.return_screen),primary=True)
        u.button('Controls / F1',(942,687,214,44),self.show_help)

    def draw_play(self):
        u=self.ui;t=self.theme;session=self.session;scene=session.scene
        u.header('STUDIO PLAYTEST' if self.playtest else self.active_stage.world.upper())
        u.fit(stages.display_name(self.active_stage),40,94,620,17,t['muted'])
        self.blit_world(session,(40,123,620,620))
        u.text('IN-GAME TIME',704,111,13,t['accent'])
        u.text(runs.clock_text(session.score.time/24/self.run_tempo),699,137,56)
        u.text(f'ATTEMPT {self.attempts:02d}   /   {session.score.time} TICKS',704,207,13,t['muted'])
        u.panel((692,242,464,100))
        u.text('PERSONAL BEST',712,260,12,t['muted'])
        u.text(runs.clock_text(self.previous_best) if self.previous_best is not None else 'Set your first time',710,285,26)
        u.text(f"{self.run_tempo:g}×  ·  {'Story' if self.run_dialogue else 'Dialogue skipped'}  ·  Local IGT",704,365,15,t['muted'])
        u.text('HEALTH',704,401,12,t['muted'])
        pygame.draw.rect(u.surface,t['panel'],(790,405,294,10),border_radius=5)
        pygame.draw.rect(u.surface,t['accent'] if scene['player'].life>10 else t['hazard'],(790,405,max(0,min(294,294*scene['player'].life/36)),10),border_radius=5)
        u.text(str(max(0,scene['player'].life)),1100,398,16)
        u.panel((692,443,464,211))
        if scene['dialogue']:
            lines=self.dialogue_lines();pages=max(1,(len(lines)+5)//6)
            for i,line in enumerate(lines[self.dialogue_page*6:(self.dialogue_page+1)*6]):u.text(line,712,459+i*26,18)
            hint='Next page' if self.dialogue_page+1<pages else 'Continue'
            u.fit(('Button 1 / Button 2  '+hint) if self.input_device=='controller' else f"{self.s['key_jump'].upper()} / Space / {self.s['key_interact'].upper()}  {hint}"+(f'  {self.dialogue_page+1}/{pages}' if pages>1 else ''),712,629,425,12,t['accent'])
        else:
            u.text('FIND YOUR LINE',712,463,13,t['accent'])
            u.wrap(f"Move  {self.s['key_left'].upper()} / {self.s['key_right'].upper()} or A / D\nJump  {self.s['key_jump'].upper()} / Space / Up\nInteract  {self.s['key_interact'].upper()} / S / E",712,496,410,17,t['muted'])
            u.text('Button 1: jump  /  Button 2: interact' if self.input_device=='controller' else 'Hold jump to slow your fall.',712,610,15,t['muted'])
        u.button('Pause / Esc',(700,679,218,45),self.pause)
        u.button('Retry / R',(934,679,218,45),self.restart)
        if self.screen!='play':
            shade=pygame.Surface((1200,800),pygame.SRCALPHA);shade.fill((0,0,0,190));u.surface.blit(shade,(0,0));u.buttons=[]
            u.panel((325,116,550,588))
            title={'pause':'Paused.','lost':'One more try.','complete':'Campaign clear!' if self.completed_world else 'Stage clear.'}[self.screen]
            u.text(title,361,150,38)
            if self.screen=='complete':
                u.text(runs.clock_text(session.score.time/24/self.run_tempo),361,205,42)
                detail='Playtest complete' if self.playtest else 'Save failed. Ctrl+S to retry.' if not self.completion_saved else 'New personal best!' if self.new_best else 'Personal best: '+runs.clock_text(self.previous_best or 0)
                u.text(detail,361,258,18,t['accent'])
                if self.previous_best is not None:
                    delta=session.score.time/24/self.run_tempo-self.previous_best
                    u.text(('Equal to your best' if abs(delta)<.0005 else f'{abs(delta):.3f}s '+('faster than your best' if delta<0 else 'behind your best')),361,287,15,t['muted'])
            else:
                u.wrap('Your run is paused. Resume when ready.' if self.screen=='pause' else 'Same stage. Same rules. Another chance.',361,210,470,18,t['muted'])
            choices=[]
            if self.screen=='pause':choices.append(('Resume',self.resume))
            elif self.screen=='complete':
                choices.append(('Back to studio' if self.playtest else 'Campaign results' if self.completed_world else 'Next stage',lambda:self.route('ending') if self.completed_world else self.next_stage()))
            else:choices.append(('Retry / R',self.restart))
            if self.screen!='lost':choices.append(('Retry / R',self.restart))
            choices += [('Customize',lambda:self.settings_screen(self.screen)),
                        ('Controls / F1',self.show_help),
                        ('Back to studio' if self.playtest else 'Stage library',self.return_editor if self.playtest else lambda:self.route('stages')),
                        ('Main menu',lambda:self.route('home'))]
            for i,(label,action) in enumerate(choices):u.button(label,(361,319+i*57,478,43),action,primary=i==0)


    def draw_ending(self):
        u=self.ui;t=self.theme;u.header('CAMPAIGN RESULTS')
        originals=[stage for stage in self.catalog.stages if stage.original]
        count=sum(self.completed(stage) for stage in originals)
        all_done=count==len(originals)
        u.text('You turned every world.' if all_done else 'A new perspective.',40,110,48)
        u.wrap('All 15 original stages complete. Thank you for returning to this little Linux adventure.' if all_done else f'{self.completed_world} is complete. Another world is waiting.',44,190,1070,24)
        u.text(f'{count} / {len(originals)} STAGES COMPLETE',44,276,19,t['accent'])
        for i,world in enumerate(stages.WORLD_NAMES):
            group=[stage for stage in originals if stage.world==world]
            done=sum(self.completed(stage) for stage in group);y=332+i*83
            u.panel((40,y,1116,68));u.text(world,62,y+20,23)
            u.text(f'{done} / {len(group)}',1006,y+22,21,t['accent'])
        u.wrap('Original game by Olli “Hectigo” Etuaho. Refreshed by Mohtab Arabiat. Your times and stage creations make the next chapter yours.',44,598,1080,18,t['muted'])
        u.button('Replay a favorite' if all_done else 'Continue adventure',(40,687,288,44),lambda:self.route('stages') if all_done else self.start_stage(self.continue_stage()),primary=True)
        u.button('Personal bests',(348,687,240,44),lambda:self.route('records'))
        u.button('Credits',(608,687,240,44),lambda:self.route('credits'))
        u.button('Main menu',(868,687,288,44),lambda:self.route('home'))

    def draw_credits(self):
        u=self.ui;t=self.theme;u.header('CREDITS / A LINUX MEMORY')
        u.text('The first game. A new chapter.',40,109,38)
        u.text('REIMAGINED BY MOHTAB ARABIAT',44,179,14,t['accent'])
        u.wrap('Which Way Is Up? was the first game I tried when I started using Linux. This refresh is my way of returning to that first experience: keeping its playful spirit alive, and making room for new players, faster runs and worlds of their own.',44,214,1088,22)
        u.text('THE ORIGINAL PERSPECTIVE',44,353,14,t['accent'])
        u.wrap('Created by Olli “Hectigo” Etuaho in 2007. His original game design, stages, artwork, dialogue and sound effects are the foundation of this independent adaptation. Thank you to the Debian Games Team and the original contributors for keeping it available.',44,387,1088,19,t['muted'])
        u.text('BUILT TO BE SHARED',44,506,14,t['accent'])
        u.wrap('Code, new artwork and ambient music: GNU GPL version 2. Original content: Creative Commons Attribution 3.0. Font: Bitstream Vera license. Full notices are in CREDITS.md, LICENSE and licenses/original-copyright.',44,540,1088,18)
        u.wrap('Refresh direction: Mohtab Arabiat. AI coding assistance: Codex (OpenAI). The Omarchy / DHH cameo is unofficial and implies no endorsement. Community stages retain their own credits and licenses.',44,627,1088,15,t['muted'])
        u.button('Back to the game',(40,696,260,42),lambda:self.route('home'),primary=True)


    def draw_help(self):
        u=self.ui;t=self.theme;u.header('KEYBOARD FIELD GUIDE')
        u.text('Keep your hands on the keys.',40,108,36)
        columns=[('PLAY & NAVIGATE',[
            (self.s['key_left'].upper()+' / '+self.s['key_right'].upper()+' · A / D','Move'),
            (self.s['key_jump'].upper()+' · Space · Up','Jump / slow fall / dialogue'),
            (self.s['key_interact'].upper()+' · S · E','Collect items / use lever'),
            ('Esc / P','Pause / resume'),('R','Retry the current stage'),
            ('Tab / Shift+Tab','Next / previous menu item'),('Enter','Activate selected item'),
            ('Ctrl+S','Save stage, or settings + practice replay')]),
            ('WINDOW, SOUND & STUDIO',[
            ('F9','Board only / restore interface'),('F2 / F11','Window size / fullscreen'),('F6 / Shift+F6','Next / previous theme'),
            ('F10 / M','Settings / toggle music'),('Arrows / Space','Studio cursor / place selected tool'),
            ('[ / ] · Delete','Previous / next tool · erase cell'),('Ctrl+Z / Ctrl+Y','Undo / redo'),
            ('F5 / Ctrl+R','Playtest / rotate board'),('Ctrl+Shift+S','Export stage JSON')])]
        for col,(title,rows) in enumerate(columns):
            x=40+col*584;u.panel((x,178,550,478));u.text(title,x+22,200,13,t['accent'])
            for i,(key,action) in enumerate(rows):
                y=243+i*44
                u.fit(key,x+22,y,506,17)
                u.fit(action,x+22,y+23,506,13,t['muted'])
        u.text('Runs save on completion. A practice replay records inputs; it is not a resume checkpoint.',44,676,15,t['muted'])
        u.button('Back',(40,707,170,38),lambda:self.route(self.help_return),primary=True)


    def draw_records(self):
        u=self.ui;t=self.theme;u.header('PERSONAL BESTS / THIS DEVICE')
        u.text('Every second has a story.',40,107,36)
        u.wrap('Your fastest completed runs, separated by stage and rules. Times use the original in-game clock; pauses are excluded.',44,160,1080,17,t['muted'])
        entries=[v for v in self.store.records.values() if isinstance(v,dict) and isinstance(v.get('best_seconds'),(int,float))]
        entries.sort(key=lambda v:(v.get('stage',''),v.get('category','')))
        self.records_page=min(self.records_page,max(0,(len(entries)-1)//6))
        if not entries:
            u.panel((40,246,1116,210));u.text('Your first finish belongs here.',68,280,27)
            u.wrap('Choose a stage and reach its goal. We will save your time and replay automatically. Try the Speedrun preset to skip dialogue.',68,333,1010,19,t['muted'])
        for i,row in enumerate(entries[self.records_page*6:(self.records_page+1)*6]):
            y=231+i*68;u.panel((40,y,1116,58))
            u.fit(row.get('stage','Stage'),59,y+17,536,19)
            u.fit(row.get('category','Legacy record / category unknown'),624,y+20,295,13,t['muted'])
            u.text(runs.clock_text(row['best_seconds']),940,y+15,24,t['accent'])
        u.wrap('Global rankings and community uploads are planned. This board contains local records only.',44,666,1090,16,t['muted'])
        u.button('Back',(40,710,150,36),lambda:self.route('home'),primary=True)
        if self.records_page>0:u.button('Previous',(820,710,156,36),lambda:setattr(self,'records_page',self.records_page-1))
        if (self.records_page+1)*6<len(entries):u.button('Next',(992,710,164,36),lambda:setattr(self,'records_page',self.records_page+1))


    def board_notice(self,surface):
        if self.message_until<=time.monotonic():return
        lines=wrapped_lines(self.message,surface.get_width()-64,20)[:3]
        height=24+len(lines)*27
        panel=pygame.Surface((surface.get_width()-32,height),pygame.SRCALPHA)
        panel.fill((*self.theme['background'],242))
        for i,line in enumerate(lines):
            panel.blit(font(20).render(line,True,self.theme['foreground']),(16,12+i*27))
        rect=surface.blit(panel,(16,surface.get_height()-height-16))
        return rect
    def draw_board(self):
        world=self.painter.draw(self.session,self.theme,self.s,self.stepper.alpha)
        if self.s['compact_hud']:
            surface=pygame.Surface((1040,1120));surface.fill(self.theme['background']);surface.blit(world,(0,80))
            player=self.session.scene['player']
            clock=runs.clock_text(self.session.score.time/24/self.run_tempo)
            surface.blit(font(28).render(clock,True,self.theme['foreground']),(22,14))
            surface.blit(font(17).render('ATTEMPT '+str(self.attempts),True,self.theme['muted']),(24,48))
            pygame.draw.rect(surface,self.theme['panel'],(278,23,170,12),border_radius=5)
            pygame.draw.rect(surface,self.theme['accent'] if player.life>10 else self.theme['hazard'],(278,23,max(0,round(170*player.life/36)),12),border_radius=5)
            surface.blit(font(17).render('HEALTH '+str(max(0,player.life)),True,self.theme['foreground']),(278,46))
            goals={'key':'Find the key','other_pants':'Find the trousers','cake':'Find the cake','power_crystal':'Find the crystal'}
            objective=next((goals[e['trigger']] for e in self.active_stage.document['events'] if e['trigger'] in goals and 'change_level' in e['actions']),'Explore and turn the room')
            surface.blit(font(22).render(objective,True,self.theme['foreground']),(490,16))
            hint='Button 7 / 8: pause' if self.input_device=='controller' else 'Esc: pause  /  R: retry'
            surface.blit(font(17).render(hint,True,self.theme['muted']),(490,47))
        else:surface=world.copy()
        layers=[]
        if self.s['compact_hud']:
            layers.append((surface.subsurface((0,0,1040,80)).copy(),(0,0,1040,80),True,False,1))
        notice=self.board_notice(surface)
        if notice:layers.append((surface.subsurface(notice).copy(),notice,True,False,1))
        self.display.present(surface,smooth=self.s['smooth'] and self.theme.style!='original',
                             integer_scale=self.s['integer_scale'] and self.theme.style=='original',pixel_scale=self.painter.scale,layers=layers)

    def draw(self):
        self.world_layers=[]
        self.ui.begin(self.theme);self.painter.configure(self.theme,self.s)
        # Board-only never resizes/floats the OS window. Essential dialogue and
        # pause/settings screens temporarily restore the interface.
        if (self.s['board_only'] and self.screen=='play' and not self.session.scene['dialogue']
                and not self.modal and not self.display.deadline):
            self.draw_board();return
        if self.screen=='home':self.draw_home()
        elif self.screen=='stages':self.draw_stages()
        elif self.screen=='settings':self.draw_settings()
        elif self.screen=='editor':self.editor.draw(self)
        elif self.screen=='credits':self.draw_credits()
        elif self.screen=='ending':self.draw_ending()
        elif self.screen=='help':self.draw_help()
        elif self.screen=='records':self.draw_records()
        elif self.screen in ('play','pause','lost','complete'):self.draw_play()
        self.ui.footer()
        if self.modal:
            u=self.ui;t=self.theme
            overlay=pygame.Surface((1200,800),pygame.SRCALPHA);overlay.fill((0,0,0,170));u.surface.blit(overlay,(0,0))
            u.panel((190,280,820,235));u.fit(self.modal['title'],218,309,760,20)
            if 'value' in self.modal:
                shown=self.modal['value']
                while shown and font(18).size(shown+'|')[0]>740:shown=shown[1:]
                pygame.draw.rect(u.surface,t['background'],(216,360,768,54),border_radius=6)
                u.text(shown+'|',228,375,18,t['accent'])
            u.text('Press a key to bind  /  Esc to cancel' if 'binding' in self.modal else 'Enter to apply  /  Esc to cancel',218,461,15,t['muted'])
        if self.display.deadline:
            u=self.ui;u.buttons=[];u.panel((210,17,780,114))
            u.text('Keep fullscreen? '+str(max(0,int(self.display.deadline-time.monotonic())))+'s',232,31,22)
            u.button('Keep / Enter / Button 1',(232,73,352,42),self.display.confirm,primary=True)
            u.button('Revert / Esc / Button 2',(600,73,368,42),self.display.toggle)
        if self.message_until>time.monotonic():
            u=self.ui;u.panel((30,761,1140,36));u.fit(self.message,43,772,1110,13,self.theme['accent'])
        self.display.present(self.ui.surface,smooth=True,layers=self.world_layers)
    def run(self):
        clock=pygame.time.Clock();start=time.monotonic()
        self.draw()
        while self.running:
            dt=clock.tick(self.s['fps'])/1000
            cost=time.perf_counter()
            for event in pygame.event.get():
                try:self.event(event)
                except (ValueError,OSError,pygame.error) as e:
                    logging.exception('Action failed');self.pause();self.notify('Action could not finish: '+str(e))
            self.update(dt);self.draw()
            self.costs.append((time.perf_counter()-cost)*1000);self.frame_count+=1
            if self.args.smoke and time.monotonic()-start>=self.args.smoke:self.running=False
        if self.args.screenshot:
            capture=self.display.screen
            pygame.image.save(capture,self.args.screenshot)
        if self.editor and self.editor.dirty:
            try:self.editor.save(draft=True)
            except OSError:logging.exception('Could not save draft on exit')
        if not self.display.fullscreen:self.s['window']=list(self.display.screen.get_size())
        self.store.save()
        if self.costs:
            values=sorted(self.costs)
            logging.info('Frames=%d, CPU work median=%.2fms p95=%.2fms',self.frame_count,values[len(values)//2],values[int((len(values)-1)*.95)])
        pygame.quit()

def main(argv=None):
    parser=argparse.ArgumentParser(description='Which Way Is Up? — an independent Omarchy homage')
    parser.add_argument('--version',action='version',version=__version__)
    parser.add_argument('--safe-window',action='store_true',help='Start in a recoverable window')
    parser.add_argument('--theme',choices=THEME_ORDER)
    parser.add_argument('--play',action='store_true')
    parser.add_argument('-l','--stage')
    parser.add_argument('--screen',choices=('home','settings','stages','editor','credits'),help=argparse.SUPPRESS)
    parser.add_argument('--smoke',type=float,help=argparse.SUPPRESS)
    parser.add_argument('--screenshot',help=argparse.SUPPRESS)
    parser.add_argument('--import-stage',dest='import_file',help='Validate and import a local JSON/TXT stage')
    args=parser.parse_args(argv)
    logging.basicConfig(filename=user_path('state')/'refresh.log',level=logging.INFO,format='%(asctime)s %(levelname)s %(message)s')
    if args.import_file:
        print(stages.import_stage(Path(args.import_file).expanduser()));return
    try:App(args).run()
    except Exception:
        logging.exception('Unhandled application error')
        traceback.print_exc()
        raise
