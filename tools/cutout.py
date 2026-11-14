#!/usr/bin/env python3
"""몬스터 그림의 종이 배경을 지워 투명한 PNG로 만든다.

  python3 tools/cutout.py 입력.png 출력.png [--flip]

- 가장자리와 이어진 종이색만 지운다. 몸 안의 밝은 부분(배, 이빨)은 남긴다.
- 발밑의 푸른 안개는 반투명으로 남긴다.
- --flip 을 주면 좌우를 뒤집는다(오른쪽을 보는 그림을 왼쪽으로).
"""
import sys
from PIL import Image, ImageDraw, ImageFilter, ImageOps
import numpy as np

LOW, HIGH = 14, 70   # 종이색에서 이만큼 다르면 반투명 시작 / 완전 불투명
NEAR = 26            # 틈새를 따라 들어갈 때 종이로 보는 한계


def cutout(src, dst, flip=False, size=1024):
    im = Image.open(src).convert('RGB')
    if im.size[0] != size:
        im = im.resize((size, size), Image.LANCZOS)
    if flip:
        im = ImageOps.mirror(im)
    a = np.asarray(im).astype(np.int16)
    paper = np.median(np.concatenate([a[:12].reshape(-1, 3), a[-12:].reshape(-1, 3), a[:, :12].reshape(-1, 3), a[:, -12:].reshape(-1, 3)]), axis=0)
    dist = np.abs(a - paper).max(axis=2)
    # 가장자리와 이어진, 종이에 가까운 영역만 배경으로 본다
    cand = Image.fromarray(np.where(dist < HIGH, 255, 0).astype(np.uint8))
    cand = cand.filter(ImageFilter.MinFilter(5))          # 펜 선의 작은 틈으로 새지 않게 막는다
    w, h = cand.size
    for x in range(0, w, 8):
        for y in (0, h - 1):
            if cand.getpixel((x, y)) == 255:
                ImageDraw.floodfill(cand, (x, y), 128)
    for y in range(0, h, 8):
        for x in (0, w - 1):
            if cand.getpixel((x, y)) == 255:
                ImageDraw.floodfill(cand, (x, y), 128)
    bg = np.asarray(cand.point(lambda v: 255 if v == 128 else 0).filter(ImageFilter.MaxFilter(7))) > 0
    # 털이나 가시 사이에 낀 종이색도 지운다: 배경에서 이어지는, 종이와 거의 같은 색만 따라 들어간다.
    near = Image.fromarray(np.where(bg | (dist < NEAR), 255, 0).astype(np.uint8)).copy()
    for x in range(0, w, 8):
        for y in (0, h - 1):
            if near.getpixel((x, y)) == 255:
                ImageDraw.floodfill(near, (x, y), 128)
    for y in range(0, h, 8):
        for x in (0, w - 1):
            if near.getpixel((x, y)) == 255:
                ImageDraw.floodfill(near, (x, y), 128)
    bg = np.asarray(near.point(lambda v: 255 if v == 128 else 0).filter(ImageFilter.MaxFilter(3))) > 0
    alpha = np.full(dist.shape, 255.0)
    soft = np.clip((dist - LOW) / (HIGH - LOW), 0, 1) * 255
    alpha[bg] = soft[bg]
    # 가장자리의 반투명한 점에서 종이색을 빼낸다. 안 그러면 털 사이에 밝은 테가 남는다.
    af = (alpha / 255.0)[..., None]
    rgb = np.where(af > 0.02, (a - (1 - af) * paper) / np.maximum(af, 0.02), a)
    rgb = np.clip(rgb, 0, 255)
    out = np.dstack([rgb.astype(np.uint8), alpha.astype(np.uint8)])
    Image.fromarray(out, 'RGBA').save(dst)


if __name__ == '__main__':
    args = [x for x in sys.argv[1:] if not x.startswith('--')]
    cutout(args[0], args[1], flip='--flip' in sys.argv)
