import pygame

from pygame.locals import *

from locals import *

from util import render_text
from variables import Variables

from level import Change

class Edit_utils:

  def __init__(self):
    self.cursor = [0, 0]
    return

  def update(self, inputs):
    if "REMOVE_TILE" in inputs:
      return Change("remove", self.cursor)
    if "ADD_TILE_WALL" in inputs:
      return Change("W", self.cursor)
    if "ADD_TILE_SPIKES" in inputs:
      return Change("S", self.cursor)
    if "ADD_TILE_BARS" in inputs:
      return Change("B", self.cursor)
    if "SAVE_TILES" in inputs:
      return Change("save", (0, 0))
    if "EDIT_RIGHT" in inputs and self.cursor[0] < (TILES_HOR - 1):
      self.cursor[0] += 1
    if "EDIT_LEFT" in inputs and self.cursor[0] > 0:
      self.cursor[0] -= 1
    if "EDIT_DOWN" in inputs and self.cursor[1] < (TILES_VER - 1):
      self.cursor[1] += 1
    if "EDIT_UP" in inputs and self.cursor[1] > 0:
      self.cursor[1] -= 1
    return None

  def render(self, screen):
    pygame.draw.rect(screen, COLOR_GUI_EDIT_HILIGHT, pygame.Rect(self.cursor[0]*TILE_DIM, self.cursor[1]*TILE_DIM, TILE_DIM, TILE_DIM), 2)
    return
