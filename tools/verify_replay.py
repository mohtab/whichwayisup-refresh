#!/usr/bin/env python3
"""Inspect a local replay using isolated saves and the actual game simulation.

Usage: python tools/verify_replay.py stage.json replay.json
This is a local tool, not a hardened public submission worker.
"""
import argparse
import json
import os
from pathlib import Path
import sys
import tempfile
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('stage',type=Path)
    parser.add_argument('replay',type=Path)
    args=parser.parse_args()
    if args.replay.stat().st_size>8*1024*1024:parser.error('Replay exceeds 8 MiB')
    os.environ.update(SDL_VIDEODRIVER='dummy',SDL_AUDIODRIVER='dummy')
    with tempfile.TemporaryDirectory(prefix='wwisup-verify-') as scratch:
        os.environ['WWISUP_USER_DIR']=scratch
        import pygame
        from refresh import stages,runs
        from refresh.storage import DEFAULTS
        pygame.display.init();pygame.font.init();pygame.display.set_mode((520,520))
        try:
            result=runs.verify(json.loads(args.replay.read_text()),stages.read(args.stage),DEFAULTS)
            print(json.dumps(result,indent=2))
        except (ValueError,OSError) as error:
            parser.exit(1,str(error)+'\n')
        finally:pygame.quit()

if __name__=='__main__':main()
