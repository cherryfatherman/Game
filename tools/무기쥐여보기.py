#!/usr/bin/env python3
"""잘라 둔 무기를 기사 손에 쥐여 본 그림을 만든다(시안용).

  python3 tools/무기쥐여보기.py [남|여] [나올파일.png]

- 무기 도감의 순서대로 40종을 한 장에 늘어놓는다.
- 모든 무기를 기사가 지금 든 검과 같은 길이로 맞춘다(손잡이 끝을 같은 자리에 둔다).
- 지금은 기사 그림에 예전 검이 그려져 있어서, 몸 밖으로 나온 부분만 지우고 그 위에 덮어 그린다.
  검 없는 기사 그림이 생기면 이 덮어 그리기는 필요 없어진다.
"""
import os, sys, math
import numpy as np
from PIL import Image, ImageDraw, ImageFont
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import importlib
도감 = importlib.import_module('무기도감판')
ROOT = 도감.ROOT

TIP = (212, 918); POM = (805, 645)          # 기사 그림(1024) 안에서 예전 검의 칼끝과 손잡이 끝
ANG = math.degrees(math.atan2(TIP[1] - POM[1], POM[0] - TIP[0]))
LEN = math.hypot(POM[0] - TIP[0], TIP[1] - POM[1])
HAND = [(690, 615), (745, 613), (752, 663), (738, 698), (722, 723), (690, 721), (672, 698), (670, 668), (688, 653)]


def 바탕(g):
    base = Image.open(os.path.join(ROOT, 'art/knight/기본-%s.png' % g)).convert('RGBA')
    a = np.asarray(base).copy()
    ux, uy = (TIP[0] - POM[0]) / LEN, (TIP[1] - POM[1]) / LEN
    yy, xx = np.mgrid[0:1024, 0:1024]
    t = (xx - POM[0]) * ux + (yy - POM[1]) * uy
    dist = np.abs((xx - POM[0]) * uy - (yy - POM[1]) * ux)
    a[(dist < 16) & (t > 0) & (xx < 452)] = 0          # 몸 밖으로 나온 예전 칼날
    a[(dist < 26) & (t < 30) & (xx > 752) & (yy < 690)] = 0   # 손 뒤로 나온 예전 손잡이 끝
    hand = Image.new('L', (1024, 1024), 0); ImageDraw.Draw(hand).polygon(HAND, fill=255)
    return base, Image.fromarray(a), hand


def 쥐기(base, body, hand, name, k=1.0):
    s = Image.open(os.path.join(ROOT, 'art/무기', name.replace(' ', '') + '.png'))
    L = int((LEN + 18) * k); s = s.resize((L, max(1, int(s.height * L / s.width))), Image.LANCZOS)
    C = 1700; cv = Image.new('RGBA', (C, C), (0, 0, 0, 0)); cv.alpha_composite(s, (C // 2 - L, C // 2 - s.height // 2))
    cv = cv.rotate(ANG, resample=Image.BICUBIC)
    out = body.copy(); lay = Image.new('RGBA', (1024, 1024), (0, 0, 0, 0))
    lay.paste(cv, (POM[0] + 12 - C // 2, POM[1] - 6 - C // 2)); out.alpha_composite(lay)
    out.paste(base, (0, 0), Image.composite(base.getchannel('A'), Image.new('L', (1024, 1024), 0), hand))
    return out


def main(g, path):
    rows = 도감.목록(); base, body, hand = 바탕(g)
    box = (140, 30, 940, 950); cw, ch = (box[2] - box[0]) // 3, (box[3] - box[1]) // 3
    f = ImageFont.truetype(도감.FONT, 19)
    sh = Image.new('RGBA', (8 * cw, 5 * (ch + 30)), (30, 42, 30, 255)); d = ImageDraw.Draw(sh)
    for i, (n, grade, name) in enumerate(rows):
        c = 쥐기(base, body, hand, name).crop(box).resize((cw, ch), Image.LANCZOS)
        x, y = (i % 8) * cw, (i // 8) * (ch + 30)
        sh.alpha_composite(c, (x, y))
        d.text((x + cw // 2, y + ch + 13), '%d %s' % (n, name), font=f, fill=도감.COL[grade], anchor='mm')
    sh.convert('RGB').save(path); print(path, sh.size)


if __name__ == '__main__':
    g = sys.argv[1] if len(sys.argv) > 1 else '남'
    main(g, sys.argv[2] if len(sys.argv) > 2 else os.path.join(ROOT, 'art/무기/손에든모습-%s.png' % g))
