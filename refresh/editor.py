"""Local stage authoring with undo, metadata and built-in event editing."""
from copy import deepcopy
from pathlib import Path
import time
import pygame
from . import stages
from .storage import user_path, atomic_json

class Editor:
    GRID=pygame.Rect(36,154,560,560)
    TOOLS=('W','S','B','erase','player','key','lever','spider','blob','power_crystal','cake')
    def __init__(self,document=None):
        self.document=deepcopy(document or stages.blank())
        self.document['id']='stage-'+str(time.time_ns())
        if document:
            self.document['title']='Remix: '+self.document['title']
            # Attribution remains on remixes; author field can add adaptation credit.
        self.tool='W';self.attached='RIGHT';self.undo=[];self.redo=[]
        self.path=None;self.dirty=False;self.drawing=False;self.cursor=[9,18]
    def key(self,event,app):
        if event.mod & pygame.KMOD_CTRL:
            actions={pygame.K_z:self.go_undo,pygame.K_y:self.go_redo,pygame.K_r:self.rotate}
            if event.key in actions:actions[event.key]();return True
            return False
        moves={pygame.K_LEFT:(-1,0),pygame.K_RIGHT:(1,0),pygame.K_UP:(0,-1),pygame.K_DOWN:(0,1)}
        if event.key in moves:
            dx,dy=moves[event.key];self.cursor=[max(0,min(19,self.cursor[0]+dx)),max(0,min(19,self.cursor[1]+dy))]
            return True
        if event.key in (pygame.K_SPACE,pygame.K_DELETE,pygame.K_BACKSPACE):
            self.paint((self.GRID.x+self.cursor[0]*28+14,self.GRID.y+self.cursor[1]*28+14),event.key!=pygame.K_SPACE)
            return True
        if event.key in (pygame.K_LEFTBRACKET,pygame.K_RIGHTBRACKET):
            index=self.TOOLS.index(self.tool);self.tool=self.TOOLS[(index+(-1 if event.key==pygame.K_LEFTBRACKET else 1))%len(self.TOOLS)]
            return True
        if event.key==pygame.K_F5:app.editor_test();return True
        return False
    def checkpoint(self):
        self.undo.append(deepcopy(self.document));self.undo=self.undo[-60:];self.redo=[];self.dirty=True
    def go_undo(self):
        if self.undo:self.redo.append(self.document);self.document=self.undo.pop();self.dirty=True
    def go_redo(self):
        if self.redo:self.undo.append(self.document);self.document=self.redo.pop();self.dirty=True
    def paint(self,pos,erase=False):
        if not self.GRID.collidepoint(pos):return False
        x=int((pos[0]-self.GRID.x)//28);y=int((pos[1]-self.GRID.y)//28)
        tool='erase' if erase else self.tool
        if tool in ('W','S','B','erase'):
            row=self.document['tiles'][y]
            val=' ' if tool=='erase' else tool
            if row[x]==val and not (tool=='erase' and any(int(e['x'])==x and int(e['y'])==y for e in self.document['entities'])):return True
            self.checkpoint()
            self.document['tiles'][y]=row[:x]+val+row[x+1:]
            if tool=='erase':self.document['entities']=[e for e in self.document['entities'] if not(int(e['x'])==x and int(e['y'])==y)]
        else:
            self.checkpoint()
            if tool=='player':self.document['entities']=[e for e in self.document['entities'] if e['type']!='player']
            e=dict(type=tool,x=x+.5,y=y+.5)
            if tool=='spider':e['attached']=self.attached
            if tool=='lever':e['uses']=-1
            self.document['entities'].append(e)
        return True
    def save(self,draft=False):
        if not draft:stages.validate(self.document)
        folder=user_path('data')/('drafts' if draft else 'stages');folder.mkdir(exist_ok=True)
        path=folder/(self.document['id']+'.json')
        atomic_json(path,self.document)
        if not draft:self.path=path;self.dirty=False
        return path
    def export(self):
        stages.validate(self.document)
        folder=user_path('data')/'exports';folder.mkdir(exist_ok=True)
        path=folder/(self.document['id']+'.json')
        atomic_json(path,self.document)
        return path
    def rotate(self):
        self.checkpoint()
        rows=self.document['tiles']
        self.document['tiles']=[''.join(rows[19-x][y] for x in range(20)) for y in range(20)]
        directions={'RIGHT':'DOWN','DOWN':'LEFT','LEFT':'UP','UP':'RIGHT'}
        for e in self.document['entities']:
            e['x'],e['y']=20-e['y'],e['x']
            if 'attached' in e:e['attached']=directions[e['attached']]
    def draw(self,app):
        ui=app.ui;t=app.theme;d=self.document
        ui.header('STAGE STUDIO / LOCAL CREATION')
        ui.fit(d['title'],36,99,560,28)
        ui.text('20 × 20 board  /  outlined area is the initial view',36,132,13,t['muted'])
        pygame.draw.rect(ui.surface,t['panel'],self.GRID)
        for y,row in enumerate(d['tiles']):
            for x,c in enumerate(row):
                cell=pygame.Rect(36+x*28,154+y*28,28,28)
                pygame.draw.rect(ui.surface,t['background'],cell,1)
                if c in 'WSB':
                    kind={'W':'wall','S':'spikes','B':'bars'}[c]
                    sprite=app.painter.sprite(kind,28,28)
                    ui.surface.blit(sprite,cell)
        for e in d['entities']:
            pos=(36+e['x']*28,154+e['y']*28)
            sprite=app.painter.sprite(e['type'],24,26,character='guy')
            ui.surface.blit(sprite,sprite.get_rect(center=pos))
        pygame.draw.rect(ui.surface,t['accent'],(36+7*28,154+7*28,13*28,13*28),2)
        cursor=pygame.Rect(self.GRID.x+self.cursor[0]*28,self.GRID.y+self.cursor[1]*28,28,28)
        pygame.draw.rect(ui.surface,t['foreground'],cursor,2)
        ui.panel((620,96,544,643))
        ui.text('BUILD YOUR PERSPECTIVE',646,118,16,t['accent'])
        labels={'W':'Wall','S':'Spikes','B':'Bars','erase':'Erase','player':'Spawn','key':'Key','lever':'Lever','spider':'Spider','blob':'Blob','power_crystal':'Crystal','cake':'Cake'}
        for i,tool in enumerate(self.TOOLS):
            ui.button(labels[tool],(646+(i%4)*120,155+(i//4)*43,110,35),lambda v=tool:setattr(self,'tool',v),selected=self.tool==tool)
        ui.button('Spider: '+self.attached,(646,292,230,35),self.cycle_direction)
        ui.button('Rotate board 90°',(890,292,244,35),self.rotate)
        ui.button('Undo',(646,338,110,35),self.go_undo)
        ui.button('Redo',(768,338,110,35),self.go_redo)
        ui.button('Title',(890,338,110,35),lambda:app.prompt('Stage title',d['title'],lambda v:self.set_field('title',v)))
        ui.button('Author',(1012,338,122,35),lambda:app.prompt('Author / adaptation credit',d['author'],lambda v:self.set_field('author',v)))
        ui.text('Built-in event',646,393,16)
        ui.button('On: '+d['events'][0]['trigger'] if d['events'] else 'Add goal event',(646,422,230,36),self.cycle_trigger)
        ui.button('Edit goal message',(890,422,244,36),lambda:app.prompt('Dialogue before stage completion',self.message(),self.set_message))
        ui.wrap('Collect the goal item to complete the stage. Add levers to rotate the world. Right-click erases.',646,477,470,16,t['muted'])
        ui.fit('Credit: '+d['author'],646,558,484,13,t['muted'])
        ui.fit('License: '+d['license'],646,580,484,13,t['muted'])
        ui.button('Save stage',(646,617,150,40),lambda:app.editor_save())
        ui.button('Playtest',(810,617,150,40),lambda:app.editor_test(),primary=True)
        ui.button('Export JSON',(974,617,160,40),lambda:app.editor_export())
        ui.button('Back',(646,680,150,36),lambda:app.leave_editor())
        ui.text('Arrows: cursor  Space: paint  [ / ]: tool  F5: test  Ctrl+S: save',36,730,14,t['muted'])
    def set_field(self,key,value):
        stages.text(value,key);self.checkpoint();self.document[key]=value
    def cycle_direction(self):
        choices=('RIGHT','DOWN','LEFT','UP');self.attached=choices[(choices.index(self.attached)+1)%4]
    def cycle_trigger(self):
        self.checkpoint()
        choices=('key','power_crystal','cake','other_pants')
        if not self.document['events']:self.document['events']=[dict(trigger='key',times=1,actions=['change_level'])]
        e=self.document['events'][0];e['trigger']=choices[(choices.index(e['trigger'])+1)%4] if e['trigger'] in choices else 'key'
    def message(self):
        return next((a[9:] for e in self.document['events'] for a in e['actions'] if a.startswith('dialogue ')),'Stage complete!')
    def set_message(self,value):
        stages.text(value,'dialogue',480);self.checkpoint()
        if not self.document['events']:self.document['events']=[dict(trigger='key',times=1,actions=[])]
        self.document['events'][0]['actions']=['dialogue '+value,'change_level']
