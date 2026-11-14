#!/usr/bin/env python3
"""꾸밈 나누기: 기사 그림 한 장을 '머리'와 '옷' 두 겹으로 나눈다.

모든 그림은 1024 x 1024, 같은 자세, 같은 자리다. 그래서 나눈 겹을 그대로 겹치면 섞어 입힐 수 있다.

  머리 = 머리카락 + 얼굴 + 귀 (턱선까지)
  옷   = 목깃부터 아래 전부 (무기와 등불도 여기)
  깃   = 옷 가운데 머리 '앞'에 와야 하는 조각 (망토 깃, 털 깃). 머리 위에 한 번 더 그린다.

겹치는 차례: 옷 -> 머리 -> 깃

쓰는 법:  python3 tools/꾸밈나누기.py
만드는 것:
  art/knight/머리/<이름>-남.png, art/knight/옷/<이름>-남.png, art/knight/옷/<이름>-남-깃.png(있을 때만)
  art/시안/꾸미기/섞어입기-남.png (머리 3 x 옷 4 확인판)
"""
import os
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
P = lambda *a: os.path.join(ROOT, *a)
N = 1024

# 턱선: 얼굴은 모든 그림에서 같은 자리에 있다. 왼쪽 볼에서 턱끝을 지나 오른쪽 볼까지 (바깥 테두리 선 포함)
JAW = [(451, 346), (455, 380), (465, 404), (485, 426), (509, 440), (537, 450), (561, 446), (586, 439), (611, 430), (634, 415), (651, 400)]
LEFT = [(0, 372), (446, 372)]            # 얼굴 왼쪽: 이 높이 위는 머리카락

# 그림마다 다른 것은 얼굴 오른쪽이다. 뒷머리가 내려오는 모양과 깃이 올라오는 모양이 다르다.
# right: 턱선 오른쪽 끝(651,400)에서 그림 오른쪽 끝까지 이어지는 경계 (이 선 위가 머리)
LOOKS = {
    '기본': dict(src='art/knight/기본-남.png',
               right=[(676, 402), (706, 409), (712, 372), (1024, 372)]),          # 망토 깃이 볼 옆으로 올라온다
    '속옷': dict(src='art/시안/꾸미기/기본속옷-남.png',
               right=[(635, 416), (636, 438), (657, 438), (673, 423), (693, 403), (701, 372), (1024, 372)]),   # 목 옆으로 뒷머리가 내려온다
    '중세': dict(src='art/시안/꾸미기/중세-남.png', jaw_end=8,                       # 털 깃이 오른쪽 볼을 조금 덮는다
               right=[(628, 425), (640, 410), (660, 385), (676, 379), (700, 372), (1024, 372)]),
    '현대': dict(src='art/시안/꾸미기/현대-남.png',
               right=[(637, 425), (650, 418), (664, 414), (678, 412), (690, 398), (701, 372), (1024, 372)]),   # 옆머리가 모자 위로 내려온다
}
# 머리 이름 -> 어느 그림에서 떼어 오는가. 검은 머리는 목이 드러난 속옷 그림에서 떼야 뒷머리가 온전하다.
HEADS = {'기본': '속옷', '중세': '중세', '현대': '현대'}
OUTFITS = ['기본', '속옷', '중세', '현대']
# 깃: 옷 그림에서 이 네모 안의 조각은 머리 앞에 한 번 더 그린다 (x0, y0, x1, y1)
COLLAR_FRONT = {
    '기본': [(627, 384, 770, 480)],
    '중세': [(380, 392, 474, 490), (624, 374, 790, 490)],
}
# 다른 머리에서 빌려 올 조각: 중세 머리는 털 깃에 가려 오른쪽 볼 끝이 없다. 같은 얼굴인 검은 머리에서 메운다.
# 왼쪽 턱에는 털 깃 끝이 얼굴 위로 올라와 있다. 그 자리도 검은 머리의 같은 얼굴로 바꾼다.
BORROW = {'중세': dict(frm='속옷', polys=[[(604, 431), (634, 416), (653, 400), (660, 388), (648, 384), (630, 398), (612, 410), (600, 418)],
                                        [(438, 394), (468, 394), (494, 430), (486, 440), (462, 428), (438, 410)]])}
# 옷 밑에 깔아 둘 살색 조각: 속옷은 목이 드러난다. 검은 뒷머리에 가려 있던 목 오른쪽을 채운다 (다각형, 테두리 선)
UNDER = {'속옷': dict(poly=[(604, 430), (634, 415), (641, 437), (652, 452), (606, 454)], sample=(598, 448), line=[(634, 415), (641, 437), (652, 452)])}
# 배경을 지우다 남은 옅은 초록 얼룩을 지울 자리 (x0, y0, x1, y1)
DEGREEN = {'현대': [(652, 362, 730, 428)]}
SMEAR = 26        # 턱 아래로 옷을 이만큼 위로 늘려 둔다. 머리를 바꿔도 목에 틈이 나지 않는다 (머리에 가려 보이지 않는 곳)


def poly_mask(points, feather=1.2):
    """다각형 안이 1인 부드러운 마스크"""
    k = 4
    m = Image.new('L', (N * k, N * k), 0)
    ImageDraw.Draw(m).polygon([(x * k, y * k) for x, y in points], fill=255)
    m = m.resize((N, N), Image.LANCZOS).filter(ImageFilter.GaussianBlur(feather))
    return np.asarray(m).astype(np.float32) / 255


def head_polygon(look):
    jaw = JAW[:look.get('jaw_end', len(JAW))]
    return [(0, 0), (N, 0)] + list(reversed(look['right'])) + list(reversed(jaw)) + list(reversed(LEFT))


def load(name):
    return np.asarray(Image.open(P(LOOKS[name]['src'])).convert('RGBA')).astype(np.float32)


def save(arr, *path):
    os.makedirs(os.path.dirname(P(*path)), exist_ok=True)
    Image.fromarray(arr.clip(0, 255).astype(np.uint8), 'RGBA').save(P(*path))


def split():
    imgs = {n: load(n) for n in LOOKS}
    for n, boxes in DEGREEN.items():
        im = imgs[n]; r, g, bl = im[..., 0], im[..., 1], im[..., 2]
        for x0, y0, x1, y1 in boxes:
            box = np.zeros((N, N), bool); box[y0:y1, x0:x1] = True
            im[..., 3][box & (g - r > 8) & (g - bl > 4) & (g > 120)] = 0
    masks = {n: poly_mask(head_polygon(LOOKS[n])) for n in LOOKS}
    heads, outfits, fronts = {}, {}, {}
    for hn, src in HEADS.items():
        h = imgs[src].copy(); h[..., 3] *= masks[src]
        if hn in BORROW:                                   # 가려진 볼 끝을 같은 얼굴에서 메운다
            b = BORROW[hn]; d = imgs[b['frm']].copy(); d[..., 3] *= masks[b['frm']]
            for poly in b['polys']:
                w = poly_mask(poly, 0.8)[..., None]; h = h * (1 - w) + d * w
        heads[hn] = h; save(h, 'art', 'knight', '머리', hn + '-남.png')
    for on in OUTFITS:
        o = imgs[on].copy(); o[..., 3] *= 1 - masks[on]
        # 턱 아래: 옷의 맨 윗줄을 위로 늘려서 머리 밑에 깔아 둔다
        solid = o[..., 3] > 200
        for x in range(JAW[2][0] + 6, JAW[-2][0] - 4):
            ys = np.where(solid[380:520, x])[0]
            if len(ys) == 0: continue
            y = 380 + ys[0] + 2
            for k in range(1, SMEAR + 1):
                if o[y - k, x, 3] < 200: o[y - k, x] = o[y, x]
        if on in UNDER:                                    # 가려져 있던 살을 채운다 (옷 밑에 깐다)
            u = UNDER[on]; col = imgs[on][u['sample'][1], u['sample'][0], :3]
            pm = Image.new('L', (N, N), 0); ImageDraw.Draw(pm).polygon(u['poly'], fill=255)
            ln = Image.new('L', (N, N), 0); ImageDraw.Draw(ln).line(u['line'], fill=255, width=5)
            patch = np.zeros_like(o); patch[..., :3] = col; patch[..., 3] = np.asarray(pm.filter(ImageFilter.GaussianBlur(1))).astype(np.float32)
            la = np.asarray(ln.filter(ImageFilter.GaussianBlur(0.8))).astype(np.float32)[..., None] / 255
            patch[..., :3] = patch[..., :3] * (1 - la) + np.array([22, 18, 20], np.float32) * la; patch[..., 3] = np.maximum(patch[..., 3], la[..., 0] * 255)
            o = over_keep(patch, o)
        outfits[on] = o; save(o, 'art', 'knight', '옷', on + '-남.png')
        if on in COLLAR_FRONT:
            f = np.zeros_like(o)
            for x0, y0, x1, y1 in COLLAR_FRONT[on]:
                f[y0:y1, x0:x1] = imgs[on][y0:y1, x0:x1]; f[y0:y1, x0:x1, 3] *= 1 - masks[on][y0:y1, x0:x1]
            a = Image.fromarray(f[..., 3].astype(np.uint8)); edge = Image.new('L', (N, N), 0)   # 네모 가장자리를 부드럽게
            for x0, y0, x1, y1 in COLLAR_FRONT[on]: ImageDraw.Draw(edge).rectangle([x0 + 3, y0 + 3, x1 - 4, y1 - 4], fill=255)
            f[..., 3] = np.minimum(f[..., 3], np.asarray(edge.filter(ImageFilter.GaussianBlur(2))).astype(np.float32) * (np.asarray(a) > 0))
            fronts[on] = f; save(f, 'art', 'knight', '옷', on + '-남-깃.png')
    return heads, outfits, fronts


def over_keep(dst, src):
    """src 를 dst 위에 얹는다 (둘 다 투명 바탕)"""
    a = src[..., 3:4] / 255; b = dst[..., 3:4] / 255; oa = a + b * (1 - a); out = np.zeros_like(dst)
    out[..., :3] = (src[..., :3] * a + dst[..., :3] * b * (1 - a)) / np.maximum(oa, 1e-6); out[..., 3:4] = oa * 255
    return out


def over(dst, src):
    a = src[..., 3:4] / 255; out = dst.copy()
    out[..., :3] = src[..., :3] * a + dst[..., :3] * (1 - a); out[..., 3:4] = 255 * (a + dst[..., 3:4] / 255 * (1 - a))
    return out


def sheet(heads, outfits, fronts, cell=256, zoom=True):
    """머리 3 x 옷 4 를 겹쳐 본 확인판. 아래 반은 목 둘레를 크게 본 것"""
    hn, on = list(heads), list(outfits)
    W, H = cell * len(on), cell * len(hn) * (2 if zoom else 1)
    out = Image.new('RGB', (W, H), (38, 58, 40))
    for r, h in enumerate(hn):
        for c, o in enumerate(on):
            im = np.zeros((N, N, 4), np.float32); im[..., :3] = (38, 58, 40); im[..., 3] = 255
            im = over(im, outfits[o]); im = over(im, heads[h])
            if o in fronts: im = over(im, fronts[o])
            pic = Image.fromarray(im.clip(0, 255).astype(np.uint8), 'RGBA').convert('RGB')
            out.paste(pic.crop((112, 30, 912, 960)).resize((int(cell * 800 / 930), cell), Image.LANCZOS), (c * cell + 18, r * cell))
            if zoom: out.paste(pic.crop((400, 300, 720, 620)).resize((cell, cell), Image.LANCZOS), (c * cell, (len(hn) + r) * cell))
    out.save(P('art', '시안', '꾸미기', '섞어입기-남.png'))


if __name__ == '__main__':
    h, o, f = split()
    sheet(h, o, f)
    print('머리', list(h), '옷', list(o), '깃', list(f))
