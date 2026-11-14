#!/usr/bin/env python3
"""꾸밈 나누기: 기사 그림 한 장을 '머리'와 '옷' 겹으로 나눈다.

모든 그림은 1024 x 1024, 같은 자세, 같은 자리다. 그래서 나눈 겹을 그대로 겹치면 섞어 입힐 수 있다.

  뒷머리 = 몸 뒤로 늘어지는 긴 머리 (양갈래, 긴 머리, 땋은 머리). 옷보다 먼저 그린다.
  옷     = 목깃부터 아래 전부 (무기와 등불도 여기)
  머리   = 머리카락 + 얼굴 + 귀 (턱선까지), 그리고 옷 앞으로 내려오는 머리
  깃     = 옷 가운데 머리 '앞'에 와야 하는 조각 (망토 깃, 털 깃). 머리 위에 한 번 더 그린다.

겹치는 차례: 뒷머리 -> 옷 -> 머리 -> 깃

쓰는 법:  python3 tools/꾸밈나누기.py
만드는 것:
  art/knight/머리/<이름>-남|여.png, <이름>-여-뒤.png(있을 때만)
  art/knight/옷/<이름>-남|여.png, <이름>-남-깃.png(있을 때만)
  art/시안/꾸미기/섞어입기-남.png, 섞어입기-여.png (머리 x 옷 확인판), 눈빛-여.png (눈 색 고치기 전과 후)
"""
import os
import colorsys
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
P = lambda *a: os.path.join(ROOT, *a)
N = 1024
BG = (38, 58, 40)

# =====================================================================================
# 남자: 얼굴은 모든 그림에서 같은 자리에 있다. 턱선과, 그림마다 다른 얼굴 오른쪽 경계로 나눈다.
# =====================================================================================
JAW_M = [(451, 346), (455, 380), (465, 404), (485, 426), (509, 440), (537, 450), (561, 446), (586, 439), (611, 430), (634, 415), (651, 400)]
LEFT_M = [(0, 372), (446, 372)]            # 얼굴 왼쪽: 이 높이 위는 머리카락
# right: 턱선 오른쪽 끝(651,400)에서 그림 오른쪽 끝까지 이어지는 경계 (이 선 위가 머리)
LOOKS_M = {
    '기본': dict(src='art/knight/기본-남.png',
               right=[(676, 402), (706, 409), (712, 372), (1024, 372)]),          # 망토 깃이 볼 옆으로 올라온다
    '속옷': dict(src='art/시안/꾸미기/기본속옷-남.png',
               right=[(635, 416), (636, 438), (657, 438), (673, 423), (693, 403), (701, 372), (1024, 372)]),   # 목 옆으로 뒷머리가 내려온다
    '중세': dict(src='art/시안/꾸미기/중세-남.png', jaw_end=8,                       # 털 깃이 오른쪽 볼을 조금 덮는다
               right=[(628, 425), (640, 410), (660, 385), (676, 379), (700, 372), (1024, 372)]),
    '현대': dict(src='art/시안/꾸미기/현대-남.png',
               right=[(637, 425), (650, 418), (664, 414), (678, 412), (690, 398), (701, 372), (1024, 372)]),   # 옆머리가 모자 위로 내려온다
    '현대2': dict(src='art/시안/꾸미기/현대2-남.png',                               # 같은 점퍼, 검은 칼. 옷으로만 쓴다
               right=[(637, 425), (650, 418), (664, 414), (678, 412), (690, 398), (701, 372), (1024, 372)]),
    '달밤': dict(src='art/시안/꾸미기/달밤-남.png',
               right=[(660, 420), (702, 432), (716, 400), (720, 372), (1024, 372)]),   # 목덜미 잔머리가 깃 위로 삐친다
}
# 머리 이름 -> 어느 그림에서 떼어 오는가. 검은 머리는 목이 드러난 속옷 그림에서 떼야 뒷머리가 온전하다.
HEADS_M = {'기본': '속옷', '중세': '중세', '현대': '현대', '달밤': '달밤'}
OUTFITS_M = ['기본', '속옷', '중세', '현대', '현대2', '달밤']
# 깃: 옷 그림에서 이 네모 안의 조각은 머리 앞에 한 번 더 그린다 (x0, y0, x1, y1)
COLLAR_FRONT = {
    '기본': [(627, 384, 770, 480)],
    '중세': [(380, 392, 474, 490), (624, 374, 790, 490)],
}
# 다른 머리에서 빌려 올 조각: 중세 머리는 털 깃에 가려 볼 끝이 없다. 같은 얼굴인 검은 머리에서 메운다.
BORROW = {'중세': dict(frm='속옷', polys=[[(604, 431), (634, 416), (653, 400), (660, 388), (648, 384), (630, 398), (612, 410), (600, 418)],
                                        [(438, 394), (468, 394), (494, 430), (486, 440), (462, 428), (438, 410)]])}
# 옷 밑에 깔아 둘 살색 조각: 속옷은 목이 드러난다. 검은 뒷머리에 가려 있던 목 오른쪽을 채운다 (다각형, 테두리 선)
UNDER = {'속옷': dict(poly=[(604, 430), (634, 415), (641, 437), (652, 452), (606, 454)], sample=(598, 448), line=[(634, 415), (641, 437), (652, 452)])}
# 배경을 지우다 남은 옅은 초록 얼룩을 지울 자리 (x0, y0, x1, y1)
DEGREEN = {'현대': [(652, 362, 730, 428)], '현대2': [(640, 362, 730, 428), (380, 640, 520, 760)], '달밤': [(380, 720, 470, 800), (640, 380, 730, 440)]}
SMEAR = 26        # 턱 아래로 옷을 이만큼 위로 늘려 둔다. 머리를 바꿔도 목에 틈이 나지 않는다 (머리에 가려 보이지 않는 곳)

# =====================================================================================
# 여자: 얼굴은 같은 자리. 머리카락이 길어서 턱선만으로는 못 나눈다.
#   턱선 위 = 머리.  턱선 아래 = 구역(zone) 안에서 '머리카락 색'인 것만 머리로 떼어 낸다.
#   구역은 대충 넓게 잡은 다각형이고, 그 안에서 색으로 가른다 (hair: 머리카락 색을 집을 자리, other: 옷과 살 색을 집을 자리).
#   layer 'back' = 뒷머리(옷보다 먼저), 'front' = 앞머리(옷 다음).  all=True 는 색을 보지 않고 다 뗀다(리본).
#   fill=True 는 떼어 낸 자리의 옷을 양옆 색으로 메운다(가슴 위로 내려온 땋은 머리 자리).
# =====================================================================================
JAW_F = [(462, 400), (464, 402), (484, 421), (510, 433), (540, 441), (572, 441), (602, 435), (630, 424), (652, 408), (662, 400)]
MIRROR_X = 548                             # 가슴 한가운데의 x (가려진 가슴을 반대쪽에서 비춰 메울 때 쓴다)
SIDE_F = 400                               # 얼굴 양옆: 이 높이 위는 모두 머리
SIDE_L = [(380, 400), (463, 400), (482, 421), (482, 476), (380, 476)]          # 왼쪽 옆머리가 내려오는 자리
# 밝은 머리는 칸의 평균 색으로 가른다. hair_rgb / other_rgb 는 그 평균 색을 재서 적은 것이다 (머리카락 / 옷과 살)
PINK = [(226, 185, 172), (218, 172, 162), (206, 155, 148), (242, 158, 103), (228, 132, 86)]      # 분홍 머리와 주황 리본
BAND = [(440, 400), (680, 400), (700, 480), (420, 480)]                                             # 턱 바로 아래: 목 뒤로 보이는 머리
LOOKS_F = {
    '기본': dict(src='art/knight/기본-여.png', head='기본', hair_rgb=PINK,
               other_rgb=[(199, 155, 131), (247, 229, 214), (233, 217, 197), (246, 244, 243), (249, 219, 205), (180, 216, 235), (204, 204, 210), (204, 179, 179)],
               hair=[(500, 150), (620, 180), (370, 520), (840, 520), (350, 650), (860, 640), (560, 110), (365, 588), (850, 585), (425, 430), (770, 418)],
               other=[(540, 480), (700, 500), (760, 700), (575, 560), (560, 680), (425, 650), (715, 650), (745, 640), (520, 790), (400, 840), (660, 560)]),
    '속옷': dict(src='art/시안/꾸미기/속옷-여.png', head='기본', hair_rgb=PINK,
               other_rgb=[(249, 219, 205), (245, 190, 179), (249, 208, 194), (246, 244, 243), (229, 222, 220), (255, 234, 189), (235, 188, 150)],
               hair=[(500, 150), (620, 180), (370, 520), (840, 520), (350, 650), (870, 640), (365, 588), (850, 585), (425, 432), (770, 418)],
               other=[(560, 470), (470, 520), (410, 690), (700, 560), (560, 560), (540, 690), (455, 700), (520, 780), (585, 425), (670, 460)],
               erase=[[(400, 440), (532, 440), (532, 472), (502, 472), (480, 540), (462, 600), (440, 650), (415, 700), (380, 700), (380, 560), (400, 500)], [(598, 424), (632, 424), (632, 450), (598, 450)]]),
    '중세': dict(src='art/시안/꾸미기/중세-여.png', head='중세', hair_rgb=[(218, 163, 115), (207, 148, 106), (193, 124, 86), (225, 169, 116)],
               other_rgb=[(246, 244, 243), (231, 226, 232), (222, 215, 224), (249, 223, 210), (224, 200, 178), (233, 166, 160), (242, 218, 162), (224, 190, 144), (228, 185, 119), (231, 188, 138), (199, 74, 98), (240, 205, 120)],
               hair=[(500, 190), (640, 230), (380, 560), (840, 580), (340, 620), (870, 640), (420, 480), (790, 470), (605, 560), (595, 640), (610, 500)],
               other=[(545, 545), (530, 590), (410, 660), (715, 640), (475, 530), (700, 525), (530, 690), (445, 740), (770, 730), (520, 465), (640, 700), (480, 800), (575, 430)],
               erase=[[(300, 465), (400, 465), (400, 585), (300, 585)], [(780, 445), (870, 445), (870, 545), (780, 545)]]),
    '현대': dict(src='art/시안/꾸미기/현대-여.png', head='현대', hair_rgb=[(201, 173, 213), (172, 143, 191), (210, 184, 216), (178, 149, 196)],
               other_rgb=[(237, 226, 215), (232, 204, 177), (236, 230, 235), (243, 171, 164), (225, 195, 168), (250, 235, 200), (190, 60, 60)],
               hair=[(480, 220), (420, 380), (740, 400), (430, 440), (720, 440)],
               other=[(450, 560), (700, 540), (690, 490), (560, 480), (600, 540), (560, 500), (575, 445), (610, 452)]),
    '달밤': dict(src='art/시안/꾸미기/달밤-여.png', head='달밤',
               hair=[(500, 130), (430, 430), (760, 430), (790, 650), (800, 720), (720, 480)],
               other=[(470, 560), (700, 570), (720, 740), (470, 490), (560, 500), (540, 680), (560, 580), (575, 445), (720, 680), (775, 652)],
               erase=[[(450, 395), (476, 395), (476, 446), (450, 446)]]),
    '한복': dict(src='art/시안/꾸미기/한복-여.png', head='한복',
               hair=[(480, 120), (430, 420), (740, 500), (760, 560), (820, 620), (800, 575)],
               other=[(640, 520), (480, 560), (700, 600), (590, 470), (560, 700), (575, 445), (810, 750)]),
    '중국': dict(src='art/시안/꾸미기/중국-여.png', head='중국',
               hair=[(550, 120), (435, 420), (680, 420)],
               other=[(560, 520), (480, 480), (690, 480), (575, 440)],
               erase=[[(605, 412), (656, 412), (656, 452), (605, 452)]]),
}
ZONES_F = {
    '기본': [dict(layer='back', poly=BAND), dict(layer='back', poly=[(290, 400), (463, 400), (470, 440), (452, 452), (448, 500), (442, 590), (425, 680), (385, 735), (290, 735)]),
           dict(layer='back', poly=[(662, 400), (915, 400), (915, 725), (800, 725), (800, 640), (745, 560), (700, 470), (662, 432)])],
    '중세': [dict(layer='back', poly=BAND), dict(layer='back', poly=[(270, 400), (463, 400), (480, 440), (480, 560), (450, 600), (400, 640), (380, 720), (270, 720)]),
           dict(layer='back', poly=[(662, 400), (915, 400), (915, 740), (790, 740), (770, 640), (735, 560), (700, 500), (662, 470)]),
           dict(layer='front', fill=True, poly=[(572, 440), (650, 430), (656, 520), (640, 560), (632, 600), (632, 700), (572, 700), (566, 560)])],
    '현대': [dict(layer='back', poly=BAND), dict(layer='front', poly=SIDE_L), dict(layer='front', poly=[(662, 400), (795, 400), (795, 482), (640, 482), (640, 430)])],
    '달밤': [dict(layer='back', poly=BAND), dict(layer='front', poly=SIDE_L),
           dict(layer='back', poly=[(662, 400), (850, 400), (872, 785), (770, 785), (738, 640), (700, 520), (640, 470), (596, 442), (630, 426), (652, 408)]),
           dict(layer='back', all=True, poly=[(752, 538), (820, 538), (820, 604), (772, 604), (752, 586)])],
    '한복': [dict(layer='back', poly=BAND), dict(layer='front', poly=SIDE_L),
           dict(layer='back', poly=[(662, 400), (770, 400), (862, 520), (872, 655), (795, 655), (700, 540), (650, 450)]),
           dict(layer='back', all=True, poly=[(764, 550), (842, 550), (842, 598), (764, 598)])],          # 댕기
    '중국': [dict(layer='back', poly=BAND), dict(layer='front', poly=SIDE_L), dict(layer='front', poly=[(662, 400), (712, 400), (712, 446), (650, 446), (648, 412)])],
}
HEADS_F = ['기본', '중세', '현대', '달밤', '한복', '중국']       # 머리는 제 이름과 같은 그림에서 뗀다
OUTFITS_F = ['기본', '속옷', '중세', '현대', '달밤', '한복', '중국']
# 눈빛 고치기: 그림에서 오른쪽 눈(등불빛)의 홍채가 갈색에 가깝다. 밝은 금빛 주황으로 옮긴다.
# 네모 안에서 주황~갈색인 점만 고친다. 흰 반짝임, 검은 눈동자, 테두리는 그대로 둔다. 머리마다 네모를 따로 줄 수 있다.
IRIS_BOX = (572, 280, 648, 368)
IRIS = {h: IRIS_BOX for h in HEADS_F}
IRIS_HUE, IRIS_SAT, IRIS_VAL = 33 / 360, 1.22, 1.16


# ------------------------------------------------------------------------------------- 도구
def poly_mask(points, feather=1.2):
    """다각형 안이 1인 부드러운 마스크"""
    k = 4
    m = Image.new('L', (N * k, N * k), 0)
    ImageDraw.Draw(m).polygon([(x * k, y * k) for x, y in points], fill=255)
    m = m.resize((N, N), Image.LANCZOS)
    if feather: m = m.filter(ImageFilter.GaussianBlur(feather))
    return np.asarray(m).astype(np.float32) / 255


def load(src):
    return np.asarray(Image.open(P(src)).convert('RGBA')).astype(np.float32)


def save(arr, *path):
    os.makedirs(os.path.dirname(P(*path)), exist_ok=True)
    arr = arr.copy(); arr[arr[..., 3] < 3] = 0
    Image.fromarray(arr.clip(0, 255).astype(np.uint8), 'RGBA').save(P(*path))


def over_keep(dst, src):
    """src 를 dst 위에 얹는다 (둘 다 투명 바탕)"""
    a = src[..., 3:4] / 255; b = dst[..., 3:4] / 255; oa = a + b * (1 - a); out = np.zeros_like(dst)
    out[..., :3] = (src[..., :3] * a + dst[..., :3] * b * (1 - a)) / np.maximum(oa, 1e-6); out[..., 3:4] = oa * 255
    return out


def over(dst, src):
    a = src[..., 3:4] / 255; out = dst.copy()
    out[..., :3] = src[..., :3] * a + dst[..., :3] * (1 - a); out[..., 3:4] = 255 * (a + dst[..., 3:4] / 255 * (1 - a))
    return out


def morph(mask, size, grow):
    im = Image.fromarray((mask * 255).astype(np.uint8))
    return np.asarray(im.filter(ImageFilter.MaxFilter(size) if grow else ImageFilter.MinFilter(size))) > 127


def smear_up(o, x0, x1, cover=None):
    """턱 아래: 옷의 맨 윗줄을 위로 늘려서 머리 밑에 깔아 둔다 (cover 가 있으면 머리에 가려지는 곳에만)"""
    solid = o[..., 3] > 200
    for x in range(x0, x1):
        ys = np.where(solid[380:520, x])[0]
        if len(ys) == 0: continue
        y = 380 + ys[0] + 2
        for k in range(1, SMEAR + 1):
            if o[y - k, x, 3] < 200 and (cover is None or cover[y - k, x]): o[y - k, x] = o[y, x]


# ------------------------------------------------------------------------------------- 남자
def head_polygon_m(look):
    jaw = JAW_M[:look.get('jaw_end', len(JAW_M))]
    return [(0, 0), (N, 0)] + list(reversed(look['right'])) + list(reversed(jaw)) + list(reversed(LEFT_M))


def split_m():
    imgs = {n: load(LOOKS_M[n]['src']) for n in LOOKS_M}
    for n, boxes in DEGREEN.items():
        im = imgs[n]; r, g, bl = im[..., 0], im[..., 1], im[..., 2]
        for x0, y0, x1, y1 in boxes:
            box = np.zeros((N, N), bool); box[y0:y1, x0:x1] = True
            im[..., 3][box & (g - r > 8) & (g - bl > 4) & (g > 120)] = 0
    masks = {n: poly_mask(head_polygon_m(LOOKS_M[n])) for n in LOOKS_M}
    heads, outfits, fronts = {}, {}, {}
    for hn, src in HEADS_M.items():
        h = imgs[src].copy(); h[..., 3] *= masks[src]
        if hn in BORROW:                                   # 가려진 볼 끝을 같은 얼굴에서 메운다
            b = BORROW[hn]; d = imgs[b['frm']].copy(); d[..., 3] *= masks[b['frm']]
            for poly in b['polys']:
                w = poly_mask(poly, 0.8)[..., None]; h = h * (1 - w) + d * w
        heads[hn] = h; save(h, 'art', 'knight', '머리', hn + '-남.png')
    for on in OUTFITS_M:
        o = imgs[on].copy(); o[..., 3] *= 1 - masks[on]
        smear_up(o, JAW_M[2][0] + 6, JAW_M[-2][0] - 4)
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
    return heads, {}, outfits, fronts


# ------------------------------------------------------------------------------------- 여자
def head_polygon_f():
    return [(0, 0), (N, 0), (N, SIDE_F)] + list(reversed(JAW_F)) + [(0, SIDE_F)]


def proto(im, pts):
    return np.array([np.median(im[y - 3:y + 4, x - 3:x + 4, :3].reshape(-1, 3), axis=0) for x, y in pts], np.float32)


def label_regions(mask):
    """이어진 덩어리마다 번호를 붙인다 (선으로 막힌 칸 하나가 한 덩어리)"""
    lab = np.where(mask, np.arange(1, mask.size + 1, dtype=np.int32).reshape(mask.shape), 0)
    while True:
        m = lab.copy()
        m[1:] = np.maximum(m[1:], lab[:-1]); m[:-1] = np.maximum(m[:-1], lab[1:])
        m[:, 1:] = np.maximum(m[:, 1:], lab[:, :-1]); m[:, :-1] = np.maximum(m[:, :-1], lab[:, 1:])
        m[~mask] = 0
        if (m == lab).all(): return lab
        lab = m


def hair_mask(im, look, zone):
    """머리카락인 점과, 옷이나 살이 분명한 점을 돌려준다 (구역 zone 안에서만 본다).
    밝은 머리: 테두리 선으로 막힌 칸마다 평균 색을 보고 칸째로 가른다 (그늘과 반짝임이 있어도 한 칸이다).
    어두운 머리: 선과 머리 색이 같아서 칸으로 못 나눈다. 점마다 색으로 가르고, 가는 선과 점은 버린다."""
    rgb = im[..., :3]; solid = im[..., 3] > 60
    ph = np.array(look['hair_rgb'], np.float32) if 'hair_rgb' in look else proto(im, look['hair'])
    po = np.array(look['other_rgb'], np.float32) if 'other_rgb' in look else proto(im, look['other'])
    lw = np.array([0.3, 0.59, 0.11], np.float32); lum = rgb @ lw
    line = (lum < 105) & solid
    hair = np.zeros((N, N), bool); other = np.zeros((N, N), bool)
    if (ph @ lw).mean() < 95:
        dh = np.min([((rgb - c) ** 2).sum(axis=2) for c in ph], axis=0)
        do = np.min([((rgb - c) ** 2).sum(axis=2) for c in po], axis=0)
        h0 = (dh < do) & solid & zone
        hair = morph(morph(h0, 7, False), 7, True)
        other = solid & (do <= dh) & ~line
        return hair, other, h0
    ys, xs = np.where(zone); y0, y1, x0, x1 = ys.min(), ys.max() + 1, xs.min(), xs.max() + 1
    free = (solid & ~line & morph(zone, 15, True))[y0:y1, x0:x1]
    lab = label_regions(free); ids, inv, cnt = np.unique(lab, return_inverse=True, return_counts=True); inv = inv.reshape(lab.shape)
    sub = rgb[y0:y1, x0:x1]
    mean = np.stack([np.bincount(inv.ravel(), sub[..., c].ravel()) / cnt for c in range(3)], axis=1)
    dh = np.min([((mean - c) ** 2).sum(axis=1) for c in ph], axis=0); do = np.min([((mean - c) ** 2).sum(axis=1) for c in po], axis=0)
    big = (cnt >= 12) & (ids > 0)
    is_hair = big & (dh < do); is_other = big & (dh >= do)
    # 머리카락에 둘러싸인 작은 '옷' 칸은 머리카락의 반짝임이다 (흰색에 가까워서 옷으로 잘못 갈린 것)
    hair[y0:y1, x0:x1] = is_hair[inv]; hs = hair[y0:y1, x0:x1]
    for i in np.where(is_other & (cnt < 700))[0]:
        m = inv == i; ring = morph(m, 11, True) & ~m
        if ring.sum() and (hs & ring).sum() > 0.3 * ring.sum(): is_other[i] = False; is_hair[i] = True
    hair[y0:y1, x0:x1] = is_hair[inv]; other[y0:y1, x0:x1] = is_other[inv]
    return hair & zone, other, hair & zone


def fill_rows(o, hole, zone):
    """떼어 낸 자리를 둘레의 옷 색으로 메운다. 가장자리에서 안쪽으로 한 겹씩 번져 들어가게 하고, 끝으로 살짝 문지른다"""
    todo = hole & zone; known = (o[..., 3] > 200) & ~hole
    col = o[..., :3] * known[..., None]; left = todo.copy()
    for _ in range(400):
        if not left.any(): break
        sm = np.zeros_like(col); cn = np.zeros((N, N), np.float32)
        for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            sm += np.roll(col * known[..., None], (dy, dx), (0, 1)); cn += np.roll(known, (dy, dx), (0, 1))
        new = left & (cn > 0)
        if not new.any(): break
        col[new] = sm[new] / cn[new][:, None]; known |= new; left &= ~new
    done = todo & ~left
    o[done, :3] = col[done]; o[done, 3] = 255
    bl = np.asarray(Image.fromarray(o.clip(0, 255).astype(np.uint8), 'RGBA').filter(ImageFilter.GaussianBlur(4))).astype(np.float32)
    o[done, :3] = bl[done, :3]


def fix_iris(h, box):
    """등불빛 눈의 홍채를 밝은 금빛 주황으로. 반짝임(흰색), 눈동자(검정), 테두리는 건드리지 않는다"""
    x0, y0, x1, y1 = box; reg = h[y0:y1, x0:x1, :3] / 255
    r, g, b = reg[..., 0], reg[..., 1], reg[..., 2]
    mx, mn = reg.max(axis=2), reg.min(axis=2); v = mx; s = np.where(mx > 0, (mx - mn) / np.maximum(mx, 1e-6), 0)
    hue = np.zeros_like(v); d = np.maximum(mx - mn, 1e-6)
    hue = np.where(mx == r, ((g - b) / d) % 6, np.where(mx == g, (b - r) / d + 2, (r - g) / d + 4)) / 6
    iris = (hue > 8 / 360) & (hue < 52 / 360) & (s > 0.42) & (v > 0.34)       # 주황~갈색이고, 살색보다 진한 점
    w = np.asarray(Image.fromarray((iris * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(0.7))).astype(np.float32) / 255
    ns = np.clip(s * IRIS_SAT, 0, 1); nv = np.clip(v * IRIS_VAL, 0, 1)
    nh = IRIS_HUE + (hue - 28 / 360) * 0.35                                   # 색의 결(밝은 곳은 노랗게, 어두운 곳은 붉게)은 조금 남긴다
    out = np.vectorize(colorsys.hsv_to_rgb)(nh, ns, nv)
    new = np.stack(out, axis=2).astype(np.float32)
    h[y0:y1, x0:x1, :3] = (reg * (1 - w[..., None]) + new * w[..., None]) * 255
    return h


def split_f():
    hp = poly_mask(head_polygon_f())
    up = lambda m, d: np.concatenate([m[d:], np.zeros((d, N), m.dtype)])          # 위로 d칸 올린다
    hp_in = up(poly_mask(head_polygon_f(), 0), 6)                                 # 머리 경계보다 6칸 위: 뒷머리와 옷은 여기까지 머리 밑에 깔린다
    imgs, hairs = {}, {}
    for n, look in LOOKS_F.items():
        im = load(look['src'])
        for poly in look.get('erase', []):                 # 배경을 지우다 남은 흰 조각 (팔과 몸 사이, 머리카락 사이)
            m = poly_mask(poly, 0) > 0.5
            im[..., 3][m & (im[..., :3].min(axis=2) > 232)] = 0
        imgs[n] = im
        zs = []
        for z in ZONES_F[look['head']]:
            zm = poly_mask(z['poly'], 0) > 0.5; zm = zm | up(zm, 8)
            if z.get('all'): zs.append((z, zm & (im[..., 3] > 60))); continue
            core, other, h0 = hair_mask(im, look, zm)
            zs.append((z, morph(zm, 5, True) & ((morph(core, 13, True) & ~other) | (morph(core, 25, True) & h0)) & (im[..., 3] > 20)))   # 머리카락을 두른 테두리 선까지 함께 뗀다
        hairs[n] = zs
    soft = lambda m: np.asarray(Image.fromarray((m * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(0.8))).astype(np.float32) / 255
    heads, backs, outfits, before = {}, {}, {}, {}
    for hn in HEADS_F:
        im = imgs[hn]; fm = hp.copy(); bm = np.zeros((N, N), np.float32)
        for z, m in hairs[hn]:
            if z['layer'] == 'front': fm = np.maximum(fm, soft(m))
            else: bm = np.maximum(bm, soft(m))
        h = im.copy(); h[..., 3] *= fm
        before[hn] = h.copy(); h = fix_iris(h, IRIS[hn])
        heads[hn] = h; save(h, 'art', 'knight', '머리', hn + '-여.png')
        if bm.max() > 0:
            b = im.copy(); b[..., 3] *= bm * (1 - hp_in)
            backs[hn] = b; save(b, 'art', 'knight', '머리', hn + '-여-뒤.png')
    for on in OUTFITS_F:
        im = imgs[on]; hole = np.zeros((N, N), bool); fz = np.zeros((N, N), bool)
        for z, m in hairs[on]:
            hole |= m
            if z.get('fill'): fz |= poly_mask(z['poly'], 0) > 0.5
        hole = morph(hole, 3, True)
        o = im.copy(); o[..., 3] *= (1 - hp_in) * (1 - soft(hole))
        if fz.any():                                       # 땋은 머리가 가리던 가슴: 먼저 왼쪽 반을 거울처럼 비춰 메우고, 남은 곳은 둘레 색으로 메운다
            todo = morph(hole, 5, True) & (hp_in < 0.5) & morph(fz, 9, True)
            src = o[:, ::-1].copy(); src = np.roll(src, 2 * MIRROR_X - N, axis=1); good = (src[..., 3] > 240) & todo & (np.arange(N)[None, :] > MIRROR_X)
            o[good] = src[good]; hole2 = todo & ~good
            fill_rows(o, hole2, np.ones((N, N), bool))
        # 머리카락을 떼고 남은 부스러기(몸과 떨어진 테두리 조각, 흰 찌꺼기)를 버린다: 몸통과 이어진 것만 남긴다
        body = Image.fromarray(((o[..., 3] > 60) * 255).astype(np.uint8)).copy(); ImageDraw.floodfill(body, (540, 600), 128)
        o[..., 3] *= morph(np.asarray(body) == 128, 5, True)
        smear_up(o, JAW_F[2][0] + 6, JAW_F[-3][0] - 4, hp > 0.6)
        outfits[on] = o; save(o, 'art', 'knight', '옷', on + '-여.png')
    # 눈빛 고치기 전과 후
    cell = 220; sh = Image.new('RGB', (cell * len(HEADS_F), cell * 2), BG)
    for i, hn in enumerate(HEADS_F):
        for r, src in enumerate((before[hn], heads[hn])):
            bg = np.zeros((N, N, 4), np.float32); bg[..., :3] = BG; bg[..., 3] = 255
            pic = Image.fromarray(over(bg, src).clip(0, 255).astype(np.uint8), 'RGBA').convert('RGB')
            sh.paste(pic.crop((440, 250, 700, 420)).resize((cell, int(cell * 170 / 260)), Image.LANCZOS), (i * cell, r * cell + 30))
    sh.save(P('art', '시안', '꾸미기', '눈빛-여.png'))
    return heads, backs, outfits, {}


# ------------------------------------------------------------------------------------- 확인판
def sheet(heads, backs, outfits, fronts, name, cell=256, crop=(112, 30, 912, 960), zoom=(400, 300, 720, 620)):
    """머리 x 옷 을 겹쳐 본 확인판. 아래 반은 목 둘레를 크게 본 것"""
    hn, on = list(heads), list(outfits)
    out = Image.new('RGB', (cell * len(on), cell * len(hn) * 2), BG)
    for r, h in enumerate(hn):
        for c, o in enumerate(on):
            im = np.zeros((N, N, 4), np.float32); im[..., :3] = BG; im[..., 3] = 255
            for layer in (backs.get(h), outfits[o], heads[h], fronts.get(o)):
                if layer is not None: im = over(im, layer)
            pic = Image.fromarray(im.clip(0, 255).astype(np.uint8), 'RGBA').convert('RGB')
            w = int(cell * (crop[2] - crop[0]) / (crop[3] - crop[1]))
            out.paste(pic.crop(crop).resize((w, cell), Image.LANCZOS), (c * cell + (cell - w) // 2, r * cell))
            out.paste(pic.crop(zoom).resize((cell, cell), Image.LANCZOS), (c * cell, (len(hn) + r) * cell))
    out.save(P('art', '시안', '꾸미기', name))


if __name__ == '__main__':
    import sys
    which = sys.argv[1] if len(sys.argv) > 1 else '남여'
    if '남' in which:
        h, b, o, f = split_m(); sheet(h, b, o, f, '섞어입기-남.png')
        print('남: 머리', list(h), '옷', list(o), '깃', list(f))
    if '여' in which:
        h, b, o, f = split_f(); sheet(h, b, o, f, '섞어입기-여.png', crop=(170, 20, 930, 950))
        print('여: 머리', list(h), '뒷머리', list(b), '옷', list(o))
