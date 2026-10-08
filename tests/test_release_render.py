"""Release presentation must preserve pixels, gameplay geometry and source art."""
import argparse
import os
import tempfile
import unittest
from unittest.mock import patch

os.environ.update(SDL_VIDEODRIVER='dummy',SDL_AUDIODRIVER='dummy')
import pygame
from refresh import lighting, sprites, chamber
from refresh.app import App
from refresh.display import Display


class ReleaseRenderTests(unittest.TestCase):
    def setUp(self):
        pygame.display.init()
        pygame.display.set_mode((13,11))
        self.display=Display.__new__(Display)
        self.display.settings={'smooth':False}

    def pixels(self,image):return pygame.image.tobytes(image,'RGBA')

    def test_crisp_final_pass_preserves_palette_and_smooth_is_optional(self):
        source=pygame.Surface((2,2))
        source.fill((0,0,0));source.set_at((1,0),(255,255,255))
        self.display.present(source)
        viewport=self.display.screen.subsurface(self.display.viewport)
        colors={tuple(viewport.get_at((x,y))[:3]) for x in range(11) for y in range(11)}
        self.assertEqual(colors,{(0,0,0),(255,255,255)})
        self.display.present(source,smooth=True)
        viewport=self.display.screen.subsurface(self.display.viewport)
        self.assertTrue(any(0<viewport.get_at((x,y)).r<255 for x in range(11) for y in range(11)))

    def test_integer_scaling_uses_native_resolution_and_keeps_pointer_mapping(self):
        source=pygame.Surface((8,8));source.fill('white')
        self.display.present(source,integer_scale=True,pixel_scale=2)
        self.assertEqual(self.display.viewport.size,(8,8))
        self.assertEqual(self.display.map(self.display.viewport.topleft),(0,0))
        self.assertEqual(self.display.map(self.display.viewport.bottomright),(8,8))
        self.assertEqual(self.display.screen.get_at((0,0))[:3],(5,8,12))
        pygame.display.set_mode((3,3))
        self.display.present(source,integer_scale=True,pixel_scale=2)
        self.assertEqual(self.display.viewport.size,(3,3))

    def test_crisp_board_layer_keeps_ui_smooth_at_fractional_window_sizes(self):
        ui=pygame.Surface((2,2));ui.fill('black');ui.set_at((1,0),'white')
        board=ui.copy()
        self.display.present(ui,smooth=True,layers=[(board,(0,0,1,1),False,False,1)])
        screen=self.display.screen
        self.assertTrue(all(screen.get_at((x+1,y)).r in (0,255) for x in range(6) for y in range(6)))
        self.assertTrue(any(0<screen.get_at((x+1,y)).r<255 for x in range(7,11) for y in range(11)))
        ui=pygame.Surface((10,10));ui.fill('black')
        board=pygame.Surface((8,8));board.fill('white')
        self.display.present(ui,smooth=True,layers=[(board,(0,0,10,10),False,True,2)])
        white=pygame.mask.from_threshold(self.display.screen,(255,255,255,255),(1,1,1,255))
        bounds=white.get_bounding_rects()
        self.assertEqual(len(bounds),1)
        self.assertEqual(bounds[0].size,(8,8))
        self.assertEqual(bounds[0].center,self.display.viewport.center)

    def test_wayland_canvas_copy_does_not_hide_finished_sprite_pixels(self):
        # Wayland can expose an alpha mask even for opaque display-format canvases.
        # Copying such a canvas enables SRCALPHA and exposes unused alpha bytes.
        canvas=pygame.Surface((4,4),0,32,(0xff0000,0xff00,0xff,0xff000000))
        canvas.set_alpha(None)
        canvas.fill((30,45,60,255))
        canvas.fill((210,130,40,0),(1,1,2,2))
        copied=canvas.copy()
        self.assertTrue(copied.get_flags() & pygame.SRCALPHA)
        before=self.pixels(copied)
        for smooth in (False,True):
            with self.subTest(smooth=smooth,view='board'):
                self.display.present(copied,smooth=smooth)
                self.assertEqual(self.display.screen.get_at(self.display.viewport.center)[:3],(210,130,40))
            with self.subTest(smooth=smooth,view='full'):
                ui=pygame.Surface((4,4));ui.fill('black')
                self.display.present(ui,layers=[(copied,(0,0,4,4),smooth,False,1)])
                self.assertEqual(self.display.screen.get_at(self.display.viewport.center)[:3],(210,130,40))
        self.assertEqual(self.pixels(copied),before)
        self.assertTrue(copied.get_flags() & pygame.SRCALPHA)

    def test_wall_quieting_keeps_solid_edges_and_actor_outline_keeps_canvas(self):
        wall=sprites.prop('wall',40,40,'default',0,2)
        before=self.pixels(wall)
        quiet=lighting.quiet_wall(wall,(20,30,40),2)
        self.assertEqual(self.pixels(wall),before)
        self.assertNotEqual(self.pixels(quiet),before)
        self.assertEqual(quiet.get_bounding_rect(),wall.get_bounding_rect())
        for edge in ((0,0,80,2),(0,78,80,2),(0,0,2,80),(78,0,2,80)):
            self.assertEqual(self.pixels(quiet.subsurface(edge)),self.pixels(wall.subsurface(edge)))
        actor=sprites.player(28,33,'walking',0,2)
        before=self.pixels(actor)
        outlined=lighting.silhouette(actor,(8,12,15),2)
        bright=lighting.silhouette(actor,(245,245,230),2,True)
        self.assertNotEqual(self.pixels(outlined),self.pixels(bright))
        self.assertEqual(actor.get_size(),outlined.get_size())
        self.assertEqual(self.pixels(actor),before)
        self.assertGreater(pygame.mask.from_surface(outlined,80).count(),pygame.mask.from_surface(actor,80).count())

    def test_modern_readability_passes_leave_game_geometry_and_original_untouched(self):
        with tempfile.TemporaryDirectory(prefix='wwisup-release-render-') as folder, patch.dict(os.environ,WWISUP_USER_DIR=folder):
            app=App(argparse.Namespace(theme='refresh',safe_window=True,play=False,stage=None,screen=None,smoke=None,screenshot=None))
            app.s['dialogue']=False;app.start_stage(app.catalog.stages[0])
            objects=(*app.session.scene['level'].tiles,*app.session.scene['objects'])
            before=[(o.x,o.y,tuple(o.rect),o.current_animation,self.pixels(o.image)) for o in objects]
            for name in ('refresh','cyberpunk','omarchy','original'):
                settings=dict(app.s,theme=name)
                theme=app.themes.get(settings)
                with patch.object(lighting,'silhouette',wraps=lighting.silhouette) as outline,patch.object(lighting,'quiet_wall',wraps=lighting.quiet_wall) as quiet,patch.object(lighting,'refresh_relief',wraps=lighting.refresh_relief) as relief:
                    app.painter.draw(app.session,theme,settings,1)
                    if name=='original':outline.assert_not_called();quiet.assert_not_called();relief.assert_not_called()
                    elif name=='refresh':self.assertTrue(outline.called);self.assertTrue(relief.called);quiet.assert_not_called()
                    else:self.assertTrue(outline.called);self.assertTrue(quiet.called);relief.assert_not_called()
            self.assertEqual(before,[(o.x,o.y,tuple(o.rect),o.current_animation,self.pixels(o.image)) for o in objects])
            self.assertEqual(app.session.tick,0)

    def test_refresh_relief_preserves_source_and_keeps_foreground_above_recess(self):
        wall=sprites.prop('wall',40,40,'default',0,2)
        actor=sprites.player(28,33,'walking',0,2)
        for source,is_wall in ((wall,True),(actor,False)):
            before=self.pixels(source)
            shaded=lighting.refresh_relief(source,0,is_wall,2)
            lit=lighting.refresh_relief(source,3,is_wall,2)
            self.assertEqual(self.pixels(source),before)
            self.assertEqual(source.get_size(),shaded.get_size())
            self.assertEqual(pygame.mask.from_surface(source).count(),pygame.mask.from_surface(shaded).count())
            self.assertEqual(pygame.mask.from_surface(source).count(),pygame.mask.from_surface(lit).count())
            self.assertNotEqual(self.pixels(shaded),self.pixels(lit))
        # A mechanical pixel guard, not a substitute for the visual reference gate.
        foreground=pygame.transform.average_color(lighting.refresh_relief(wall,0,True,2))
        recess=pygame.transform.average_color(chamber.background())
        luma=lambda c:.2126*c[0]+.7152*c[1]+.0722*c[2]
        self.assertGreater(luma(foreground),luma(recess)+15)

    def test_room_light_varies_with_position_and_preserves_alpha(self):
        source=pygame.Surface((40,40),pygame.SRCALPHA);source.fill((130,130,130,0))
        pygame.draw.circle(source,(130,130,130,255),(20,20),16)
        before=self.pixels(source);field=lighting.room_field([], (1040,1040))
        near=lighting.spatial_response(source,pygame.Rect(50,50,40,40),field)
        far=lighting.spatial_response(source,pygame.Rect(900,900,40,40),field)
        self.assertGreater(sum(near.get_at((20,20))[:3]),sum(far.get_at((20,20))[:3]))
        warm=lighting.room_field([(460,460)],(1040,1040))
        pool=lighting.spatial_response(source,pygame.Rect(900,900,40,40),warm)
        self.assertGreater(pool.get_at((20,20)).r,far.get_at((20,20)).r)
        self.assertEqual(self.pixels(source),before)
        for image in (near,far,pool):
            self.assertEqual(pygame.mask.from_surface(image).count(),pygame.mask.from_surface(source).count())
        # Static directional hierarchy exists independently of optional effects.
        self.assertNotEqual(field.get_at((80,80)),field.get_at((960,960)))


if __name__=='__main__':unittest.main()
