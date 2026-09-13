import pygame
import os
from functools import lru_cache

from pygame.locals import *

from locals import *

import data

from frame import Frame

class Animation:

  cached_frames = {}

  def __init__(self, object, anim_name):
    repeat_times, durations = definition(object, anim_name)
    self.frames = [Frame(object, anim_name, i, length) for i, length in enumerate(durations)]
    self.repeat_times = repeat_times
    self.cache_name = object + ":" + anim_name + ":"
    self.reset()
    return

  def reset(self):
    self.c = 0
    self.i = 0
    self.repeated = 0
    self.finished = False
    self.image = self.frames[self.i].get_image()
    return


  def update_and_get_image(self):
    if (not self.finished):
      self.c += 1
      if (self.c > int(self.frames[self.i].get_time())):
        self.c = 0
        self.i += 1
        if (self.i == len(self.frames)):
          self.repeated += 1
          if (self.repeated == self.repeat_times):
            self.i -= 1
            self.finished = True
          else:
            self.i = 0
        if (self.cache_name + str(self.i)) in Animation.cached_frames:
          self.image = Animation.cached_frames[self.cache_name + str(self.i)]
        else:
          self.image = (self.frames[self.i]).get_image()
          Animation.cached_frames[self.cache_name + str(self.i)] = self.image
    return self.image


@lru_cache(maxsize=256)
def definition(object_name, anim_name):
  for path in (data.animpath(object_name, anim_name), data.animpath("brown", anim_name), data.animpath("default", "static")):
    try:
      with open(path) as source:
        lines = source.read().splitlines()
      break
    except FileNotFoundError:
      continue
  else:
    raise FileNotFoundError(anim_name)
  repeat = -1
  durations = []
  for line in lines:
    values = line.split()
    if values and values[0] == "repeat_times": repeat = int(values[1])
    if values and values[0] == "frame": durations.append(int(values[2]))
  if not durations: raise ValueError("Animation has no frames: " + anim_name)
  return repeat, tuple(durations)
