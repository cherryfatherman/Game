#!/usr/bin/env python3
"""기사 그림의 칼이 발보다 아래로 내려가지 않게, 몸 밖으로 나온 칼날 부분만 줄인다.
  python3 tools/칼끝.py 입력.png 출력.png [칼날이 몸에서 벗어나는 x(기본 430)]
칼 굵기는 그대로 두고 길이 방향으로만 줄인다. 배경을 지운 1024 그림에 쓴다."""
import sys
import numpy as np
from PIL import Image

def fix(src, dst, px=430, margin=6, half=18):
    im = np.asarray(Image.open(src).convert('RGBA')).astype(np.float32)
    al = im[..., 3] > 40
    xs = np.nonzero(al.any(axis=0))[0]; tx = xs.min(); ty = np.nonzero(al[:, tx])[0].mean()      # 칼끝 = 가장 왼쪽
    x2 = tx + 80; y2 = np.nonzero(al[:, x2])[0].mean()
    d = np.array([x2 - tx, y2 - ty]); d /= np.hypot(*d)                                          # 칼끝에서 손 쪽으로
    P = np.array([tx, ty]) + d * ((px - tx) / d[0])                                              # 줄이기의 기준점
    body = al[:, px + 30:]; feet = np.nonzero(body.sum(axis=1) > 10)[0].max()                    # 발바닥 높이
    L = np.hypot(*(P - [tx, ty])); want = (feet - margin - P[1]) / (-d[1]) if d[1] < 0 else L
    f = min(1.0, want / L)
    if f >= 0.999: Image.open(src).save(dst); return 1.0
    H, W = al.shape; yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    rx, ry = xx - P[0], yy - P[1]
    s = -(rx * d[0] + ry * d[1]); n = rx * d[1] - ry * d[0]                                      # s: 기준점에서 칼끝 쪽 거리
    band = (s > 0) & (np.abs(n) < half) & (s < L + 6)
    out = im.copy(); out[band] = 0
    dest = (s > 0) & (np.abs(n) < half) & (s < L * f + 3)
    ss = s / f                                                                                   # 줄이기 전 자리에서 가져온다
    sx = P[0] - ss * d[0] + n * d[1]; sy = P[1] - ss * d[1] - n * d[0]
    x0 = np.clip(np.floor(sx), 0, W - 2).astype(int); y0 = np.clip(np.floor(sy), 0, H - 2).astype(int)
    fx = (sx - x0)[..., None]; fy = (sy - y0)[..., None]
    pm = im.copy(); pm[..., :3] *= pm[..., 3:4] / 255                                            # 투명도 곱해서 보간
    v = (pm[y0, x0] * (1 - fx) * (1 - fy) + pm[y0, x0 + 1] * fx * (1 - fy) + pm[y0 + 1, x0] * (1 - fx) * fy + pm[y0 + 1, x0 + 1] * fx * fy)
    a = np.maximum(v[..., 3:4], 1e-3); v[..., :3] = v[..., :3] / a * 255
    out[dest] = v[dest]
    Image.fromarray(out.clip(0, 255).astype(np.uint8), 'RGBA').save(dst); return f

if __name__ == '__main__':
    print('줄인 비율', round(fix(sys.argv[1], sys.argv[2], *(int(a) for a in sys.argv[3:4])), 3))
