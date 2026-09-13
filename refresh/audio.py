"""Original synthesized ambient loop; separate from the preserved sound effects."""
from array import array
import math
import pygame

class Audio:
    def __init__(self, available):
        self.available=available
        self.loop=None
        self.channel=None
        if available:pygame.mixer.set_reserved(1)

    def apply(self, settings):
        if not self.available:return
        volume=settings['music_volume']/100 if settings['music'] else 0
        if not volume:
            if self.channel:self.channel.stop()
            return
        if self.loop is None:self.loop=self.make_loop()
        if self.channel is None:self.channel=pygame.mixer.Channel(0)
        self.channel.set_volume(volume*.38)
        if not self.channel.get_busy():self.channel.play(self.loop,loops=-1)

    @staticmethod
    def make_loop():
        rate,fmt,channels=pygame.mixer.get_init()
        if fmt!=-16:raise pygame.error('Ambient loop requires signed 16-bit audio')
        # Four gentle two-second arpeggios; envelopes reach zero at loop boundaries.
        notes=(220.,329.63,440.,329.63,196.,293.66,392.,293.66,
               174.61,261.63,349.23,261.63,196.,293.66,392.,293.66)
        samples=array('h')
        for n,freq in enumerate(notes):
            for i in range(rate//2):
                t=i/rate;envelope=math.sin(math.pi*t/.5)**2
                wave=math.sin(2*math.pi*freq*t)+.22*math.sin(2*math.pi*freq*2*t)
                value=round(5600*envelope*wave)
                samples.extend([value]*channels)
        return pygame.mixer.Sound(buffer=samples)
