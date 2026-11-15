#!/usr/bin/env python3
"""무기 네 자루가 한 장에 든 그림을 한 자루씩 잘라 배경을 지운다.

  python3 tools/무기자르기.py 그림.png 나올폴더 이름1 이름2 이름3 이름4

- 위에서 아래로 놓인 순서대로 이름을 붙인다.
- 배경(흰색이든 옅은 초록이든)은 가장자리에서부터 지운다. 칼날 안의 밝은 빛은 남긴다.
- 끈이나 날개가 아래 줄까지 늘어져도 되도록, 줄이 아니라 '이어진 덩어리'로 나눈다.
- 손잡이 막이 안쪽처럼 사방이 막힌 흰 배경은 저절로 지우지 않는다(흰 칼날까지 지워지기 때문).
  지울 곳은 `구멍=[(x, y), ...]`으로 알려 준다. 좌표는 2048 기준이고, `후보()`가 찾아 준다.
- 잘라 낸 그림은 칼끝이 왼쪽, 손잡이가 오른쪽인 채로 여백 없이 저장한다.

여러 장을 한꺼번에 자를 때는 `tools/무기모두자르기.py`를 쓴다.
"""
import os, sys, tempfile
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from cutout import cutout

SIZE = 2048
Q = 4            # 덩어리를 찾을 때 줄여 보는 배율


def 덩어리(mask, 최소=1):
    """참/거짓 그림에서 이어진 덩어리를 찾아 [(넓이, 참거짓배열)] 로 돌려준다. 최소 넓이보다 작은 것은 버린다."""
    arr = np.where(mask, 255, 0).astype(np.uint8)
    im = Image.fromarray(arr).copy()          # copy 를 해야 floodfill 이 먹는다
    out = []
    ys, xs = np.where(mask)
    for y, x in zip(ys.tolist(), xs.tolist()):
        if im.getpixel((x, y)) != 255:
            continue                                  # 이미 센 덩어리
        ImageDraw.floodfill(im, (x, y), 128)
        now = np.asarray(im)
        comp = now == 128
        area = int(comp.sum())
        if area >= 최소:
            out.append((area, comp))
        im = Image.fromarray(np.where(comp, 0, now).astype(np.uint8)).copy()
    return out


def _bbox(c):
    ys, xs = np.where(c)
    return xs.min(), ys.min(), xs.max(), ys.max()


def _gap(a, b):
    ax0, ay0, ax1, ay1 = a; bx0, by0, bx1, by1 = b
    dx = max(bx0 - ax1, ax0 - bx1, 0); dy = max(by0 - ay1, ay0 - by1, 0)
    return max(dx, dy)


def _자르기(src, pockets):
    tmp = os.path.join(tempfile.mkdtemp(), 'c.png')
    cutout(src, tmp, size=SIZE, pockets=pockets)
    return np.asarray(Image.open(tmp)).copy()


def _흰덩어리(rgba):
    """불투명하면서 거의 순백인 곳을 1/4 크기로 찾는다(가는 빛줄기는 뺀다)."""
    white = (rgba[..., 3] > 200) & (rgba[..., :3].min(axis=2) >= 244)
    im = Image.fromarray(np.where(white, 255, 0).astype(np.uint8)).resize((SIZE // Q, SIZE // Q), Image.BILINEAR)
    im = im.point(lambda v: 255 if v > 200 else 0).filter(ImageFilter.MinFilter(3))
    return np.asarray(im) > 0


def 후보(src):
    """무기 안에 갇힌 흰 덩어리들의 (x, y, 넓이)를 돌려준다. 이 가운데 배경인 것만 골라 구멍으로 준다."""
    rgba = _자르기(src, False)
    out = []
    for area, c in 덩어리(_흰덩어리(rgba), 6):
        ys, xs = np.where(c)
        k = np.argmin((xs - xs.mean()) ** 2 + (ys - ys.mean()) ** 2)
        out.append((int(xs[k]) * Q, int(ys[k]) * Q, area * Q * Q))
    return sorted(out, key=lambda t: (t[1] // 450, t[0]))


def split(src, outdir, names, 구멍=()):
    os.makedirs(outdir, exist_ok=True)
    rgba = _자르기(src, False)
    if 구멍:
        im = Image.fromarray(np.where(_흰덩어리(rgba), 255, 0).astype(np.uint8)).copy()
        for (x, y) in 구멍:
            if im.getpixel((x // Q, y // Q)) != 255:
                raise SystemExit('구멍 좌표 (%d, %d) 에 갇힌 흰 덩어리가 없습니다.' % (x, y))
            ImageDraw.floodfill(im, (x // Q, y // Q), 128)
        region = im.point(lambda v: 255 if v == 128 else 0).filter(ImageFilter.MaxFilter(7)).resize((SIZE, SIZE), Image.NEAREST)
        region = np.asarray(region) > 0
        rgb = rgba[..., :3].astype(np.float32)
        d = 255 - rgb.min(axis=2)                       # 흰색에서 얼마나 먼가
        soft = np.clip((d - 14) / (70 - 14), 0, 1)
        af = np.where(region, np.minimum(rgba[..., 3] / 255.0, soft), rgba[..., 3] / 255.0)
        fix = region & (af > 0.02) & (af < 1)
        rgb[fix] = np.clip((rgb[fix] - (1 - af[fix])[:, None] * 255) / af[fix][:, None], 0, 255)
        rgba[..., :3] = rgb.astype(np.uint8); rgba[..., 3] = (af * 255).astype(np.uint8)

    alpha = rgba[..., 3]
    small = np.asarray(Image.fromarray(np.where(alpha > 40, 255, 0).astype(np.uint8)).resize((SIZE // Q, SIZE // Q), Image.BILINEAR)) > 30
    comps = sorted(덩어리(small, 4), key=lambda t: -t[0])
    if len(comps) < len(names):
        raise SystemExit('무기 %d자루를 찾으려 했는데 %d자루만 보입니다. 서로 닿아 있는지 보세요.' % (len(names), len(comps)))
    big = sorted(comps[:len(names)], key=lambda t: _bbox(t[1])[1] + _bbox(t[1])[3])
    masks = [c.copy() for _, c in big]
    boxes = [_bbox(m) for m in masks]
    for area, c in comps[len(names):]:
        if area < 4:
            continue                                   # 먼지
        gaps = [_gap(_bbox(c), b) for b in boxes]
        k = int(np.argmin(gaps))
        if gaps[k] <= 12:                              # 가까이 떨어져 그려진 장식은 그 무기에 붙인다
            masks[k] |= c
    out = []
    for name, m in zip(names, masks):
        mm = Image.fromarray(np.where(m, 255, 0).astype(np.uint8)).filter(ImageFilter.MaxFilter(5)).resize((SIZE, SIZE), Image.NEAREST)
        one = rgba.copy()
        one[..., 3] = np.where(np.asarray(mm) > 0, one[..., 3], 0)
        im = Image.fromarray(one, 'RGBA')
        im = im.crop(im.getbbox())
        p = os.path.join(outdir, name + '.png'); im.save(p); out.append((p, im.size))
    return out


if __name__ == '__main__':
    for p, size in split(sys.argv[1], sys.argv[2], sys.argv[3:]):
        print(p, size)
