"""Refresh-only room-led layouts. Actions and state remain owned by App."""
import pygame
from . import runs, stages, __version__
from .ui import metal_panel

BOARD=(484,76,680,680)
DIALOGUE_WIDTH=352
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

def health(surface,rect,value,theme):
    rect=pygame.Rect(rect);surface.blit(metal_panel(rect.size,theme['panel'],theme['accent']),rect)
    color=theme['accent'] if value>10 else theme['hazard']
    for i in range(12):
        x=rect.x+7+i*(rect.w-14)/12;width=max(2,int((rect.w-14)/12)-3)
        if i<max(0,value)/3:
            cell=pygame.Rect(x,rect.y+5,width,max(2,rect.h-10))
            pygame.draw.rect(surface,color,cell)
            pygame.draw.line(surface,(246,220,158),cell.topleft,cell.topright)
            pygame.draw.line(surface,(71,49,28),cell.bottomleft,cell.bottomright,2)

def play(app):
    u=app.ui;t=app.theme;s=app.session;scene=s.scene;talk=bool(scene['dialogue'])
    u.header('WHICH WAY IS UP?  /  '+('STUDIO PLAYTEST' if app.playtest else app.active_stage.world.upper()))
    u.panel((476,68,696,696));app.blit_world(s,BOARD)
    goals={'key':'Find the key','other_pants':'Find the trousers','cake':'Find the cake','power_crystal':'Find the crystal'}
    objective=next((goals[e['trigger']] for e in app.active_stage.document['events'] if e['trigger'] in goals and 'change_level' in e['actions']),'Explore and turn the room')
    if talk:
        lines=app.dialogue_lines();pages=max(1,(len(lines)+5)//6);visible=lines[app.dialogue_page*6:(app.dialogue_page+1)*6]
        u.text('A word from Guy',48,100,32)
        height=max(184,156+28*len(visible));u.panel((32,160,420,height))
        for i,line in enumerate(visible):u.text(line,66,201+i*28,20)
        y=201+len(visible)*28+26
        u.text(('Next page' if app.dialogue_page+1<pages else 'Continue')+f'    {app.dialogue_page+1}/{pages}',66,y,19,t['accent'])
        hint='Button 1 / Button 2' if app.input_device=='controller' else f"{app.s['key_jump'].upper()} / Space / {app.s['key_interact'].upper()}"
        u.wrap(hint,66,y+31,352,17,t['muted'],limit=2)
        u.text(objective,48,548,18,t['muted'])
        u.text('Time '+runs.clock_text(s.score.time/24/app.run_tempo),48,592,18,t['muted'])
        u.text('Health '+str(max(0,scene['player'].life)),288,592,18,t['muted'])
    else:
        u.wrap(stages.display_name(app.active_stage),48,96,396,23,limit=2)
        u.text(objective,48,173,30)
        u.panel((32,234,420,180))
        u.text('RUN TIME',58,262,16,t['muted']);u.text(runs.clock_text(s.score.time/24/app.run_tempo),56,291,30)
        u.text(f'Attempt {app.attempts:02d}',58,346,18,t['muted'])
        u.text('PERSONAL BEST',268,262,16,t['muted'])
        u.text(runs.clock_text(app.previous_best) if app.previous_best is not None else 'No finish yet',268,300,18)
        u.text(f"{app.run_tempo:g}× · {'Story' if app.run_dialogue else 'Speedrun'}",268,346,17,t['muted'])
        u.text('HEALTH  '+str(max(0,scene['player'].life)),48,439,18)
        health(u.surface,(184,433,250,28),scene['player'].life,t)
        rows=[('Move',f"{app.s['key_left'].upper()} / {app.s['key_right'].upper()} · A / D"),('Jump',f"{app.s['key_jump'].upper()} / Space / Up"),('Interact',f"{app.s['key_interact'].upper()} / S / E")]
        for i,(label,value) in enumerate(rows):
            y=490+i*37;u.text(label,48,y,18,t['accent']);u.text(value,161,y,18,t['muted'])
        u.text('Hold jump to slow your fall.',48,616,18,t['muted'])
    u.button('Pause / Esc',(42,690,196,48),app.pause)
    u.button('Retry / R',(252,690,196,48),app.restart)

def compact_frame(surface,theme):
    surface.blit(metal_panel((1040,80),theme['background'],theme['accent']),(0,0))
    pygame.draw.line(surface,theme['accent'],(0,78),(1040,78))


def complete(app):
    """Resolved real room and final actions; no obsolete active-run HUD."""
    u=app.ui;t=app.theme;s=app.session
    u.header('WHICH WAY IS UP?  /  '+('STUDIO PLAYTEST' if app.playtest else app.active_stage.world.upper()))
    u.panel((476,68,696,696));app.blit_world(s,BOARD,resolved=True)
    u.text('Campaign clear!' if app.completed_world else 'Stage clear.',48,94,38)
    u.fit(stages.display_name(app.active_stage),48,150,396,18,t['muted'])
    u.panel((32,194,420,176))
    u.text('FINISH TIME',62,221,16,t['muted'])
    u.text(runs.clock_text(s.score.time/24/app.run_tempo),60,250,36)
    detail=('Playtest complete' if app.playtest else 'Save failed · Ctrl+S to retry' if not app.completion_saved
            else 'New personal best!' if app.new_best else 'Personal best: '+runs.clock_text(app.previous_best or 0))
    u.fit(detail,62,312,356,18,t['accent'])
    if app.previous_best is not None:
        delta=s.score.time/24/app.run_tempo-app.previous_best
        u.fit('Equal to your best' if abs(delta)<.0005 else f'{abs(delta):.3f}s '+('faster than your best' if delta<0 else 'behind your best'),48,385,396,17,t['muted'])
    choices=[('Back to studio' if app.playtest else 'Campaign results' if app.completed_world else 'Next stage',lambda:app.route('ending') if app.completed_world else app.next_stage()),
             ('Retry / R',app.restart),('Customize',lambda:app.settings_screen('complete')),
             ('Controls / F1',app.show_help),('Back to studio' if app.playtest else 'Stage library',app.return_editor if app.playtest else lambda:app.route('stages')),('Main menu',lambda:app.route('home'))]
    for i,(label,action) in enumerate(choices):u.button(label,(42,425+i*54,406,46),action,primary=i==0)
