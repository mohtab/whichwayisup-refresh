"""Shared decoded sprite assets. Derived from the GPL-2.0 original, 2026-09-12."""
from functools import lru_cache
import pygame
import data
from log import error_message

@lru_cache(maxsize=512)
def sprite(object_name, animation, frame):
    candidates = [(object_name, animation, frame), ('brown', animation, frame), ('object', 'idle', 0)]
    for index, args in enumerate(candidates):
        try:
            image = pygame.image.load(data.picpath(*args)).convert()
            image.set_colorkey((255, 0, 255))
            if index == 2:
                error_message('Object graphic missing: ' + '_'.join(map(str, candidates[0])))
            return image
        except (FileNotFoundError, pygame.error):
            if index == 2:
                raise

class Frame:
    def __init__(self, object, anim_name, frameno, frame_length):
        self.image = sprite(object, anim_name, frameno)
        self.frame_length = frame_length
    def get_image(self):
        return self.image
    def get_time(self):
        return self.frame_length
