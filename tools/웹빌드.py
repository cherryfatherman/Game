#!/usr/bin/env python3
"""웹 빌드: 휴대폰에서 가볍게 돌도록 게임을 dist/ 에 묶는다.

  python3 tools/웹빌드.py

만드는 것
  dist/index.html   게임 한 장. <!doctype>, <html>, <head>, <body> 없이 <title> -> <style> -> 화면 -> <script> 차례다.
                    (올리는 곳이 바깥 틀을 씌운다. 그 틀이 휴대폰의 안전 영역만큼 :root 에 여백을 준다)
  dist/a/*.webp     그림. 한글 이름 대신 짧은 영문 이름을 쓰고, 작게 줄여 WebP 로 바꾼다.

index.html 은 그림 주소를 모두 assetUrl(경로) 로 얻는다. 이 도구가 '원래 경로 -> a/짧은이름.webp' 표를 그 자리에 채워 넣는다.
게임 안의 자리 값(등불, 발바닥, 눈, 자르는 틀)은 1024 그림 기준이고, 실제 그림 너비 / 1024 만큼 줄여 쓰므로 그림이 작아져도 맞는다.
"""
import os
import re
import sys
import json
import shutil
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
P = lambda *a: os.path.join(ROOT, *a)
DIST = P('dist')
QUALITY = 88
SIZE = dict(monster=640, boss=768, knight=640, hero=768, face=256)     # 긴 변(픽셀)
SLUG = {'기본': 'basic', '속옷': 'inner', '중세': 'medieval', '현대': 'modern', '현대2': 'modern2', '달밤': 'moon', '한복': 'hanbok', '중국': 'china'}
SEX = {'남': 'm', '여': 'f'}


def assets():
    """(원래 경로, 짧은 이름, 긴 변) 목록. 게임이 쓰는 그림만 고른다"""
    out = []
    for f in sorted(os.listdir(P('art', 'monsters'))):                 # 몬스터: 1-01-이름.png -> m01
        m = re.match(r'1-(\d\d)-.+\.png$', f)
        if m: out.append(('art/monsters/' + f, 'm' + m.group(1), SIZE['boss'] if m.group(1) == '10' else SIZE['monster']))
    for folder, base in (('머리', 'kh'), ('옷', 'ko')):                 # 기사 겹: 머리, 뒷머리, 옷, 깃
        for f in sorted(os.listdir(P('art', 'knight', folder))):
            m = re.match(r'(.+?)-(남|여)(-뒤|-깃)?\.png$', f)
            if not m: continue
            if m.group(1) not in SLUG: sys.exit('이름표에 없는 그림: ' + f + ' (SLUG 에 더해 주세요)')
            kind = {'-뒤': 'kb', '-깃': 'kf'}.get(m.group(3), base)
            out.append(('art/knight/%s/%s' % (folder, f), '%s-%s-%s' % (kind, SEX[m.group(2)], SLUG[m.group(1)]), SIZE['knight']))
    for f, name, size in (('영웅-얼굴.png', 'hero-m', SIZE['hero']), ('영웅-얼굴-여.png', 'hero-f', SIZE['hero']),
                          ('영웅-얼굴-256.png', 'face-m', SIZE['face']), ('영웅-얼굴-여-256.png', 'face-f', SIZE['face'])):
        out.append(('art/ui/' + f, name, size))
    return out


def to_webp(src, dst, size):
    """줄여서 WebP 로. 투명한 그림은 색에 투명도를 곱한 채로 줄여야 가장자리에 어두운 테가 생기지 않는다"""
    im = Image.open(src)
    alpha = im.mode in ('RGBA', 'LA', 'P') and 'A' in im.convert('RGBA').getbands() and im.convert('RGBA').getextrema()[3][0] < 255
    if alpha:
        im = im.convert('RGBA')
        if max(im.size) > size:
            k = size / max(im.size)
            im = im.convert('RGBa').resize((round(im.width * k), round(im.height * k)), Image.LANCZOS).convert('RGBA')
        im.save(dst, 'WEBP', quality=QUALITY, method=6, alpha_quality=100, exact=False)
    else:
        im = im.convert('RGB')
        if max(im.size) > size:
            k = size / max(im.size); im = im.resize((round(im.width * k), round(im.height * k)), Image.LANCZOS)
        im.save(dst, 'WEBP', quality=QUALITY, method=6)
    return os.path.getsize(dst)


def page(amap):
    """index.html 에서 제목, 꾸밈(style), 화면과 코드만 꺼내 바깥 틀 없는 한 장으로 만든다"""
    src = open(P('index.html'), encoding='utf-8').read()
    title = re.search(r'<title>.*?</title>', src, re.S).group(0)
    style = re.search(r'<style>.*?</style>', src, re.S).group(0)
    body = re.search(r'<body>(.*)</body>', src, re.S).group(1).strip()
    mark = '/*@@ASSET_MAP@@*/null'
    if body.count(mark) != 1: sys.exit('index.html 에 그림 표를 채울 자리(' + mark + ')가 없습니다')
    body = body.replace(mark, json.dumps(amap, ensure_ascii=False, separators=(',', ':')))
    out = title + '\n' + style + '\n' + body + '\n'
    if re.search(r'<\s*(!doctype|html|head|body)\b', out, re.I): sys.exit('바깥 틀 태그가 남아 있습니다')
    if re.search(r'(https?:)?//[a-z0-9.-]+\.[a-z]{2,}/', out, re.I): sys.exit('바깥 주소가 들어 있습니다')
    if '100vh' in out: sys.exit('100vh 를 쓰고 있습니다')
    if not out.startswith('<title>'): sys.exit('<title> 로 시작하지 않습니다')
    return out


def main():
    if os.path.isdir(DIST): shutil.rmtree(DIST)
    os.makedirs(os.path.join(DIST, 'a'))
    amap, total, rows = {}, 0, []
    for path, name, size in assets():
        dst = os.path.join(DIST, 'a', name + '.webp')
        n = to_webp(P(*path.split('/')), dst, size); total += n
        amap[path] = 'a/' + name + '.webp'; rows.append((n, name, path))
    html = page(amap)
    open(os.path.join(DIST, 'index.html'), 'w', encoding='utf-8').write(html)
    hsize = len(html.encode('utf-8')); total += hsize
    for n, name, path in rows: print('%7.1f KB  a/%s.webp  <- %s' % (n / 1024, name, path))
    print('%7.1f KB  index.html' % (hsize / 1024))
    files = len(rows) + 1
    print('모두 %d개, %.2f MB' % (files, total / 1024 / 1024))
    if total > 10 * 1024 * 1024 or files > 120: sys.exit('너무 큽니다 (10 MB, 120개를 넘지 않게)')


if __name__ == '__main__':
    main()
