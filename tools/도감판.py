#!/usr/bin/env python3
"""구역 하나의 몬스터 열 마리를 한 장으로 모아 보여 준다.  python3 tools/도감판.py"""
import os
from PIL import Image, ImageDraw, ImageFont
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
F = '/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc'
fT, fN, fB, fS = (ImageFont.truetype(F, s) for s in (54, 36, 25, 23))
TITLE = '1구역 · 이슬숲 길'
ITEMS = [
    ('1-1', '냄비 쓴 다람쥐', '가장 약하다. 냄비를 투구처럼 쓰고 표정만 사납다. 이 게임의 얼굴.', '찌그러진 냄비', '1-01-냄비다람쥐'),
    ('1-2', '박쥐', '날아다녀서 성가시다. 등불을 보면 덮친다.', '박쥐 날개', '1-02-박쥐'),
    ('1-3', '여우', '마르고 날래다. 움직임이 빠르다.', '여우 꼬리', '1-03-여우'),
    ('1-4', '거대 사마귀', '풀숲에서 기다리다 낫발로 내리친다. 한 방이 아프다.', '사마귀 낫발', '1-04-사마귀'),
    ('1-5', '독버섯', '뿌리로 걸어 다닌다. 느리지만 잘 버틴다.', '독버섯 갓', '1-05-독버섯'),
    ('1-6', '멧돼지', '엄니를 앞세워 들이받는다. 숲에서 힘이 가장 세다.', '굽은 엄니', '1-06-멧돼지'),
    ('1-7', '늑대', '이를 드러내고 낮게 다가온다. 숲에서 가장 빠르다.', '늑대 송곳니', '1-07-늑대'),
    ('1-8', '고블린', '녹슨 단검을 든 약탈자. 마을 물건을 훔쳐 간다.', '녹슨 단검', '1-08-고블린'),
    ('1-9', '홉고블린', '고블린 무리의 싸움꾼. 가죽 갑옷이 단단하다.', '이 빠진 큰 칼', '1-09-홉고블린'),
    ('1-10 보스', '고블린 왕', '숲의 우두머리. 쇠못 박힌 전투 망치를 휘두른다.', '찌그러진 왕관', '1-10-고블린왕'),
]
CW, CH, TOP = 460, 700, 120
W, H = CW * 5, TOP + CH * 2 + 20
sh = Image.new('RGBA', (W, H), (34, 46, 36, 255)); d = ImageDraw.Draw(sh)
d.text((W / 2, 62), TITLE, font=fT, fill=(244, 238, 214), anchor='mm')

def wrap(text, font, width):
    lines, cur = [], ''
    for word in text.split(' '):
        t = (cur + ' ' + word).strip()
        if d.textlength(t, font=font) <= width: cur = t
        else: lines.append(cur); cur = word
    return lines + [cur]

for i, (no, name, trait, drop, fn) in enumerate(ITEMS):
    x0, y0 = (i % 5) * CW, TOP + (i // 5) * CH
    boss = '보스' in no
    d.rounded_rectangle([x0 + 12, y0 + 8, x0 + CW - 12, y0 + CH - 8], 18, fill=(58, 50, 62, 255) if boss else (48, 64, 48, 255), outline=(170, 140, 190, 255) if boss else (88, 108, 82, 255), width=3 if boss else 2)
    im = Image.open(os.path.join(ROOT, 'art', 'monsters', fn + '.png')); im = im.crop(im.getbbox()); im.thumbnail((390, 370), Image.LANCZOS)
    sh.alpha_composite(im, (x0 + (CW - im.width) // 2, y0 + 30 + (370 - im.height) // 2))
    d.text((x0 + CW / 2, y0 + 440), no + '  ' + name, font=fN, fill=(244, 238, 214), anchor='mm')
    y = y0 + 482
    for line in wrap(trait, fB, CW - 70):
        d.text((x0 + CW / 2, y), line, font=fB, fill=(206, 212, 190), anchor='ma'); y += 34
    d.rounded_rectangle([x0 + 40, y0 + CH - 82, x0 + CW - 40, y0 + CH - 34], 12, fill=(30, 40, 32, 255))
    d.text((x0 + CW / 2, y0 + CH - 58), '전리품  ' + drop, font=fS, fill=(232, 204, 130), anchor='mm')
out = os.path.join(ROOT, 'art', '1구역-도감판.png')
sh.convert('RGB').save(out); print(out)
