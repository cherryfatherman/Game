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


def 색맞춤(im):
    """밝은 만화 색의 발판을 먼 배경의 색(어두운 청록 숲)에 맞춘다: 채도를 낮추고, 숲 그늘 색을 입히고, 아래로 갈수록 어둡게."""
    a = np.asarray(im.convert('RGBA')).astype(np.float32); rgb = a[..., :3]
    grey = rgb.mean(axis=2, keepdims=True)
    rgb = grey + (rgb - grey) * 0.58                         # 채도
    rgb = rgb * np.array([0.74, 0.86, 0.80]) * 0.86          # 숲 그늘 색
    h = a.shape[0]; fall = np.linspace(1.06, 0.62, h)[:, None, None]   # 윗면은 빛을 받고 아래는 그늘
    a[..., :3] = np.clip(rgb * fall, 0, 255)
    return Image.fromarray(a.astype(np.uint8), 'RGBA')


def 발판():
    m = importlib.import_module('무기자르기')
    for p, size in m.split(os.path.join(ROOT, 'art/맵/원본/1구역-발판.png'), os.path.join(ROOT, 'art/맵'),
                           ['1구역-땅', '1구역-발판-중', '1구역-발판-소', '1구역-통나무']):
        im = Image.open(p); im = im.resize((im.width // 2, im.height // 2), Image.LANCZOS)
        im = 색맞춤(im); im.save(p); print(os.path.basename(p), im.size)


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


def 윗면(im):
    """발판 그림에서 딛는 윗면의 y(폭의 55% 넘게 차는 첫 줄)."""
    a = np.asarray(im)[..., 3] > 128
    for y in range(a.shape[0]):
        if a[y].sum() > a.shape[1] * 0.55:
            return y
    return 0


def 윗빛(im):
    """유화풍 발판이 어두운 배경에 묻히지 않게: 전체를 조금 밝히고, 딛는 윗면에 아침 햇살을 얹는다."""
    a = np.asarray(im.convert('RGBA')).astype(np.float32); top = 윗면(im); h = a.shape[0]
    y = np.arange(h)[:, None, None]
    lift = 1.22 + 0.55 * np.clip(1 - np.abs(y - top - 6) / 34.0, 0, 1)        # 윗면 둘레가 가장 밝다
    a[..., :3] = np.clip(a[..., :3] * lift * np.array([1.04, 1.03, 0.90]), 0, 255)
    return Image.fromarray(a.astype(np.uint8), 'RGBA')


def 발판_나():
    """배경 그림체(유화풍)로 뽑은 발판."""
    m = importlib.import_module('무기자르기')
    for p, size in m.split(os.path.join(ROOT, 'art/맵/원본/1구역-발판-나.png'), os.path.join(ROOT, 'art/맵'),
                           ['1구역-나-땅', '1구역-나-발판-중', '1구역-나-발판-소', '1구역-나-통나무']):
        im = Image.open(p); im = im.resize((im.width // 2, im.height // 2), Image.LANCZOS)
        im = 윗빛(im); im.save(p)
        importlib.import_module('무기모두자르기').흰틈지우기(p, 6)          # 늘어진 뿌리 사이의 흰 배경
        print(os.path.basename(p), im.size, '윗면', 윗면(im))


def 몬스터(src, dst, 키=300):
    """몬스터 그림을 여백 없이 잘라 키를 맞춘다(발이 그림 맨 아래)."""
    if '원본' in src:
        from cutout import cutout
        tmp = os.path.join(ROOT, 'art/시안/그림체/_tmp.png'); raw = Image.open(src).convert('RGB'); n = max(raw.size)
        sq = Image.new('RGB', (n, n), (255, 255, 255)); sq.paste(raw, ((n - raw.width) // 2, (n - raw.height) // 2)); sq.save(tmp)   # 정사각형으로 맞춰 찌그러지지 않게
        cutout(tmp, tmp, size=1024, pockets=False); im = Image.open(tmp).copy(); os.remove(tmp)
    else:
        im = Image.open(src).convert('RGBA')
    im = im.crop(im.getbbox()); im = im.resize((int(im.width * 키 / im.height), 키), Image.LANCZOS); im.save(dst); print(os.path.basename(dst), im.size)


def 인형_나(g='남'):
    """몬스터 그림체로 다시 그린 기사(통짜 그림)를 같은 자리에서 나눈다."""
    from cutout import cutout
    쥠 = importlib.import_module('무기쥐여보기'); M = 쥠.모양[g]
    tmp = os.path.join(ROOT, 'art/시안/그림체/_k.png'); cutout(os.path.join(ROOT, 'art/시안/그림체/기사-몬스터풍-원본.png'), tmp, size=1024, pockets=False)
    whole = Image.open(tmp).copy(); os.remove(tmp)
    w = np.asarray(whole).copy(); box = w[500:660, 640:700]                    # 팔과 몸 사이에 갇힌 흰 배경
    box[box[..., :3].min(axis=2) > 232] = 0; whole = Image.fromarray(w, 'RGBA')
    saved = M['굵기']; M['굵기'] = 28; base, body, hand, _, _ = 쥠.바탕(g, 그림=whole); M['굵기'] = saved
    a = np.asarray(body).copy(); yy, xx = np.mgrid[0:1024, 0:1024]
    leg = (yy > 706) & (xx > 455) & (xx < 705)
    out = os.path.join(ROOT, 'art/knight/인형')
    def save(name, arr, mask):
        b = arr.copy(); b[~mask] = 0; Image.fromarray(b, 'RGBA').save(os.path.join(out, '%s-나-%s.png' % (g, name)))
    save('몸통', a, ~leg | (yy < 724)); save('왼다리', a, leg & (xx < 578)); save('오른다리', a, leg & (xx >= 578))
    save('손', np.asarray(base).copy(), np.asarray(hand) > 0)
    from PIL import ImageFilter
    hm = Image.open(os.path.join(ROOT, 'art/knight/머리/기본-%s.png' % g)).getchannel('A').filter(ImageFilter.MaxFilter(9))
    save('머리', np.asarray(whole).copy(), np.asarray(hm) > 60)
    print('인형 나', g)


def 발판_다():
    """기준 그림(art/기준/화면-기준.png)에 맞춰 뽑은 발판."""
    m = importlib.import_module('무기자르기')
    for p, size in m.split(os.path.join(ROOT, 'art/맵/원본/1구역-발판-다.png'), os.path.join(ROOT, 'art/맵'),
                           ['1구역-다-땅', '1구역-다-발판-중', '1구역-다-발판-소', '1구역-다-통나무']):
        im = Image.open(p); im = im.resize((im.width // 2, im.height // 2), Image.LANCZOS); im.save(p)
        importlib.import_module('무기모두자르기').흰틈지우기(p, 6)
        print(os.path.basename(p), im.size, '윗면', 윗면(im))


def 인형_다(g='남'):
    """기준 그림체의 기사(검 없이 선 그림)를 몸통, 두 다리, 손, 머리로 나눈다. 좌표는 1024 기준."""
    from cutout import cutout
    from PIL import ImageFilter
    out = os.path.join(ROOT, 'art/knight/인형'); tmp = os.path.join(out, '_t.png')
    cutout(os.path.join(ROOT, 'art/knight/원본/기사-유화-%s.png' % g), tmp, size=1024, pockets=True)
    im = Image.open(tmp).copy(); os.remove(tmp)
    a = np.asarray(im).copy()
    a[..., 3] = np.asarray(Image.fromarray(a[..., 3]).filter(ImageFilter.MinFilter(5)))      # 흰 테를 깎는다
    blob = a[185:220, 345:375]; blob[blob[..., :3].min(axis=2) > 200] = 0                    # 머리카락에 묻은 흰 얼룩
    yy, xx = np.mgrid[0:1024, 0:1024]
    def save(name, mask):
        b = a.copy(); b[~mask] = 0; Image.fromarray(b, 'RGBA').save(os.path.join(out, '%s-다-%s.png' % (g, name)))
    leg = yy > 738
    save('몸통', (yy >= 470) & (yy < 760)); save('왼다리', leg & (xx < 497)); save('오른다리', leg & (xx >= 497))
    save('머리', yy < 500)
    hand = Image.new('L', (1024, 1024), 0); ImageDraw.Draw(hand).polygon([(338, 690), (402, 684), (408, 742), (350, 752)], fill=255)
    save('손', np.asarray(hand) > 0)
    print('인형 다', g)


def 시험세트_라():
    """2026-11-18 시험 세트: 밝은 살빛·고른 빛의 새 기사(검 없이 선 그림)를 인형으로 나누고, 새 다람쥐·먼 배경·가운데 겹을 가로 시험판용으로 만든다.
    확정 전이라 art/시안/시험세트/가로/ 에 둔다. 좌표는 1024 기준."""
    from cutout2 import cutout
    src = os.path.join(ROOT, 'art/시안/시험세트'); out = os.path.join(src, '가로'); os.makedirs(out, exist_ok=True)
    tmp = os.path.join(out, '_t.png')
    cutout(os.path.join(src, '기사-남-4-검없이.png'), tmp, keep=[(850, 560, 1350, 760)], holes=[(790, 1350, 860, 1460)])
    im = Image.open(tmp).resize((1024, 1024), Image.LANCZOS); os.remove(tmp)
    a = np.asarray(im).copy(); yy, xx = np.mgrid[0:1024, 0:1024]
    def save(name, mask):
        b = a.copy(); b[~mask] = 0; Image.fromarray(b, 'RGBA').save(os.path.join(out, '기사-%s.png' % name))
    leg = yy > 805
    save('몸통', (yy >= 440) & (yy < 824)); save('왼다리', leg & (xx < 583)); save('오른다리', leg & (xx >= 583))
    save('머리', yy < 458)
    hand = Image.new('L', (1024, 1024), 0); ImageDraw.Draw(hand).polygon([(662, 658), (744, 658), (744, 732), (662, 732)], fill=255)
    save('손', np.asarray(hand) > 0)
    print('기사 발끝 y', int(np.where(a[..., 3] > 128)[0].max()))
    m = Image.open(os.path.join(src, '누끼/1-01-냄비다람쥐-2.png')); m = m.crop(m.getbbox()); m = m.resize((int(m.width * 300 / m.height), 300), Image.LANCZOS); m.save(os.path.join(out, '다람쥐.png'))
    b = Image.open(os.path.join(src, '1-1-먼배경.png')).convert('RGB'); b = b.resize((1600, int(b.height * 1600 / b.width)), Image.LANCZOS); b.save(os.path.join(out, '먼배경.jpg'), quality=88)
    g = Image.open(os.path.join(src, '누끼/1-1-가운데겹.png')); g = g.resize((1600, int(g.height * 1600 / g.width)), Image.LANCZOS); g.save(os.path.join(out, '가운데겹.png'))
    print('시험세트 라', b.size, g.size, m.size)


if __name__ == '__main__':
    if '라' in sys.argv: 시험세트_라(); sys.exit()
    발판_다(); 인형_다('남')
    몬스터(os.path.join(ROOT, 'art/monsters/원본/1-01-냄비다람쥐-유화.png'), os.path.join(ROOT, 'art/맵/다람쥐-다.png'))
    먼배경(); 발판(); 인형('남')
    발판_나(); 인형_나('남')
    몬스터(os.path.join(ROOT, 'art/monsters/1-01-냄비다람쥐.png'), os.path.join(ROOT, 'art/맵/다람쥐-나.png'))
    몬스터(os.path.join(ROOT, 'art/시안/그림체/다람쥐-기사풍-원본.png'), os.path.join(ROOT, 'art/맵/다람쥐-가.png'))
