#!/usr/bin/env python3
"""무기 도감의 순서대로 무기 40종을 등급 색 칸에 넣은 한 장짜리 그림을 만든다.

  python3 tools/무기도감판.py [나올파일.png]

- 순서와 등급은 `잊혀진 기사 키우기 세계관/무기 도감.md`의 표에서 읽는다.
- 그림은 art/무기/<이름에서 띄어쓰기를 뺀 것>.png 를 쓴다. 없는 무기는 빈 칸으로 둔다.
"""
import os, re, sys
from PIL import Image, ImageDraw, ImageFont
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FONT = '/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc'
COL = {'일반': (232, 232, 232), '고급': (96, 204, 116), '희귀': (86, 156, 255), '영웅': (182, 110, 255), '전설': (255, 92, 84), '신화': (255, 214, 64)}


def 목록():
    rows = []
    for l in open(os.path.join(ROOT, '잊혀진 기사 키우기 세계관/무기 도감.md'), encoding='utf-8'):
        m = re.match(r'^\| (\d+) \| (\S+) \| ([^|]+?) \|', l)
        if m:
            rows.append((int(m.group(1)), m.group(2), m.group(3).strip()))
    return rows


def 칸(d, sh, x, y, S, n, grade, name, f, fs):
    c = COL[grade]
    d.rounded_rectangle([x, y, x + S, y + S], 20, fill=(c[0] // 9 + 22, c[1] // 9 + 24, c[2] // 9 + 26, 255), outline=c, width=5)
    p = os.path.join(ROOT, 'art/무기', name.replace(' ', '') + '.png')
    if os.path.exists(p):
        im = Image.open(p)
        r = im.rotate(-45, expand=True, resample=Image.BICUBIC); r = r.crop(r.getbbox()); r.thumbnail((S - 26, S - 26), Image.LANCZOS)
        sh.alpha_composite(r, (x + S // 2 - r.width // 2, y + S // 2 - r.height // 2))
    d.text((x + S // 2, y + S + 20), name, font=f, fill=c, anchor='mm')


def main(out):
    rows = 목록(); S = 200; GX = 226; GY = 262
    f = ImageFont.truetype(FONT, 20); fs = ImageFont.truetype(FONT, 22); fg = ImageFont.truetype(FONT, 30)
    grades = []
    for _, g, _ in rows:
        if g not in grades: grades.append(g)
    sh = Image.new('RGBA', (110 + 8 * GX, 30 + len(grades) * GY), (18, 22, 24, 255)); d = ImageDraw.Draw(sh)
    for gi, g in enumerate(grades):
        d.text((55, 30 + gi * GY + S // 2), g, font=fg, fill=COL[g], anchor='mm')
        for k, (n, _, name) in enumerate([r for r in rows if r[1] == g]):
            칸(d, sh, 110 + k * GX, 30 + gi * GY, S, n, g, name, f, fs)
    sh.convert('RGB').save(out); print(out, sh.size)


def 길게(out):
    """무기를 한 자루씩 가로로 길게 늘어놓은 그림(두 줄 × 스무 칸)."""
    rows = 목록(); W = 860; H = 200; f = ImageFont.truetype(FONT, 24)
    sh = Image.new('RGBA', (2 * W + 60, 20 * H + 40), (22, 26, 30, 255)); d = ImageDraw.Draw(sh)
    for i, (n, g, name) in enumerate(rows):
        x = 20 + (i // 20) * (W + 20); y = 20 + (i % 20) * H; c = COL[g]
        d.rounded_rectangle([x, y + 4, x + W, y + H - 4], 14, fill=(c[0] // 9 + 22, c[1] // 9 + 24, c[2] // 9 + 26, 255), outline=c, width=2)
        d.text((x + 18, y + H // 2 - 16), g, font=f, fill=c, anchor='lm')
        d.text((x + 18, y + H // 2 + 16), name, font=f, fill=(236, 232, 220), anchor='lm')
        p = os.path.join(ROOT, 'art/무기', name.replace(' ', '') + '.png')
        if os.path.exists(p):
            im = Image.open(p); im.thumbnail((W - 250, H - 12), Image.LANCZOS)
            sh.alpha_composite(im, (x + 225 + (W - 250 - im.width) // 2, y + H // 2 - im.height // 2))
    sh.convert('RGB').save(out); print(out, sh.size)


if __name__ == '__main__':
    main(sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, 'art/무기/도감판.png'))
    길게(os.path.join(ROOT, 'art/무기/한자루씩.png'))
