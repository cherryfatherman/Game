#!/usr/bin/env python3
"""가로시험.html 을 휴대폰에서 열어 볼 수 있게 dist-가로/ 에 묶는다(그림은 WebP, 이름은 영문 숫자)."""
import os, re
from PIL import Image
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, 'dist-가로'); os.makedirs(os.path.join(OUT, 'a'), exist_ok=True)
html = open(os.path.join(ROOT, '가로시험.html'), encoding='utf-8').read()
html = html.replace("'art/무기/' + w + '.png'", "WFILE[i]")
names = re.search(r"const WEAPONS = \[(.*?)\];", html).group(1).replace("'", '').split(', ')
files = {}
def conv(src):
    if src not in files:
        k = 'a/%02d.webp' % len(files); im = Image.open(os.path.join(ROOT, src))
        if max(im.size) > 1600: im.thumbnail((1600, 1600), Image.LANCZOS)
        im.save(os.path.join(OUT, k), 'WEBP', quality=88); files[src] = k
    return files[src]
html = re.sub(r"'(art/[^']+\.(?:png|jpg))'", lambda m: "'%s'" % conv(m.group(1)), html)
wf = [conv('art/무기/%s.png' % n) for n in names]
html = html.replace('const WEAPONS =', 'const WFILE = %s;\nconst WEAPONS =' % repr(wf))
body = re.search(r'<canvas.*</script>', html, re.S).group(0)
style = re.search(r'<style>.*?</style>', html, re.S).group(0).replace('html, body {', ':root { --bg: #0c120c; }\n  html, body {')
open(os.path.join(OUT, 'index.html'), 'w', encoding='utf-8').write('<title>가로 시험판 1-1</title>\n<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">\n' + style + '\n' + body + '\n')
print(len(files), '개 그림', sum(os.path.getsize(os.path.join(OUT, f)) for f in files.values()) // 1024, 'KB')
