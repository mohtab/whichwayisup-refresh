"""Refresh alpha sheet extraction must preserve source bytes and game canvases."""
import os
import unittest
os.environ.update(SDL_VIDEODRIVER='dummy',SDL_AUDIODRIVER='dummy')
import pygame
from refresh import objects

class RefreshObjectTests(unittest.TestCase):
    def setUp(self):
        pygame.display.init();pygame.display.set_mode((64,64))
    def test_all_cells_are_nonempty_and_runtime_does_not_mutate_sources(self):
        for kind in ('other_pants','power_crystal','cake','blob'):
            source=objects.frame(kind);before=pygame.image.tobytes(source,'RGBA')
            self.assertGreater(pygame.mask.from_surface(source).count(),100)
            for phase in (0,4,8,12):
                for state in ('default','walking','dying'):
                    image=objects.sprite(kind,28,32,state,phase,2)
                    self.assertEqual(image.get_size(),(56,64))
                    bounds=image.get_bounding_rect(min_alpha=64)
                    self.assertGreater(bounds.width,5);self.assertGreater(bounds.height,5)
                    self.assertLessEqual(bounds.bottom,64)
                    self.assertGreaterEqual(bounds.bottom,62)
                    self.assertLessEqual(abs(bounds.centerx-28),1)
            self.assertEqual(pygame.image.tobytes(source,'RGBA'),before)

    def test_terrain_cells_preserve_source_and_solid_core(self):
        from refresh import lighting
        for index in range(6):
            source=objects.wall_frame(index);before=pygame.image.tobytes(source,'RGBA')
            tile=objects.wall(40,40,index,2)
            self.assertEqual(tile.get_size(),(80,80))
            self.assertGreater(pygame.mask.from_surface(tile).count(),80*80*.85)
            for neighbors in ((False,False,False,False),(True,True,True,True)):
                connected=lighting.connected_wall(tile,neighbors,index,2)
                self.assertEqual(connected.get_size(),(80,80))
                self.assertGreater(connected.get_at((40,40)).a,200)
            self.assertEqual(pygame.image.tobytes(source,'RGBA'),before)

    def test_union_has_no_internal_seam_and_tracks_render_rectangles(self):
        joined,_=objects.terrain_layer(((20,20,40,40),(60,20,40,40)),(160,120),1)
        single,_=objects.terrain_layer(((20,20,80,40),),(160,120),1)
        self.assertEqual(pygame.image.tobytes(joined,'RGBA'),pygame.image.tobytes(single,'RGBA'))
        moved,_=objects.terrain_layer(((30,25,80,40),),(160,120),1)
        self.assertEqual(moved.get_at((25,35)).a,0)
        self.assertGreater(moved.get_at((35,35)).a,200)

    def test_lever_reveal_changes_only_actual_overlap_and_keeps_sources(self):
        lever=pygame.Surface((20,30),pygame.SRCALPHA);pygame.draw.rect(lever,(190,130,70,255),(8,0,4,30))
        spider=pygame.Surface((20,20),pygame.SRCALPHA);pygame.draw.circle(spider,(150,50,90,255),(10,10),8)
        old=[pygame.image.tobytes(s,'RGBA') for s in (lever,spider)]
        world=pygame.Surface((80,80));world.fill((10,20,30));before=pygame.image.tobytes(world,'RGB')
        self.assertFalse(objects.reveal_lever(world,lever,pygame.Rect(0,0,20,30),spider,pygame.Rect(40,40,20,20),1))
        self.assertEqual(pygame.image.tobytes(world,'RGB'),before)
        self.assertTrue(objects.reveal_lever(world,lever,pygame.Rect(10,10,20,30),spider,pygame.Rect(10,15,20,20),1))
        self.assertNotEqual(pygame.image.tobytes(world,'RGB'),before)
        self.assertEqual([pygame.image.tobytes(s,'RGBA') for s in (lever,spider)],old)

    def test_real_flip_uses_interpolated_union_without_scene_mutation(self):
        import argparse,json,tempfile
        from pathlib import Path
        from unittest.mock import patch
        from refresh.app import App
        root=Path(__file__).resolve().parents[1]
        replay=json.loads((root/'docs/campaign-acceptance/replays/w0-l0.json').read_text())
        with tempfile.TemporaryDirectory() as profile,patch.dict(os.environ,WWISUP_USER_DIR=profile):
            app=App(argparse.Namespace(theme='refresh',safe_window=True,play=False,stage=None,screen=None,smoke=None,screenshot=None))
            app.s['dialogue']=False;app.start_stage(app.catalog.stages[0]);seen=False;checked=0
            for commands in replay['inputs']:
                app.session.step(commands)
                tiles=app.session.scene['level'].tiles
                flipping=any(getattr(t,'flipping',False) for t in tiles)
                if flipping or seen:
                    before=[(t.x,t.y,tuple(t.rect)) for t in tiles]
                    app.painter.draw(app.session,app.theme,app.s,.5)
                    expected=[]
                    for t in tiles:
                        if t.tileclass!='wall':continue
                        x,y=app.session.position(t,.5)
                        expected.append((round((x-t.rect.width/2)*2),round((y-t.rect.height/2)*2),t.rect.width*2,t.rect.height*2))
                    self.assertEqual(app.painter.terrain_key,tuple(expected))
                    self.assertEqual(before,[(t.x,t.y,tuple(t.rect)) for t in tiles]);checked+=1
                    if seen and not flipping:break
                    seen=True
            self.assertTrue(seen);self.assertGreater(checked,1)
