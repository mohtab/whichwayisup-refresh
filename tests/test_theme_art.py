"""Theme-specific artwork must remain distinct, animated and non-mutating."""
import os,unittest
os.environ.update(SDL_VIDEODRIVER='dummy',SDL_AUDIODRIVER='dummy')
import pygame
from refresh import sprites,branding
from refresh.art import Painter
from refresh.themes import Themes
from refresh.storage import DEFAULTS
class ThemeArtTests(unittest.TestCase):
    def setUp(self):
        pygame.display.init();pygame.display.set_mode((520,520));self.painter=Painter();self.themes=Themes()
    def draw(self,theme,kind,phase=0):
        settings=dict(DEFAULTS,theme=theme);self.painter.configure(self.themes.get(settings),settings)
        return self.painter.sprite(kind,40,40,'default',phase,'guy',2)
    def test_every_cyberpunk_asset_has_its_own_art(self):
        for kind in ('player','spider','wall','spikes','lever','projectile','key','bars','blob','other_pants','cake'):
            with self.subTest(kind=kind):
                cyber=self.draw('cyberpunk',kind);refresh=self.draw('refresh',kind)
                self.assertNotEqual(pygame.image.tobytes(cyber,'RGBA'),pygame.image.tobytes(refresh,'RGBA'))
                self.assertGreater(cyber.get_bounding_rect().width,0)
    def test_reviewed_frames_keep_full_strides_and_tile_edges(self):
        for name in sprites.REGIONS:
            for index in range(24):
                frame,_=sprites.source_frame(name,6,4,index)
                self.assertGreater(frame.get_bounding_rect().width,50)
        full,_=sprites.source_frame('cyber-courier-v1.png',6,4,0)
        self.assertGreater(full.get_width(),256)
        tile=self.draw('cyberpunk','wall');self.assertEqual(tile.get_bounding_rect().size,tile.get_size())
    def test_cyber_spider_feet_stay_on_each_support(self):
        for phase in range(16):
            for side in range(4):
                art=sprites.orient_spider(sprites.spider(40,40,'walking',phase,2,'cyberpunk'),side)
                r=art.get_bounding_rect(min_alpha=96)
                self.assertTrue({0:r.right>=79,1:r.bottom>=79,2:r.left<=1,3:r.top<=1}[side])
    def test_logo_pulses_but_reduced_effects_stay_steady(self):
        bright=branding.collectible(40,40,8,2);dim=branding.collectible(40,40,24,2)
        self.assertNotEqual(pygame.image.tobytes(bright,'RGBA'),pygame.image.tobytes(dim,'RGBA'))
        self.assertGreater(bright.get_bounding_rect(min_alpha=100).width,dim.get_bounding_rect(min_alpha=100).width)
        a=branding.collectible(40,40,8,2,False);b=branding.collectible(40,40,24,2,False)
        self.assertEqual(pygame.image.tobytes(a,'RGBA'),pygame.image.tobytes(b,'RGBA'))
        self.assertNotEqual(pygame.image.tobytes(self.draw('omarchy','key'),'RGBA'),pygame.image.tobytes(self.draw('refresh','key'),'RGBA'))
if __name__=='__main__':unittest.main()
