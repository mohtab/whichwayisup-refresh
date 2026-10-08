"""Refresh-only room-led layouts. Actions and state remain owned by App."""
import pygame
from . import runs, stages, __version__
from .ui import metal_panel

BOARD=(260,76,680,680)
DIALOGUE_WIDTH=180
DIALOGUE_LINES=6

def home(app):
    u=app.ui;t=app.theme
    u.header('REFRESH EDITION  /  '+__version__)
    u.text('Which Way',40,115,52);u.text('Is Up?',40,175,52)
    pygame.draw.line(u.surface,t['accent'],(44,252),(168,252),3)
    u.text('A little gravity. A lot of possibility.',44,262,19)
    u.wrap('Find the key. Flip the room. A Linux favorite, revisited by Mohtab Arabiat.',44,291,430,18,t['muted'])
    stage=app.continue_stage();started=any(key!='legacy_import' for key in app.store.records)
    u.fit('NEXT / '+app.short_name(stage),44,397,430,15,t['muted'])
    # Primary first in keyboard/controller navigation order.
    u.button('Continue' if started else 'Play',(44,420,430,50),lambda:app.start_stage(stage),primary=True)
    u.button('Choose a stage',(44,482,430,46),lambda:app.route('stages'))
    u.button('Personal bests',(44,540,208,46),lambda:app.route('records'))
    u.button('Stage studio',(266,540,208,46),lambda:app.new_editor())
    u.button('Customize',(44,596,208,46),lambda:app.settings_screen('home'))
    u.button('Credits',(266,596,208,46),lambda:app.route('credits'))
    u.button('Story',(44,345,208,44),lambda:app.preset('story'),selected=app.s['dialogue'] and app.s['tempo']==1.)
    u.button('Speedrun',(266,345,208,44),lambda:app.preset('speedrun'),selected=not app.s['dialogue'] and app.s['tempo']==1.)
    for i,ident in enumerate(('original','refresh','omarchy','system','cyberpunk')):
        rect=(44+i*146,656,138,44) if i<3 else (44+(i-3)*222,708,208,44)
        u.button(app.themes.packs[ident].name,rect,lambda v=ident:app.set_theme(v),selected=app.s['theme']==ident)
    u.panel((532,98,628,628));app.blit_world(app.preview,(540,106,612,612),True)
    originals=[s for s in app.catalog.stages if s.original]
    u.text(f'{sum(app.completed(s) for s in originals)} / {len(originals)} STAGES COMPLETE',548,735,16,t['muted'])
    u.button('Quit',(1064,18,92,44),lambda:setattr(app,'running',False))

def play(app):
    u=app.ui;t=app.theme;s=app.session;scene=s.scene
    u.header('WHICH WAY IS UP?  /  '+('STUDIO PLAYTEST' if app.playtest else app.active_stage.world.upper()))
    u.panel((254,70,692,692));app.blit_world(s,BOARD)
    u.wrap(stages.display_name(app.active_stage),32,96,204,20,limit=3)
    u.text('RUN TIME',32,180,14,t['muted'])
    u.text(runs.clock_text(s.score.time/24/app.run_tempo),30,205,28)
    u.text(f'ATTEMPT {app.attempts:02d}',32,253,15,t['muted'])
    pygame.draw.line(u.surface,t['panel'],(32,284),(232,284),2)
    u.text('PERSONAL BEST',32,310,14,t['accent'])
    u.text(runs.clock_text(app.previous_best) if app.previous_best is not None else 'No finish yet',32,338,19)
    u.wrap(f"{app.run_tempo:g}× tempo\n{'Story' if app.run_dialogue else 'Dialogue skipped'}\nLocal in-game time",32,395,200,17,t['muted'])
    u.text('HEALTH  '+str(max(0,scene['player'].life)),32,516,16)
    pygame.draw.rect(u.surface,t['panel'],(32,550,196,12))
    pygame.draw.rect(u.surface,t['accent'] if scene['player'].life>10 else t['hazard'],(32,550,max(0,min(196,196*scene['player'].life/36)),12))
    goals={'key':'Find the key','other_pants':'Find the trousers','cake':'Find the cake','power_crystal':'Find the crystal'}
    objective=next((goals[e['trigger']] for e in app.active_stage.document['events'] if e['trigger'] in goals and 'change_level' in e['actions']),'Explore and turn the room')
    u.text('OBJECTIVE',968,98,14,t['accent']);u.wrap(objective,968,125,194,20,limit=3)
    if scene['dialogue']:
        lines=app.dialogue_lines();pages=max(1,(len(lines)+5)//6);visible=lines[app.dialogue_page*6:(app.dialogue_page+1)*6]
        height=max(180,100+26*len(visible));u.panel((958,210,216,height))
        u.text('GUY',976,225,14,t['accent'])
        for i,line in enumerate(visible):u.text(line,976,254+i*26,18)
        y=254+len(visible)*26+12
        u.text(('NEXT PAGE' if app.dialogue_page+1<pages else 'CONTINUE')+f'  {app.dialogue_page+1}/{pages}',976,y,14,t['accent'])
        hint='Button 1 / 2' if app.input_device=='controller' else f"{app.s['key_jump'].upper()} / Space / {app.s['key_interact'].upper()}"
        u.wrap(hint,976,y+23,180,14,t['muted'],limit=2)
    else:
        rows=[('MOVE',f"{app.s['key_left'].upper()} / {app.s['key_right'].upper()}\nA / D"),('JUMP',f"{app.s['key_jump'].upper()} / Space / Up"),('INTERACT',f"{app.s['key_interact'].upper()} / S / E")]
        for i,(label,value) in enumerate(rows):
            y=220+i*90;u.text(label,968,y,14,t['accent']);u.wrap(value,968,y+25,194,17,t['muted'])
        u.wrap('Button 1 jumps. Button 2 interacts.' if app.input_device=='controller' else 'Hold jump to slow your fall.',968,511,194,17,t['muted'])
    u.button('Pause / Esc',(968,636,196,48),app.pause)
    u.button('Retry / R',(968,696,196,48),app.restart)

def compact_frame(surface,theme):
    surface.blit(metal_panel((1040,80),theme['background'],theme['accent']),(0,0))
    pygame.draw.line(surface,theme['accent'],(0,78),(1040,78))
