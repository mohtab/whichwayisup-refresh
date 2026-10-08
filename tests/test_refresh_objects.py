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
