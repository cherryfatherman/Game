#!/usr/bin/env python3
"""무기 네 자루가 한 장에 든 그림을 한 자루씩 잘라 배경을 지운다.

  python3 tools/무기자르기.py 그림.png 나올폴더 이름1 이름2 이름3 이름4

- 위에서 아래로 놓인 순서대로 이름을 붙인다. 한 자루만 든 그림이면 이름을 하나만 준다.
- 배경은 흰색이든 옅은 초록이든 가장자리에서부터 지운다. 칼날 안의 밝은 빛은 남긴다.
- 잘라 낸 그림은 칼끝이 왼쪽, 손잡이가 오른쪽인 채로 여백 없이 저장한다.
"""
import os, sys, tempfile
import numpy as np
from PIL import Image
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from cutout import cutout


def bands(alpha, want):
    """불투명한 줄이 이어진 구간을 찾아 큰 것부터 want개 고른다."""
    rows = (alpha > 40).sum(axis=1) > 3
    segs, s = [], None
    for y, v in enumerate(rows):
        if v and s is None: s = y
        if not v and s is not None: segs.append((s, y)); s = None
    if s is not None: segs.append((s, len(rows)))
    # 아주 가까운 구간은 한 자루로 합친다 (장식이 떨어져 그려진 경우)
    merged = []
    for a, b in segs:
        if merged and a - merged[-1][1] < 12: merged[-1] = (merged[-1][0], b)
        else: merged.append((a, b))
    merged = sorted(sorted(merged, key=lambda r: r[1] - r[0], reverse=True)[:want])
    return merged


def split(src, outdir, names):
    os.makedirs(outdir, exist_ok=True)
    tmp = os.path.join(tempfile.mkdtemp(), 'c.png')
    cutout(src, tmp, size=2048, pockets=False)
    im = Image.open(tmp); a = np.asarray(im).copy()
    a[1780:, 1750:] = 0                      # 오른쪽 아래 별 표시 자리
    im = Image.fromarray(a)
    found = bands(a[..., 3], len(names))
    if len(found) != len(names):
        raise SystemExit('무기 %d자루를 찾으려 했는데 %d자루만 보입니다.' % (len(names), len(found)))
    out = []
    for name, (y0, y1) in zip(names, found):
        row = im.crop((0, max(0, y0 - 4), im.width, min(im.height, y1 + 4)))
        row = row.crop(row.getbbox())
        p = os.path.join(outdir, name + '.png'); row.save(p); out.append((p, row.size))
    return out


if __name__ == '__main__':
    for p, size in split(sys.argv[1], sys.argv[2], sys.argv[3:]):
        print(p, size)
