"""Optional visible-region accelerator; unchanged full-surface fallback in objects.

No runtime dependencies or installation: build once per process in a private temporary
folder with the existing C compiler. If unavailable, retain the portable renderer.
The sampler never rounds the requested angle or interpolation alpha.
"""
import ctypes
from functools import lru_cache
import math
from pathlib import Path
import subprocess
import tempfile
import pygame

@lru_cache(maxsize=1)
def kernel():
    if pygame.version.vernum[:2] != (2,6):return None
    try:
        with tempfile.TemporaryDirectory(prefix='wwiup-terrain-') as directory:
            output=Path(directory)/'sampler.so'
            subprocess.run(['cc','-O3','-march=native','-shared','-fPIC','-fwrapv',str(Path(__file__).with_suffix('.c')),'-o',str(output)],check=True,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,timeout=20)
            library=ctypes.CDLL(str(output))
        fn=library.sample_region
        fn.argtypes=[ctypes.c_void_p,ctypes.c_int,ctypes.c_int,ctypes.c_int,ctypes.c_void_p]+[ctypes.c_int]*9
        fn.restype=None
        return fn
    except (OSError,subprocess.SubprocessError):
        return None

def material(source,size,scale,matrix):
    c,s=matrix;angle=ctypes.c_float(-math.degrees(math.atan2(s,c))).value;zoom=ctypes.c_float(math.hypot(c,s)).value
    # Match the library's angle-zero zoom branch and unsupported formats exactly.
    if abs(angle)<=.001 or source.get_bitsize()!=32 or zoom<.001:return None
    fn=kernel()
    if fn is None:return None
    radians=angle*(math.pi/180.);sine=math.sin(radians)*zoom;cosine=math.cos(radians)*zoom
    x=source.get_width()//2;y=source.get_height()//2
    fullw=2*max(1,math.ceil(max(abs(cosine*x+sine*y),abs(cosine*x-sine*y),abs(-cosine*x+sine*y),abs(-cosine*x-sine*y))))
    fullh=2*max(1,math.ceil(max(abs(sine*x+cosine*y),abs(sine*x-cosine*y),abs(-sine*x+cosine*y),abs(-sine*x-cosine*y))))
    # Include only the destination pixels that the ordinary blit can expose.
    target=pygame.Rect(120*scale-fullw//2,120*scale-fullh//2,fullw,fullh)
    visible=target.clip(pygame.Rect((0,0),size))
    result=pygame.Surface(size)
    if not visible:return result
    image=pygame.Surface(visible.size,0,32,source.get_masks())
    inv=65536./(zoom*zoom)
    source.lock();image.lock()
    try:
        fn(source._pixels_address,source.get_width(),source.get_height(),source.get_pitch(),image._pixels_address,image.get_width(),image.get_height(),image.get_pitch(),fullw,fullh,visible.x-target.x,visible.y-target.y,int(sine*inv),int(cosine*inv))
    finally:
        image.unlock();source.unlock()
    result.blit(image,visible)
    return result
