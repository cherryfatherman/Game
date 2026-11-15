#!/usr/bin/env python3
"""가로 시험판(가로시험.html)에 쓸 그림을 만든다.

  python3 tools/가로자산.py

- 먼 배경: art/맵/원본/1-1-먼배경.png → art/맵/1-1-먼배경.jpg (가로 1600, 오른쪽 아래 별 표시는 덮는다)
- 발판: art/맵/원본/1구역-발판.png → 땅, 발판-중, 발판-소, 통나무 (art/맵/1구역-*.png)
- 기사 인형: 속옷 차림 그림에서 나무 검을 지우고 몸통, 왼다리, 오른다리, 손, 머리로 나눈다 (art/knight/인형/남-*.png)
"""
import os, sys
import numpy as np
from PIL import Image, ImageDraw
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import importlib


def 먼배경():
    im = Image.open(os.path.join(ROOT, 'art/맵/원본/1-1-먼배경.png')).convert('RGB')
    w, h = im.size
    patch = im.crop((w - 420, h - 230, w - 210, h)).transpose(Image.FLIP_LEFT_RIGHT)   # 별 표시 자리를 옆 땅으로 덮는다
    im.paste(patch, (w - 210, h - 230))
    im = im.resize((1600, int(h * 1600 / w)), Image.LANCZOS)
    im.save(os.path.join(ROOT, 'art/맵/1-1-먼배경.jpg'), quality=86); print('먼배경', im.size)


def 발판():
    m = importlib.import_module('무기자르기')
    for p, size in m.split(os.path.join(ROOT, 'art/맵/원본/1구역-발판.png'), os.path.join(ROOT, 'art/맵'),
                           ['1구역-땅', '1구역-발판-중', '1구역-발판-소', '1구역-통나무']):
        im = Image.open(p); im = im.resize((im.width // 2, im.height // 2), Image.LANCZOS); im.save(p); print(os.path.basename(p), im.size)


def 인형(g='남'):
    쥠 = importlib.import_module('무기쥐여보기')
    M = 쥠.모양[g]
    # 옷 겹만 따로 꺼내 나무 검을 지운다
    saved = M['겹'], M['굵기']; M['겹'] = [p for p in saved[0] if p.startswith('옷/')]; M['굵기'] = 27
    base, body, hand, _, _ = 쥠.바탕(g); M['겹'], M['굵기'] = saved
    a = np.asarray(body).copy(); yy, xx = np.mgrid[0:1024, 0:1024]
    cx = 578
    leg = (yy > 706) & (xx > 455) & (xx < 705)
    out = os.path.join(ROOT, 'art/knight/인형')
    def save(name, mask):
        b = a.copy(); b[~mask] = 0; Image.fromarray(b, 'RGBA').save(os.path.join(out, '%s-%s.png' % (g, name)))
    save('몸통', ~leg | (yy < 724))                   # 다리 위쪽을 조금 겹쳐 틈이 안 보이게
    save('왼다리', leg & (xx < cx)); save('오른다리', leg & (xx >= cx))
    h = np.asarray(base).copy(); h[~(np.asarray(hand) > 0)] = 0
    Image.fromarray(h, 'RGBA').save(os.path.join(out, '%s-손.png' % g))
    Image.open(os.path.join(ROOT, 'art/knight/머리/기본-%s.png' % g)).save(os.path.join(out, '%s-머리.png' % g))
    print('인형', g)


if __name__ == '__main__':
    먼배경(); 발판(); 인형('남')
