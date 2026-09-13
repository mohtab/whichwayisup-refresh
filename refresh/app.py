"""Desktop application for the Which Way Is Up? homage."""
import argparse
from collections import deque
import json
import logging
import os
from pathlib import Path
import time
import traceback

import pygame
from .storage import Store, user_path, atomic_json
from .themes import Themes, color
from .runtime import Session, Stepper
from .art import Painter
from .ui import UI, font
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
        self.last_poll=0.;self.last_autosave=0.;self.axis_ready=True
        self.costs=deque(maxlen=600);self.frame_count=0
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
    def notify(self,message):self.message=str(message);self.message_until=time.monotonic()+7
    def route(self,screen):
        self.screen=screen;self.ui.focus=0;self.held.clear();self.pending.clear();self.stepper.reset()
    def set_theme(self,ident):
        self.s['theme']=ident;self.s['accent']=''
        self.theme=self.themes.get(self.s);self.painter.configure(self.theme,self.s);self.store.save()
    def setting(self,key,values):
        current=self.s.get(key)
        self.s[key]=values[(values.index(current)+1)%len(values)] if current in values else values[0]
        self.theme=self.themes.get(self.s)
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
        self.active_stage=stage;self.run_tempo=self.s['tempo'];self.playtest=playtest
        settings=dict(self.s,sound=self.s['sound'] and self.audio)
        self.session=Session(stage.engine_path,settings)
        self.s['stage']=stage.id
        if not playtest:self.store.save()
        self.route('play')
    def pause(self):
        if self.screen=='play':self.route('pause')
    def resume(self):
        if self.session:
            Variables.vdict.update(sound=self.s['sound'] and self.audio,dialogue=self.s['dialogue'])
            self.route('play')
    def restart(self):
        if self.active_stage:self.start_stage(self.active_stage,self.playtest)
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
            key=stages.fingerprint(self.active_stage.document)+f':legacy24-v1:{self.run_tempo}'
            previous=self.store.records.get(key,{})
            if not self.playtest:
                self.store.records[key]={'stage':self.active_stage.title,'best_seconds':min(seconds,previous.get('best_seconds',seconds)),
                                         'legacy_ticks':self.session.score.time,'tempo':self.run_tempo,'rules':'legacy24-v1'}
                self.store.save_records()
                replay=dict(schema=1,stage_hash=stages.fingerprint(self.active_stage.document),rules='legacy24-v1',tempo=self.run_tempo,
                            seed=self.session.seed,inputs=self.session.history,complete=not getattr(self.session,'history_truncated',False))
                atomic_json(user_path('data')/'last-completion-replay.json',replay)
            self.route('complete')
        elif result==1:self.route('lost')
        else:self.route('pause')
    def next_stage(self):
        if self.playtest:self.return_editor();return
        index=next((i for i,s in enumerate(self.catalog.stages) if s.id==self.active_stage.id),0)
        if index+1<len(self.catalog.stages):self.start_stage(self.catalog.stages[index+1])
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
        if event.type==pygame.QUIT:
            logging.info('Received QUIT on %s',self.screen);self.running=False;return
        if event.type==pygame.WINDOWFOCUSLOST:
            self.focused=False;self.held.clear();self.pending.clear();self.pause();return
        if event.type==pygame.WINDOWFOCUSGAINED:self.focused=True;return
        if event.type in (pygame.JOYDEVICEADDED,pygame.JOYDEVICEREMOVED):
            if event.type==pygame.JOYDEVICEREMOVED:self.pause()
            self.reload_joysticks();return
        if event.type==pygame.DROPFILE:
            try:self.import_file(event.file);self.route('stages')
            except (ValueError,OSError) as e:self.notify(e)
            return
        if self.modal:
            if event.type==pygame.KEYDOWN:
                if event.key==pygame.K_ESCAPE:self.modal=None;pygame.key.stop_text_input();return
                if 'binding' in self.modal:
                    name=pygame.key.name(event.key)
                    reserved=(pygame.K_F11,pygame.K_TAB,pygame.K_RETURN,pygame.K_p)
                    if event.key in reserved:self.notify('Choose a key other than a menu or fullscreen shortcut.');return
                    action=self.modal['binding']
                    conflicts={self.s['key_'+a] for a in ('left','right','jump','interact') if a!=action}
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
            if event.key==pygame.K_F11:
                try:self.display.toggle()
                except pygame.error as e:self.notify('Display change failed: '+str(e))
                self.pause();return
            if self.display.deadline:
                if event.key==pygame.K_RETURN:self.display.confirm();return
                if event.key==pygame.K_ESCAPE:self.display.toggle();return
            if self.screen=='play':
                if event.key in (pygame.K_ESCAPE,pygame.K_p):self.pause();return
                if event.key==pygame.K_r:self.restart();return
                self.held.add(event.key)
                action=self.action_for(event.key)
                if action:self.pending.add(action)
                return
            if self.screen=='editor' and event.mod & pygame.KMOD_CTRL:
                if event.key==pygame.K_z:self.editor.go_undo()
                if event.key==pygame.K_y:self.editor.go_redo()
                if event.key==pygame.K_s:self.editor_save()
                return
            if event.key==pygame.K_ESCAPE:
                if self.screen=='pause':self.resume()
                elif self.screen=='editor':self.leave_editor()
                elif self.screen=='settings':self.route(self.return_screen)
                else:self.route('home')
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
                if event.button==0:self.pending.add('jump')
                elif event.button==1:self.pending.add('interact')
                elif event.button in (6,7):self.pause()
            elif event.button==0:self.ui.activate()
            elif event.button==1:
                if self.screen=='pause':self.resume()
                else:self.route('home')
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
            self.editor.save(draft=True);self.last_autosave=now
        if self.screen=='play':
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
        alpha=1 if not self.s['effects'] else (self.preview_clock.alpha if preview else self.stepper.alpha)
        image=self.painter.draw(session,self.theme,self.s,alpha if self.screen=='play' or preview else 1,preview)
        transform=pygame.transform.smoothscale if self.s['smooth'] and self.theme.style!='original' else pygame.transform.scale
        self.ui.surface.blit(transform(image,(rect[2],rect[3])),rect[:2])
        pygame.draw.rect(self.ui.surface,self.theme['accent'],rect,1,border_radius=2)
    def settings_screen(self,back):self.return_screen=back;self.route('settings')
    def draw_home(self):
        u=self.ui;t=self.theme
        u.header('OMARCHY REFRESH / 0.1')
        u.text('A CHANGE OF PERSPECTIVE',40,114,14,t['accent'])
        u.text('Which way',36,151,64)
        u.text('is up?',36,220,64)
        u.wrap('An old favorite. A new perspective.',40,320,490,25)
        u.wrap('Jump, pull a lever, turn your world around. Explore the original stages in a design that feels like you.',40,372,470,19,t['muted'])
        stage=self.catalog.stages[self.stage_index]
        u.button('Play  /  '+stage.id,(40,493,270,54),lambda:self.start_stage(stage),primary=True)
        u.button('Choose a stage',(326,493,240,54),lambda:self.route('stages'))
        u.button('Customize',(40,563,167,44),lambda:self.settings_screen('home'))
        u.button('Stage studio',(219,563,167,44),lambda:self.new_editor())
        u.button('Credits',(398,563,168,44),lambda:self.route('credits'))
        self.blit_world(self.preview,(632,112,520,520),True)
        u.text(t.name.upper(),650,645,13,t['accent'])
        u.text('CHOOSE YOUR WORLD',40,646,13,t['muted'])
        for i,ident in enumerate(THEME_ORDER):
            pack=self.themes.packs[ident]
            u.button(pack.name,(40+i*226,679,214,52),lambda v=ident:self.set_theme(v),selected=self.s['theme']==ident)
        u.button('Quit',(1066,27,86,31),lambda:setattr(self,'running',False))
    def draw_stages(self):
        u=self.ui;t=self.theme;u.header('CAMPAIGNS / YOUR STAGES')
        u.text('Every world starts with a stage.',40,101,34)
        u.text('All 15 original stages are available. Your imported stages appear here too.',40,147,16,t['muted'])
        subset=self.catalog.stages[self.page*12:self.page*12+12]
        for i,stage in enumerate(subset):
            x=40+(i%3)*378;y=192+(i//3)*111
            u.panel((x,y,362,95))
            u.text(stage.world.upper(),x+16,y+13,12,t['accent'])
            label=stage.title if not stage.original else 'Stage '+str(int(stage.id.split('-l')[-1])+1)+'  /  '+stage.id
            u.button(label,(x+12,y+38,236,43),lambda v=stage:self.start_stage(v),primary=False)
            u.button('Remix',(x+258,y+38,92,43),lambda v=stage:self.new_editor(v.document))
        u.button('Back',(40,676,130,44),lambda:self.route('home'))
        u.button('New stage',(184,676,170,44),lambda:self.new_editor(),primary=True)
        u.button('Import file',(368,676,170,44),self.import_prompt)
        u.button('Resume draft',(552,676,166,44),self.resume_draft)
        if self.page>0:u.button('Previous',(760,676,170,44),lambda:setattr(self,'page',self.page-1))
        if (self.page+1)*12<len(self.catalog.stages):u.button('Next',(944,676,170,44),lambda:setattr(self,'page',self.page+1))
        u.text('Drop a stage JSON into the window to import it. Built-in stages stay unchanged.',40,737,14,t['muted'])
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
        u=self.ui;t=self.theme;u.header('MAKE IT YOURS')
        u.text('Your game. Your atmosphere.',40,102,31)
        theme_ids=list(THEME_ORDER)+[k for k in self.themes.packs if k not in THEME_ORDER]
        rows=[('World design',t.name,lambda:self.setting('theme',theme_ids)),
              ('Character',{'theme':'Theme default','original':'Original Guy','guy':'Refresh Guy','dhh':'DHH cameo'}[self.s['character']],lambda:self.setting('character',['theme','original','guy','dhh'])),
              ('Tempo  /  next run',f"{self.s['tempo']:g}×",lambda:self.setting('tempo',[.75,1.,1.25,1.5])),
              ('Display refresh',str(self.s['fps'])+' FPS',lambda:self.setting('fps',[30,60,120,144,240])),
              ('Motion & effects','On' if self.s['effects'] else 'Reduced',lambda:self.setting('effects',[True,False])),
              ('Original sounds','On' if self.s['sound'] and self.audio else 'Off / unavailable',lambda:self.setting('sound',[True,False])),
              ('Original dialogue','On' if self.s['dialogue'] else 'Skip',lambda:self.setting('dialogue',[True,False])),
              ('World scaling','Smooth' if self.s['smooth'] else 'Crisp',lambda:self.setting('smooth',[False,True])),
              ('Accent override',self.s['accent'] or 'Theme default',lambda:self.prompt('Accent hex color (#rrggbb), or blank to reset',self.s['accent'],self.set_accent))]
        for i,(label,value,action) in enumerate(rows):
            y=169+i*48;u.text(label,44,y+9,17,t['muted']);u.button(value,(302,y,294,38),action)
        self.blit_world(self.preview,(652,169,500,500),True)
        u.text(t.subtitle,652,687,14,t['muted'])
        for i,action in enumerate(('left','right','jump','interact')):
            u.button(action.title()+': '+self.s['key_'+action],(40+i*143,621,133,37),lambda v=action:self.remap(v))
        u.button('Done',(40,686,160,43),lambda:self.route(self.return_screen),primary=True)
        u.button('Save theme pack',(216,686,190,43),self.export_theme)
        u.button('Reset accent',(422,686,174,43),lambda:self.set_accent(''))
    def draw_play(self):
        u=self.ui;t=self.theme;session=self.session;scene=session.scene
        u.header('STUDIO PLAYTEST' if self.playtest else self.active_stage.world.upper())
        self.blit_world(session,(40,120,620,620))
        u.text(self.active_stage.title,40,91,17,t['muted'])
        u.text('KEEP YOUR',710,125,27)
        u.text('PERSPECTIVE.',710,161,37)
        u.panel((700,229,460,124))
        u.text('LIFE',721,246,12,t['muted'])
        pygame.draw.rect(u.surface,t['background'],(721,272,270,12),border_radius=6)
        pygame.draw.rect(u.surface,t['accent'],(721,272,max(0,270*scene['player'].life/36),12),border_radius=6)
        u.text(f"{max(0,scene['player'].life)} / 36",1006,266,16)
        u.text(f"{session.score.time/24/self.run_tempo:06.2f}s    ·    {self.run_tempo:g}× tempo",721,309,18,t['muted'])
        u.text(t.name.upper(),712,383,14,t['accent'])
        dialogue=scene['dialogue']
        if dialogue:
            u.wrap(dialogue,712,418,420,19,limit=7)
            u.text('Jump / interact to continue',712,623,14,t['accent'])
        else:
            u.wrap('Move: ← → or A / D\nJump: Z, Space or ↑\nHold jump to slow your fall.',712,425,414,19,t['muted'])
            u.wrap('↓ / E  Pick up a key or pull a lever.\nEsc / P  Pause     R  Restart',712,528,414,17,t['muted'])
        u.button('Pause',(712,672,206,45),self.pause)
        u.button('Restart',(934,672,206,45),self.restart)
        if self.screen!='play':
            shade=pygame.Surface((1200,800),pygame.SRCALPHA);shade.fill((0,0,0,165));u.surface.blit(shade,(0,0))
            u.buttons=[]
            u.panel((340,175,520,445))
            title={'pause':'Take a breath.','lost':'Another perspective?','complete':'A new way forward.'}[self.screen]
            u.text(title,375,211,29)
            if self.screen=='complete':u.text('Stage complete. Nicely turned.',375,258,18,t['muted'])
            elif self.screen=='lost':u.text('Try again, or adjust the tempo.',375,258,18,t['muted'])
            else:u.text('The world can wait.',375,258,18,t['muted'])
            choices=[]
            if self.screen=='pause':choices.append(('Resume',self.resume))
            elif self.screen=='complete':choices.append(('Back to studio' if self.playtest else 'Next stage',self.next_stage))
            else:choices.append(('Try again',self.restart))
            choices += [('Customize',lambda:self.settings_screen(self.screen)),('Back to studio' if self.playtest else 'Stage library',self.return_editor if self.playtest else lambda:self.route('stages')),('Main menu',lambda:self.route('home'))]
            for i,(label,action) in enumerate(choices):u.button(label,(375,307+i*62,450,48),action,primary=i==0)
    def draw_credits(self):
        u=self.ui;t=self.theme;u.header('AN HOMAGE, WITH GRATITUDE')
        u.text('The original perspective.',40,110,42)
        u.wrap('Which Way Is Up? was created by Olli “Hectigo” Etuaho in 2007. This independent refresh preserves his original game, stages, artwork, dialogue and sounds as a playable design.',40,183,1040,24)
        u.wrap('Thanks also to the Debian Games Team and the original contributors for preserving and maintaining the game. The new interface, palette-driven art and Omarchy integration are adaptation work, not a claim of authorship of the original game.',40,305,1040,21,t['muted'])
        u.wrap('Code: GNU GPL version 2. Original game content: CC BY 3.0. Vera font: Bitstream Vera license. New code-drawn artwork: GPL version 2. Full notices and source accompany this build.',40,444,1040,20)
        u.wrap('The Omarchy / DHH character is an unofficial stylized fan-art cameo. No affiliation or endorsement is implied. New stages retain their creator credits and declared licenses.',40,553,1040,18,t['muted'])
        u.button('Back to the game',(40,682,280,48),lambda:self.route('home'),primary=True)
    def draw(self):
        self.ui.begin(self.theme);self.painter.configure(self.theme,self.s)
        if self.screen=='home':self.draw_home()
        elif self.screen=='stages':self.draw_stages()
        elif self.screen=='settings':self.draw_settings()
        elif self.screen=='editor':self.editor.draw(self)
        elif self.screen=='credits':self.draw_credits()
        elif self.screen in ('play','pause','lost','complete'):self.draw_play()
        self.ui.footer()
        if self.modal:
            u=self.ui;t=self.theme
            overlay=pygame.Surface((1200,800),pygame.SRCALPHA);overlay.fill((0,0,0,170));u.surface.blit(overlay,(0,0))
            u.panel((190,280,820,235));u.text(self.modal['title'],218,309,20)
            if 'value' in self.modal:
                shown=self.modal['value'][-65:]
                pygame.draw.rect(u.surface,t['background'],(216,360,768,54),border_radius=6)
                u.text(shown+'|',228,375,18,t['accent'])
            u.text('Enter to save  /  Esc to cancel',218,461,15,t['muted'])
        if self.display.deadline:
            u=self.ui;u.panel((210,17,780,62));u.text('Keep fullscreen? Enter to keep · Esc to revert · '+str(max(0,int(self.display.deadline-time.monotonic())))+'s',232,35,18)
        if self.message_until>time.monotonic():
            u=self.ui;u.panel((30,723,1140,36));u.text(self.message[:130],43,732,13,self.theme['accent'])
        self.display.present(self.ui.surface)
    def run(self):
        clock=pygame.time.Clock();start=time.monotonic()
        self.draw()
        while self.running:
            dt=clock.tick(self.s['fps'])/1000
            cost=time.perf_counter()
            for event in pygame.event.get():self.event(event)
            self.update(dt);self.draw()
            self.costs.append((time.perf_counter()-cost)*1000);self.frame_count+=1
            if self.args.smoke and time.monotonic()-start>=self.args.smoke:self.running=False
        if self.args.screenshot:
            pygame.image.save(self.ui.surface,self.args.screenshot)
        if self.editor and self.editor.dirty:self.editor.save(draft=True)
        if not self.display.fullscreen:self.s['window']=list(self.display.screen.get_size())
        self.store.save()
        if self.costs:
            values=sorted(self.costs)
            logging.info('Frames=%d, CPU work median=%.2fms p95=%.2fms',self.frame_count,values[len(values)//2],values[int((len(values)-1)*.95)])
        pygame.quit()

def main(argv=None):
    parser=argparse.ArgumentParser(description='Which Way Is Up? — an independent Omarchy homage')
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
