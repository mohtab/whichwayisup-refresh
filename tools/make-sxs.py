#!/usr/bin/env python3
"""Review-only, equal-size reference/game pairs, labels and identical blur."""
from pathlib import Path
import argparse
from PIL import Image,ImageDraw,ImageFilter
p=argparse.ArgumentParser();p.add_argument('--input',default='artifacts/baseline/matched-stills');p.add_argument('--output',default='artifacts/baseline/sxs-vs-refs');a=p.parse_args()
base=Path(__file__).resolve().parents[2];out=base/a.output;out.mkdir(parents=True,exist_ok=True)
for n in range(1,5):
 ref=Image.open(next((base/'refs-locked').glob(f'ref-{n:02d}-*'))).convert('RGB')
 game=Image.open(base/a.input/f'still-{n:02d}.png').convert('RGB')
 assert ref.size==game.size==(1920,1080)
 pair=Image.new('RGB',(3840,1120),'#101820');pair.paste(ref,(0,40));pair.paste(game,(1920,40))
 d=ImageDraw.Draw(pair);d.text((20,12),f'REF R{n:02d} (review only)',fill='white');d.text((1940,12),f'GAME still-{n:02d}',fill='white');pair.save(out/f'sxs-{n:02d}.png')
 blur=Image.new('RGB',(3840,1120),'#101820');blur.paste(ref.filter(ImageFilter.GaussianBlur(14)),(0,40));blur.paste(game.filter(ImageFilter.GaussianBlur(14)),(1920,40));d=ImageDraw.Draw(blur);d.text((20,12),f'REF R{n:02d} (review only)',fill='white');d.text((1940,12),f'GAME still-{n:02d}',fill='white');blur.resize((1920,560),Image.Resampling.LANCZOS).save(out/f'sxs-{n:02d}-blur.png')
print(out)
