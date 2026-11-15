#!/usr/bin/env python3
"""무기 그림 열 장(art/무기/원본/01~10.png)을 한 자루씩 잘라 art/무기/ 에 이름으로 저장한다.

  python3 tools/무기모두자르기.py          # 열 장 모두
  python3 tools/무기모두자르기.py 4 9      # 4번과 9번 그림만

- 한 장에 든 네 자루의 이름을 위에서 아래 순서로 적는다.
- 구멍: 손잡이 막이 안쪽처럼 사방이 막힌 흰 배경의 좌표(2048 기준). 새 그림을 받으면
  `무기자르기.후보(그림)`으로 갇힌 흰 덩어리를 뽑아 보고, 배경인 것만 여기에 적는다.
  (칼날의 흰 빛, 흰 손잡이, 유리는 적지 않는다.)
- 무기의 순서(등급)는 여기가 아니라 `잊혀진 기사 키우기 세계관/무기 도감.md`가 정한다. 파일 이름에는 번호를 붙이지 않는다.
"""
import os, sys, subprocess
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)

SHEETS = {
    1: (['목검', '녹슨검', '수습기사의검', '경비대의칼'], []),
    2: (['청동검', '사냥꾼의칼', '뱃사람의칼', '넓은검'], [(1708, 1340)]),
    3: (['낫모양검', '북쪽바다의검', '외날넓은칼', '사브르'], [(1708, 1812)]),
    4: (['레이피어', '고리자루칼', '굽은칼', '은검'], [(1492, 276), (1492, 368), (1564, 384), (1764, 396), (1880, 792)]),
    5: (['찌르기검', '물결검', '기사의긴검', '도른의검'], [(1520, 1704), (1520, 1852)]),
    6: (['달밤의칼', '가시덩굴검', '수정검', '폭풍의검'], [(1420, 276)]),
    7: (['얼음검', '불꽃검', '등불검', '기사단장의검'], []),
    8: (['용비늘검', '깊은바다검', '별빛검', '해와달의검'], []),
    9: (['돌에박혀있던검', '잊혀진기사단의검', '마녀의검', '되찾은이름의검'], []),
    10: (['새벽의검', '오로라검', '모래시계검', '기억의검'], []),
}

if __name__ == '__main__':
    if len(sys.argv) == 3 and sys.argv[1] == '--한장':          # 메모리를 아끼려고 한 장씩 따로 돌린다
        sys.path.insert(0, HERE)
        import importlib
        m = importlib.import_module('무기자르기')
        n = int(sys.argv[2]); names, holes = SHEETS[n]
        for p, size in m.split(os.path.join(ROOT, 'art/무기/원본/%02d.png' % n), os.path.join(ROOT, 'art/무기'), names, 구멍=holes):
            print(os.path.basename(p), size)
    else:
        for n in ([int(a) for a in sys.argv[1:]] or sorted(SHEETS)):
            subprocess.run([sys.executable, os.path.abspath(__file__), '--한장', str(n)], check=True)
