#!/usr/bin/env python3
"""게임.html 이 쓰는 그림과 자료를 art/게임/ 에 만든다. 그림을 새로 뽑지 않고, 있는 그림을 줄이고 모은다.

  python3 tools/게임자산.py      # 게임.html 을 고친 뒤에도 돌린다. docs/ 가 새로 만들어진다

- 배경: 스테이지마다 가로 1600 JPG (art/게임/bg/1-1.jpg …). 3장 일반 스테이지는 그림이 아직 없어 우두머리 방 그림을 함께 쓴다.
- 몬스터: 누끼 딴 그림을 줄인다 (art/게임/mob/1-01.png …).
- 땅 띠와 발판: 딛는 윗면의 자리를 재서 함께 적는다.
- 기사 인형과 무기.
- 자료: 몬스터 이름, 도감 글, 전리품과 그 설명(몬스터 도감.md), 곳 이름(배경 100곳.md), 1장 글(1구역-글.json)을 art/게임/자료.js 로 낸다.
"""
import os, re, json, shutil
import numpy as np
from PIL import Image
Image.MAX_IMAGE_PIXELS = None
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, 'art/게임')
P = lambda *a: os.path.join(ROOT, *a)


def top(im):
    """딛는 윗면의 y: 폭의 55% 넘게 차는 첫 줄."""
    a = np.asarray(im)[..., 3] > 128
    for y in range(a.shape[0]):
        if a[y].sum() > a.shape[1] * 0.55:
            return y
    return 0


def 배경():
    os.makedirs(P(OUT, 'bg'), exist_ok=True)
    src = {'1-1': 'art/시안/시험세트/1-1-먼배경.png', '1-10': 'art/시안/시험세트/우두머리방/1장-그룸이서있던자리.png',
           '2-10': 'art/시안/시험세트/우두머리방/2장-언덕꼭대기.png', '3-10': 'art/시안/맵/3장/3-10-마상시합장.png'}
    for ch in (1, 2):
        for f in sorted(os.listdir(P('art/시안/맵/%d장' % ch))):
            m = re.match(r'(%d-\d)-.*\.png$' % ch, f)
            if m:
                src[m.group(1)] = 'art/시안/맵/%d장/%s' % (ch, f)
    have = {}
    for k, f in sorted(src.items()):
        im = Image.open(P(f)).convert('RGB'); im = im.resize((1600, round(im.height * 1600 / im.width)), Image.LANCZOS)
        im.save(P(OUT, 'bg', k + '.jpg'), quality=84); have[k] = k
    for i in range(1, 10):
        have['3-%d' % i] = '3-10'          # 3장 일반 스테이지: 그림이 없어 우두머리 방 그림을 쓴다(임시)
    return have


MOBS = {  # 번호: (파일, 화면에서의 키, 나는가, 걷는 빠르기)
    '1-01': ('art/monsters/1-01-냄비다람쥐.png', 120, 0, 50), '1-02': ('art/monsters/1-02-도토리어치.png', 140, 1, 80),
    '1-03': ('art/monsters/1-03-목도리여우.png', 140, 0, 85), '1-04': ('art/monsters/1-04-거대사마귀.png', 195, 0, 40),
    '1-05': ('art/monsters/1-05-우산버섯.png', 185, 0, 28), '1-06': ('art/monsters/1-06-멧돼지.png', 170, 0, 60),
    '1-07': ('art/monsters/1-07-늑대.png', 180, 0, 90), '1-08': ('art/monsters/1-08-나무껍질병사.png', 185, 0, 40),
    '1-09': ('art/monsters/1-09-이끼등곰.png', 240, 0, 45), '1-10': ('art/monsters/1-10-그룸.png', 600, 0, 22),
    '2-01': ('art/monsters/2-01-화분쓴두더지.png', 120, 0, 45), '2-02': ('art/monsters/2-02-이름잊은까마귀.png', 135, 1, 80),
    '2-03': ('art/monsters/2-03-민들레족제비.png', 110, 0, 95), '2-04': ('art/monsters/2-04-방울산양.png', 185, 0, 60),
    '2-05': ('art/monsters/2-05-뭉게양.png', 175, 0, 26), '2-06': ('art/monsters/2-06-연끄는매.png', 165, 1, 85),
    '2-07': ('art/monsters/2-07-목줄끄는개.png', 160, 0, 95), '2-08': ('art/monsters/2-08-돌탑지기.png', 215, 0, 26),
    '2-09': ('art/monsters/2-09-풍차지기.png', 230, 0, 40), '2-10': ('art/monsters/2-10-바람을삼킨거인.png', 660, 0, 20),
    '3-01': ('art/시안/3장/누끼/3-01-창든산토끼.png', 110, 0, 100), '3-02': ('art/시안/3장/누끼/3-02-투구속올빼미.png', 150, 1, 75),
    '3-03': ('art/시안/3장/누끼/3-03-보초서는두루미.png', 215, 0, 35), '3-04': ('art/시안/3장/누끼/3-04-방패진오소리.png', 135, 0, 40),
    '3-05': ('art/시안/3장/누끼/3-05-주인잃은목마.png', 200, 0, 65), '3-06': ('art/시안/3장/누끼/3-06-돌아가는짚인형.png', 190, 0, 24),
    '3-07': ('art/시안/3장/누끼/3-07-스라소니.png', 165, 0, 95), '3-08': ('art/시안/3장/누끼/3-08-그림자수습기사.png', 150, 0, 45),
    '3-09': ('art/시안/3장/누끼/3-09-그림자기수.png', 240, 0, 35), '3-10': ('art/시안/3장/누끼/3-10-마지막그림자기사-3.png', 640, 0, 26),
}


def 몬스터():
    os.makedirs(P(OUT, 'mob'), exist_ok=True); out = {}
    for k, (f, h, fly, sp) in MOBS.items():
        im = Image.open(P(f)).convert('RGBA'); im = im.crop(im.getbbox())
        hh = min(im.height, round(h * 1.6)); im = im.resize((round(im.width * hh / im.height), hh), Image.LANCZOS)
        im.save(P(OUT, 'mob', k + '.png')); out[k] = {'h': h, 'w': round(im.width * h / im.height), 'fly': fly, 'sp': sp}
    return out


PLATS = {  # 장: [(이름, 파일, 화면에서의 폭, 종류)]  종류 float = 떠 있는 것, stand = 땅에 놓인 것
    1: [('흙덩이긴', 'art/시안/맵/1장/발판/흙덩이-긴.png', 560, 'float'), ('흙덩이짧은', 'art/시안/맵/1장/발판/흙덩이-짧은.png', 300, 'float'),
        ('통나무', 'art/시안/맵/1장/발판/통나무.png', 420, 'stand'), ('버섯갓', 'art/시안/맵/1장/발판/버섯갓.png', 300, 'stand')],   # 울짱은 윗면이 뾰족해서 발판으로 쓰지 않는다
    2: [('풀밭긴', 'art/시안/시험세트/2장/앞겹-발판-긴.png', 560, 'float'), ('풀밭짧은', 'art/시안/시험세트/2장/앞겹-발판-짧은.png', 300, 'float'),
        ('건초더미', 'art/시안/맵/2장/발판/건초더미.png', 330, 'stand'), ('수레', 'art/시안/맵/2장/발판/수레.png', 330, 'stand'),
        ('돌담', 'art/시안/맵/2장/발판/돌담.png', 480, 'stand'), ('바위', 'art/시안/맵/2장/발판/바위.png', 330, 'stand')],
    3: [('돌담', 'art/시안/맵/2장/발판/돌담.png', 480, 'stand'), ('바위', 'art/시안/맵/2장/발판/바위.png', 330, 'stand')],   # 3장 발판 그림이 없어 2장 것을 쓴다(임시)
}
GROUND = {1: 'art/시안/맵/1장/발판/땅.png', 2: 'art/시안/맵/2장/발판/땅.png', 3: 'art/시안/맵/3장/땅.png'}


def 발판():
    os.makedirs(P(OUT, 'plat'), exist_ok=True); out = {'ground': {}, 'plat': {}}
    for ch, f in GROUND.items():
        im = Image.open(P(f)).convert('RGBA'); im = im.resize((1600, round(im.height * 1600 / im.width)), Image.LANCZOS)
        im.save(P(OUT, 'plat', '땅-%d.png' % ch)); a = np.asarray(im)
        under = [int(v) for v in a[-6, 800, :3]]
        out['ground'][ch] = {'top': top(im), 'h': im.height, 'under': under}
    for ch, lst in PLATS.items():
        out['plat'][ch] = []
        for name, f, w, kind in lst:
            im = Image.open(P(f)).convert('RGBA'); im = im.resize((w, round(im.height * w / im.width)), Image.LANCZOS)
            fn = '%d-%s.png' % (ch, name); im.save(P(OUT, 'plat', fn))
            out['plat'][ch].append({'img': fn, 'w': w, 'h': im.height, 'top': top(im), 'kind': kind})
    return out


WEAPONS = ['목검', '녹슨검', '청동검', '사냥꾼의칼', '수습기사의검', '뱃사람의칼', '경비대의칼', '넓은검',
           '낫모양검', '달밤의칼', '레이피어', '고리자루칼', '북쪽바다의검', '외날넓은칼', '사브르', '굽은칼']
WNAME = ['목검', '녹슨 검', '청동 검', '사냥꾼의 칼', '수습기사의 검', '뱃사람의 칼', '경비대의 칼', '넓은 검',
         '낫 모양 검', '달밤의 칼', '레이피어', '고리자루 칼', '북쪽 바다의 검', '외날 넓은 칼', '사브르', '굽은 칼']


def 기사와무기():
    os.makedirs(P(OUT, 'knight'), exist_ok=True); os.makedirs(P(OUT, 'weapon'), exist_ok=True)
    for a, b in [('기사-몸통', 'body'), ('기사-왼다리', 'legL'), ('기사-오른다리', 'legR'), ('기사-손', 'hand'), ('기사-머리', 'head'), ('기사-머리-오른쪽', 'headR')]:
        shutil.copy(P('art/시안/시험세트/가로', a + '.png'), P(OUT, 'knight', b + '.png'))
    for i, w in enumerate(WEAPONS):
        im = Image.open(P('art/무기', w + '.png')).convert('RGBA'); im = im.resize((700, round(im.height * 700 / im.width)), Image.LANCZOS)
        im.save(P(OUT, 'weapon', '%02d.png' % i))
    return [{'name': n, 'grade': '일반' if i < 8 else '고급', 'step': i % 8 + 1} for i, n in enumerate(WNAME)]


def 글():
    md = open(P('잊혀진 기사 키우기 세계관/몬스터 도감.md'), encoding='utf-8').read(); mobs = {}; head = None
    for line in md.split('\n'):
        c = [x.strip() for x in line.strip().strip('|').split('|')]
        if line.startswith('| 스테이지'):
            head = c; continue
        m = re.match(r'(\d+)-(\d+)', c[0]) if line.startswith('|') and head else None
        if not m or len(c) != len(head):
            continue
        r = dict(zip(head, c)); k = '%s-%02d' % (m.group(1), int(m.group(2)))
        mobs[k] = {'name': r['몬스터'], 'text': r['도감 글'], 'loot': r['전리품'], 'lootText': r['전리품 설명']}
    places = {}
    for line in open(P('기획/배경 100곳.md'), encoding='utf-8'):
        c = [x.strip() for x in line.strip().strip('|').split('|')]
        m = re.match(r'(\d+)-(\d+)$', c[0]) if line.startswith('|') else None
        if m and len(c) >= 3:
            places['%s-%s' % (m.group(1), m.group(2))] = c[2]
    j = json.load(open(P('잊혀진 기사 키우기 세계관/1구역-글.json'), encoding='utf-8'))
    story = {'opening': j['여는장면']['카드'], 'diary': {'1-%d' % d['스테이지']: d['글'] for d in j['일지']},
             'scene': {s['id']: s['카드'] for s in j['장면']}}
    return mobs, places, story


def 내보내기():
    """깃허브 페이지에 올릴 것만 docs/ 에 모은다. 저장소 전체는 1GB가 넘어서 통째로는 못 올린다.
    깃허브에서 Settings → Pages → 가지를 고르고 폴더를 /docs 로 하면 docs/index.html 이 열린다."""
    docs = P('docs'); shutil.rmtree(docs, ignore_errors=True); os.makedirs(P(docs, 'art'))
    shutil.copy(P('게임.html'), P(docs, 'index.html')); shutil.copytree(OUT, P(docs, 'art/게임'))
    open(P(docs, '.nojekyll'), 'w').close()
    print('docs %.1fMB' % (sum(os.path.getsize(os.path.join(d, x)) for d, _, f in os.walk(docs) for x in f) / 1e6))


if __name__ == '__main__':
    bg = 배경(); mob = 몬스터(); pl = 발판(); weapons = 기사와무기(); text, places, story = 글()
    for k in mob:
        mob[k].update(text.get(k, {}))
    data = {'bg': bg, 'mob': mob, 'ground': pl['ground'], 'plat': pl['plat'], 'weapons': weapons, 'places': places, 'story': story}
    open(P(OUT, '자료.js'), 'w', encoding='utf-8').write('// tools/게임자산.py 가 만든다. 손으로 고치지 않는다.\nwindow.DATA = ' + json.dumps(data, ensure_ascii=False, indent=1) + ';\n')
    n = sum(len(f) for _, _, f in os.walk(OUT)); size = sum(os.path.getsize(os.path.join(d, x)) for d, _, f in os.walk(OUT) for x in f)
    print('파일', n, '크기 %.1fMB' % (size / 1e6), '몬스터', len(mob), '글 없는 몬스터', [k for k in mob if 'name' not in mob[k]])
    print({k: places.get(k) for k in ('1-1', '2-5', '3-7')})
    내보내기()
