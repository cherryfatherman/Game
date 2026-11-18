#!/usr/bin/env python3
"""흰 배경 그림(유화풍 캐릭터·몬스터·무기)을 투명한 PNG로 만든다. 원본 크기 그대로 딴다.

  python3 tools/cutout2.py 입력.png 출력.png [--눈=x0,y0,x1,y1]

- 가장자리와 이어진 흰 배경을 지운다.
- 손가락 사이, 팔과 몸 사이, 다리 사이처럼 사방이 막힌 곳에 갇힌 순백도 작은 것까지 지운다.
- 테두리에 묻은 흰 기운을 안쪽 색으로 바꿔서, 어두운 배경에 올려도 밝은 띠가 생기지 않는다.
- 눈의 반짝임처럼 지우면 안 되는 흰 점은 --눈 으로 네모 칸을 알려 주면 남긴다(여러 번 줄 수 있다).
- 그래도 남는 깊은 틈(쥔 손 안쪽 등)은 --틈=x0,y0,x1,y1 로 네모 칸을 짚어 주면 그 안의 흰색을 지운다.
- 나무가 가장자리까지 꽉 찬 배경 겹은 --흰종이 를 붙인다.
- 다 딴 뒤에는 반드시 어두운 바탕과 분홍 바탕에 올려 확대해서 확인한다(tools/cutout2.py --확인 그림.png 확인.jpg).
"""
import sys
import numpy as np
from PIL import Image
from scipy import ndimage as nd

PAPER = 12       # 종이색에서 이만큼 안쪽이면 종이로 본다
LOW, HIGH = 10, 60  # 가장자리에서 반투명이 시작되는 / 완전히 불투명해지는 차이
POCKET_MIN = 12  # 이 넓이(픽셀, 2048 기준)보다 큰 갇힌 흰 덩어리를 지운다
BAND = 5         # 테두리에서 이 폭(픽셀)만큼 흰 기운을 걷어 낸다


def cutout(src, dst, keep=(), flip=False, holes=(), paper=None):
    im = Image.open(src).convert('RGB')
    if flip:
        im = im.transpose(Image.FLIP_LEFT_RIGHT)
    a = np.asarray(im).astype(np.float32)
    h, w = a.shape[:2]
    k = max(w, h) / 2048.0
    edge = np.concatenate([a[:12].reshape(-1, 3), a[-12:].reshape(-1, 3), a[:, :12].reshape(-1, 3), a[:, -12:].reshape(-1, 3)])
    # 그림이 가장자리까지 꽉 찬 배경 겹은 가장자리 색이 종이색이 아니다. 그럴 땐 paper=(255,255,255)를 준다.
    paper = np.median(edge, axis=0) if paper is None else np.array(paper, np.float32)
    dist = np.abs(a - paper).max(axis=2)

    lab, n = nd.label(dist < PAPER)
    outer_ids = np.unique(np.concatenate([lab[0], lab[-1], lab[:, 0], lab[:, -1]]))
    outer_ids = outer_ids[outer_ids > 0]
    bg = np.isin(lab, outer_ids)
    # 갇힌 흰 틈
    sizes = nd.sum(np.ones_like(lab), lab, np.arange(1, n + 1))
    objs = nd.find_objects(lab)
    removed, kept = [], []
    for i in range(n):
        if (i + 1) in outer_ids or sizes[i] < POCKET_MIN * k * k:
            continue
        ys, xs = objs[i]
        cx, cy = (xs.start + xs.stop) // 2, (ys.start + ys.stop) // 2
        if any(x0 <= cx <= x1 and y0 <= cy <= y1 for x0, y0, x1, y1 in keep):
            kept.append((int(sizes[i]), cx, cy))
            continue
        bg |= lab == i + 1
        removed.append((int(sizes[i]), cx, cy))

    # 손으로 짚어 준 틈: 그 네모 칸 안의 밝은 점을 전부 배경으로 본다
    for x0, y0, x1, y1 in holes:
        bg[y0:y1, x0:x1] |= dist[y0:y1, x0:x1] < 60

    # 틈의 꼬리: 손가락 사이처럼 한두 픽셀 폭으로 가늘게 이어지는 흰 금은 조각조각 끊겨서 위에서 빠진다.
    # 이미 지운 배경 바로 곁(4픽셀 안)에 있는 밝은 조각을 크기와 상관없이 따라가며 지운다.
    lab2, n2 = nd.label(dist < 30)
    reach = max(2, round(4 * k))
    for _ in range(12):
        touch = np.unique(lab2[nd.binary_dilation(bg, iterations=reach) & ~bg])
        touch = touch[touch > 0]
        add = np.isin(lab2, touch) & ~bg
        for x0, y0, x1, y1 in keep:
            add[y0:y1, x0:x1] = False
        # 손가락 사이의 외딴 실금: 순백에 가까운 작은 조각이 배경에서 14픽셀 안에 있으면 지운다
        far = np.unique(lab[nd.binary_dilation(bg, iterations=round(14 * k)) & ~bg])
        far = far[far > 0]
        far = far[sizes[far - 1] >= 3]
        add |= np.isin(lab, far) & ~bg
        for x0, y0, x1, y1 in keep:
            add[y0:y1, x0:x1] = False
        if not add.any():
            break
        bg |= add

    # 배경 바로 옆의 밝은 번짐까지 반투명으로
    near = nd.binary_dilation(bg, iterations=max(2, round(4 * k)))
    soft = np.clip((dist - LOW) / (HIGH - LOW), 0, 1)
    alpha = np.where(bg, 0.0, np.where(near, soft, 1.0))

    # 테두리 색 고치기: 테두리 띠에서, 안쪽보다 밝은(=흰 기운이 묻은) 점은 가장 가까운 안쪽 색으로 바꾼다
    solid = alpha >= 0.999
    inner = nd.binary_erosion(solid, iterations=max(2, round(BAND * k)))
    if inner.any():
        _, (iy, ix) = nd.distance_transform_edt(~inner, return_indices=True)
        srcc = a[iy, ix]
        band = ~inner & (alpha > 0)
        lum = a @ np.array([.299, .587, .114], np.float32)
        slum = srcc @ np.array([.299, .587, .114], np.float32)
        # 흰색 쪽으로 물든 정도: 밝아졌고 채도도 빠진 점
        sat = a.max(2) - a.min(2)
        ssat = srcc.max(2) - srcc.min(2)
        fix = band & (lum > slum + 10) & ((alpha < 0.999) | (sat < ssat + 6))
        a = np.where(fix[..., None], srcc, a)
    out = np.dstack([np.clip(a, 0, 255), alpha * 255]).astype(np.uint8)
    Image.fromarray(out, 'RGBA').save(dst)
    return removed, kept


def check(png, jpg, zoom=1):
    """어두운 초록·분홍 바탕에 나란히 올린 확인 그림을 만든다."""
    im = Image.open(png).convert('RGBA')
    box = im.getbbox()
    tiles = []
    for col in ((18, 40, 24, 255), (255, 0, 255, 255)):
        b = Image.new('RGBA', im.size, col)
        b.alpha_composite(im)
        tiles.append(b.crop(box).convert('RGB'))
    o = Image.new('RGB', (tiles[0].width * 2, tiles[0].height))
    o.paste(tiles[0], (0, 0))
    o.paste(tiles[1], (tiles[0].width, 0))
    if zoom != 1:
        o = o.resize((int(o.width * zoom), int(o.height * zoom)), Image.LANCZOS)
    o.save(jpg, quality=92)


if __name__ == '__main__':
    args = [x for x in sys.argv[1:] if not x.startswith('--')]
    if '--확인' in sys.argv:
        check(args[0], args[1])
    else:
        keep = [tuple(int(v) for v in x.split('=')[1].split(',')) for x in sys.argv[1:] if x.startswith('--눈=')]
        holes = [tuple(int(v) for v in x.split('=')[1].split(',')) for x in sys.argv[1:] if x.startswith('--틈=')]
        rm, kp = cutout(args[0], args[1], keep=keep, holes=holes, paper=(255, 255, 255) if '--흰종이' in sys.argv else None)
        print('지운 틈:', rm)
        print('남긴 점:', kp)
