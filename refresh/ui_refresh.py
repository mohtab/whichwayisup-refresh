"""Authored room-led layouts. Actions and state remain owned by App."""
import pygame
from . import runs, stages, __version__
from .ui import metal_panel, palette_panel, wrapped_lines

BOARD=(416,68,704,704)
RESULT_BOARD=(484,76,680,680)
DIALOGUE_WIDTH=304
DIALOGUE_SIZE=24
DIALOGUE_LINES=6

def home(app):
    u=app.ui;t=app.theme
    u.header(('REFRESH EDITION' if t.id=='refresh' else t.name.upper())+'  /  '+__version__)
    u.fit(app.rules_notice(),44,82,470,16,t['muted'])
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
    rect=pygame.Rect(rect);surface.blit((metal_panel if theme.id=='refresh' else palette_panel)(rect.size,theme['panel'],theme['accent']),rect)
    color=theme['accent'] if value>10 else theme['hazard']
    for i in range(12):
        x=rect.x+7+i*(rect.w-14)/12;width=max(2,int((rect.w-14)/12)-3)
        if i<max(0,value)/3:
            cell=pygame.Rect(x,rect.y+5,width,max(2,rect.h-10))
            pygame.draw.rect(surface,color,cell)
            pygame.draw.line(surface,(246,220,158),cell.topleft,cell.topright)
            pygame.draw.line(surface,(71,49,28),cell.bottomleft,cell.bottomright,2)

def play(app):
    from . import chamber
    u=app.ui;t=app.theme;s=app.session;scene=s.scene;talk=bool(scene['dialogue'])
    if t.id=='refresh':u.surface.blit(chamber.surround((1200,800)),(0,0))
    u.header('WHICH WAY IS UP?  /  '+('STUDIO PLAYTEST' if app.playtest else app.active_stage.world.upper()))
    u.panel((408,60,720,720));app.blit_world(s,BOARD)
    goals={'key':'Find the key','other_pants':'Find the trousers','cake':'Find the cake','power_crystal':'Find the crystal'}
    objective=next((goals[e['trigger']] for e in app.active_stage.document['events'] if e['trigger'] in goals and 'change_level' in e['actions']),'Explore and turn the room')
    if talk:
        speech(app)
        return
    height=310+36*(min(2,len(wrapped_lines(objective,296,28)))-1)
    top=max(100,418-height//2)
    u.panel((32,top,360,height))
    x=62;y=top+24
    u.fit(app.rules_notice(),x,y,296,18,t['muted']);y+=34
    u.fit(app.short_name(app.active_stage),x,y,296,18,t['muted']);y+=32
    y=u.wrap(objective,x,y,296,28,limit=2)+10
    u.text(runs.clock_text(s.score.time/24/app.run_tempo),x,y,28);y+=38
    if not talk:
        u.fit('Best '+(runs.clock_text(app.previous_best) if app.previous_best is not None else '—')+f'  /  Attempt {app.attempts:02d}',x,y,296,17,t['muted']);y+=30
    u.text('Health '+str(max(0,scene['player'].life)),x,y,17)
    health(u.surface,(x+108,y-3,188,24),scene['player'].life,t);y+=38
    u.button('Pause / Esc',(x,y,142,44),app.pause)
    u.button('Retry / R',(x+154,y,142,44),app.restart)


def speech(app):
    from .portrait import speaker
    u=app.ui;t=app.theme
    # One stable portrait and speech anchor. No run-status machinery in this state.
    u.surface.blit(speaker(),(48,100))
    u.text('GUY',68,398,18,t['accent'])
    lines=app.dialogue_lines();pages=max(1,(len(lines)+5)//6)
    visible=lines[app.dialogue_page*6:(app.dialogue_page+1)*6]
    cue_y=450+32*len(visible)+22
    reading=pygame.Surface((344,cue_y-432+72),pygame.SRCALPHA);reading.fill((*t['background'],224))
    u.surface.blit(reading,(48,432))
    pygame.draw.line(u.surface,t['accent'],(68,434),(126,434),2)
    for i,line in enumerate(visible):u.text(line,68,450+i*32,DIALOGUE_SIZE,t['foreground'])
    label='Next page' if app.dialogue_page+1<pages else 'Continue'
    if pages>1:label+=f'  {app.dialogue_page+1}/{pages}'
    u.text(label,68,cue_y,20,t['accent'])
    hint='Button 1 / Button 2' if app.input_device=='controller' else f"{app.s['key_jump'].upper()} / Space / {app.s['key_interact'].upper()}"
    u.fit(hint,68,cue_y+32,304,18,t['foreground'])


def compact_frame(surface,theme):
    surface.blit((metal_panel if theme.id=='refresh' else palette_panel)((1040,80),theme['background'],theme['accent']),(0,0))
    pygame.draw.line(surface,theme['accent'],(0,78),(1040,78))


def complete(app):
    """Resolved real room and final actions; no obsolete active-run HUD."""
    u=app.ui;t=app.theme;s=app.session
    u.header('WHICH WAY IS UP?  /  '+('STUDIO PLAYTEST' if app.playtest else app.active_stage.world.upper()))
    u.panel((476,68,696,696));app.blit_world(s,RESULT_BOARD,resolved=True)
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


def records(app):
    from . import chamber,rules
    u=app.ui;t=app.theme
    if t.id=='refresh':u.surface.blit(chamber.surround((1200,800)),(0,0))
    u.header('PERSONAL BESTS / THIS DEVICE')
    entries=[v for v in app.store.records.values() if isinstance(v,dict) and isinstance(v.get('best_seconds'),(int,float))]
    entries.sort(key=lambda v:(v.get('stage',''),v.get('category','')))
    app.records_page=min(app.records_page,max(0,(len(entries)-1)//6))
    rows=entries[app.records_page*6:(app.records_page+1)*6]
    top=94 if len(rows)>3 else 202
    u.text('Every second has a story.',64,top,36)
    u.wrap('Your fastest completed runs, separated by stage and rules. Pauses are excluded.',64,top+54,1060,18,t['foreground'])
    y=top+102
    if not rows:
        u.panel((48,y,1104,126));u.text('Your first finish belongs here.',76,y+25,27)
        u.text('Choose a stage and reach its goal to save a time and replay.',76,y+72,19,t['foreground']);y+=140
    for row in rows:
        u.panel((48,y,1104,72));u.fit(row.get('stage','Stage'),76,y+22,504,19)
        u.fit(rules.label(row.get('rules',rules.LEGACY)),608,y+15,286,16,t['foreground'])
        u.fit(row.get('category','Category unknown'),608,y+39,286,16,t['muted'])
        u.text(runs.clock_text(row['best_seconds']),922,y+22,24,t['accent']);y+=76
    u.text('Local records on this device.',64,y+10,17,t['foreground']);y+=46
    u.button('Back',(64,y,150,44),lambda:app.route('home'),primary=True)
    if not rows:u.button('Choose a stage',(232,y,220,44),lambda:app.route('stages'))
    if app.records_page>0:u.button('Previous',(788,y,156,44),lambda:setattr(app,'records_page',app.records_page-1))
    if (app.records_page+1)*6<len(entries):u.button('Next',(964,y,164,44),lambda:setattr(app,'records_page',app.records_page+1))


def card_secondary(theme):
    """Readable System metadata against its actual palette-graded card face."""
    from .art import mix
    from .themes import contrast
    card=palette_panel((362,112),theme['panel'],theme['accent'])
    samples=[card.get_at((x,y))[:3] for x in range(26,337,31) for y in (12,20,82,92)]
    # Preserve a trace of the selected hue, but never inherit unreadable muted text.
    candidate=mix(theme['muted'],theme['foreground'],.8)
    choices=(candidate,theme['foreground'],(248,248,240),(10,13,18))
    return next((c for c in choices if min(contrast(c,bg) for bg in samples)>=4.5),max(choices,key=lambda c:min(contrast(c,bg) for bg in samples)))
