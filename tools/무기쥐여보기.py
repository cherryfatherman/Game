#!/usr/bin/env python3
"""잘라 둔 무기를 기사 손에 쥐여 본 그림을 만든다(시안용).

  python3 tools/무기쥐여보기.py [남|여] [나올파일.png]

- 무기에 눈이 가도록 기사는 기본 머리에 속옷 차림, 배경은 흰색이다.
- 무기 도감의 순서대로 40종을 한 장에 늘어놓는다.
- 모든 무기를 기사가 원래 든 검과 같은 길이로 맞춘다(손잡이 끝을 같은 자리에 둔다).
- 기사 그림에 그려져 있는 나무 검은 코드로 지운다. 몸과 겹친 곳은 위아래 색으로 메운 것이라 가까이 보면 어색하다.
  검 없는 기사 그림이 생기면 이 지우기는 필요 없어진다.
"""
import os, sys, math
import numpy as np
from PIL import Image, ImageDraw, ImageFont
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import importlib
도감 = importlib.import_module('무기도감판')
ROOT = 도감.ROOT

# 속옷 차림 그림(1024) 안에서: 나무 검의 칼끝, 손잡이 끝, 손(검 앞에 다시 그릴 곳), 따로 지울 곳
모양 = {
    '남': dict(겹=['옷/속옷-남', '머리/기본-남'], tip=(264, 879), pom=(805, 647), 굵기=19,
              손=[(672, 672), (690, 660), (735, 657), (741, 690), (733, 712), (712, 723), (690, 725), (676, 706)], 지움=[], 원=[]),
    '여': dict(겹=['머리/기본-여-뒤', '옷/속옷-여', '머리/기본-여'], tip=(338, 858), pom=(795, 650), 굵기=19,
              손=[(672, 676), (685, 660), (730, 655), (739, 690), (729, 712), (700, 723), (680, 719)],
              지움=[(738, 636, 803, 792)], 원=[(665, 710, 34)]),          # 손잡이 끝의 리본, 둥근 막이
}


def 바탕(g, 그림=None):
    M = 모양[g]
    base = Image.new('RGBA', (1024, 1024), (0, 0, 0, 0))
    if 그림 is not None:
        base.alpha_composite(그림)                    # 겹 대신 통짜 그림(1024)을 쓴다
    for p in ([] if 그림 is not None else M['겹']):
        base.alpha_composite(Image.open(os.path.join(ROOT, 'art/knight/%s.png' % p)))
    a = np.asarray(base).astype(np.float32)
    tip, pom = M['tip'], M['pom']; L = math.hypot(pom[0] - tip[0], pom[1] - tip[1])
    ux, uy = (tip[0] - pom[0]) / L, (tip[1] - pom[1]) / L
    yy, xx = np.mgrid[0:1024, 0:1024]
    t = (xx - pom[0]) * ux + (yy - pom[1]) * uy
    dist = np.abs((xx - pom[0]) * uy - (yy - pom[1]) * ux)
    mask = (dist < M['굵기']) & (t > -25) & (t < L + 25)
    for (cx, cy, r) in M['원']:
        mask |= (xx - cx) ** 2 + (yy - cy) ** 2 < r * r
    hand = Image.new('L', (1024, 1024), 0); ImageDraw.Draw(hand).polygon(M['손'], fill=255)
    mask &= ~(np.asarray(hand) > 0)
    out = a.copy()
    for x in range(1024):                                   # 세로줄마다, 지운 곳을 위아래 색으로 메운다
        col = mask[:, x]
        if not col.any():
            continue
        ys = np.where(col)[0]; runs = np.split(ys, np.where(np.diff(ys) > 1)[0] + 1)
        for r in runs:
            y0, y1 = r[0] - 1, r[-1] + 1
            top = a[y0, x] if y0 >= 0 else None; bot = a[y1, x] if y1 < 1024 else None
            if top is None or bot is None or top[3] < 128 or bot[3] < 128:
                out[r, x] = 0
            else:
                k = ((r - y0) / (y1 - y0))[:, None]
                out[r, x] = top * (1 - k) + bot * k
    for (x0, y0, x1, y1) in M['지움']:
        keep = np.asarray(hand)[y0:y1, x0:x1] > 0
        out[y0:y1, x0:x1][~keep] = 0
    return base, Image.fromarray(out.astype(np.uint8), 'RGBA'), hand, M, L


def 쥐기(base, body, hand, M, L, name):
    tip, pom = M['tip'], M['pom']
    ang = math.degrees(math.atan2(tip[1] - pom[1], pom[0] - tip[0]))
    s = Image.open(os.path.join(ROOT, 'art/무기', name.replace(' ', '') + '.png'))
    W = int(L + 10); s = s.resize((W, max(1, int(s.height * W / s.width))), Image.LANCZOS)
    C = 1700; cv = Image.new('RGBA', (C, C), (0, 0, 0, 0)); cv.alpha_composite(s, (C // 2 - W, C // 2 - s.height // 2))
    cv = cv.rotate(ang, resample=Image.BICUBIC)
    out = body.copy(); lay = Image.new('RGBA', (1024, 1024), (0, 0, 0, 0))
    lay.paste(cv, (pom[0] + 5 - C // 2, pom[1] - 2 - C // 2)); out.alpha_composite(lay)
    out.paste(base, (0, 0), Image.composite(base.getchannel('A'), Image.new('L', (1024, 1024), 0), hand))
    return out


def main(g, path):
    rows = 도감.목록(); base, body, hand, M, L = 바탕(g)
    box = (160, 20, 960, 960); cw, ch = (box[2] - box[0]) // 3, (box[3] - box[1]) // 3
    f = ImageFont.truetype(도감.FONT, 20)
    sh = Image.new('RGBA', (8 * cw, 5 * (ch + 44)), (255, 255, 255, 255)); d = ImageDraw.Draw(sh)
    for i, (n, grade, name) in enumerate(rows):
        c = 쥐기(base, body, hand, M, L, name).crop(box).resize((cw, ch), Image.LANCZOS)
        x, y = (i % 8) * cw, (i // 8) * (ch + 44)
        sh.alpha_composite(c, (x, y))
        col = 도감.COL[grade]; tw = d.textlength(name, font=f)
        d.rounded_rectangle([x + cw // 2 - tw // 2 - 12, y + ch + 2, x + cw // 2 + tw // 2 + 12, y + ch + 34], 10, fill=(40, 44, 50, 255))
        d.text((x + cw // 2, y + ch + 18), name, font=f, fill=col, anchor='mm')
    sh.convert('RGB').save(path); print(path, sh.size)


if __name__ == '__main__':
    g = sys.argv[1] if len(sys.argv) > 1 else '남'
    main(g, sys.argv[2] if len(sys.argv) > 2 else os.path.join(ROOT, 'art/무기/손에든모습-%s.png' % g))
