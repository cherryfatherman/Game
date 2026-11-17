#!/usr/bin/env python3
"""모든 키우기 시스템을 한 식으로 묶어 스테이지 100곳의 몬스터 체력·방어력·공격력을 낸다.
   python3 tools/밸런스.py        표를 찍는다
   python3 tools/밸런스.py 뽑기   무기 뽑기로 장마다 며칠 걸리는지 돌려 본다
기준: 기획/능력치와 밸런스.md"""
import sys, random
GRADE = ['일반', '고급', '희귀', '영웅', '전설']
# ---- 무기 40자루의 공격력: 등급 안에서 한 단계에 STEP배, 등급이 바뀔 때 JUMP배
STEP = [1.22, 1.22, 1.25, 1.25, 1.60]; JUMP = 1.40
W = []; v = 10.0
for g in range(5):
    row = []
    for k in range(8):
        row.append(v); v *= STEP[g]
    v = row[-1] * JUMP; W.append(row)
# ---- 스테이지마다 맞는 무기 (등급, 단계)
def need(ch, st):
    low = [1, 1, 1, 2, 2, 2, 3, 3, 4, 4]; one = [1, 2, 3, 4, 5, 5, 6, 7, 8, 8]
    if ch == 1: return 0, low[st - 1]
    if ch == 2: return 0, low[st - 1] + 4
    if ch == 3: return 1, low[st - 1]
    if ch == 4: return 1, low[st - 1] + 4
    if ch == 5: return 2, one[st - 1]
    if ch == 6: return 3, one[st - 1]
    if ch == 7: return 3, 8
    return 4, ch - 7            # 8장은 전설 1단계, 9장은 2단계, 10장은 3단계 (앞 장을 끝내고 받은 것)
# ---- 무기 말고 다른 시스템이 "그 스테이지쯤이면 이만큼"인 값 (기준값)
SLOT = [0, 2, 4, 6, 7, 8, 9, 10, 11, 12, 13]                 # 무기 칸·장비 칸 강화 단계 (장의 처음 → 끝)
NECK = [10, 10, 20, 20, 35, 35, 55, 55, 80, 80]              # 목걸이 공격력 % (등급은 장 둘마다)
PETEQ = [0, 10, 20, 20, 40, 40, 70, 70, 120, 120]            # 데리고 다니는 펫의 공격력 %
PETUP = [0, 0, 1, 1, 2, 2, 3, 3, 4, 5]                       # 그 펫의 강화 단계 (한 단계에 +20%)
PETOWN = [0, 2, 5, 9, 17, 25, 41, 57, 87, 102]               # 가진 펫 모두의 보유 효과 % 합
def lerp(a, b, t): return a + (b - a) * t
def others(ch, st):
    i = (ch - 1) * 10 + st; t = (st - 1) / 9
    stat = 1 + 0.04 * i                                       # 능력치 강화(공격력): 스테이지마다 한 레벨, +4%
    slot = lerp(SLOT[ch - 1], SLOT[ch], t)
    wslot = 1 + 0.05 * slot                                   # 무기 칸 강화: 한 단계에 +5%
    neck = 1 + (NECK[ch - 1] / 100) * (1 + 0.05 * slot) if i >= 5 else 1
    pet = 1 + (PETEQ[ch - 1] / 100) * (1 + 0.2 * PETUP[ch - 1]) + PETOWN[ch - 1] / 100
    if ch == 1: pet = 1
    stars = min(ch - 1, 7); lamp_lv = min(100, 12 * stars + (12 * t if ch <= 7 else 0) + (4 * (ch - 8) + 4 * t if ch >= 8 else 0))
    lamp = 1 + 0.01 * lamp_lv                                 # 깜빡이 불씨 레벨: +1%
    book = 1 + 0.005 * i                                      # 전리품 도감: 한 종에 +0.5%
    return dict(능력치=stat, 무기칸=wslot, 목걸이=neck, 펫=pet, 깜빡이=lamp, 도감=book, 칸단계=slot, 불씨=lamp_lv)
def mult(o): return o['능력치'] * o['무기칸'] * o['목걸이'] * o['펫'] * o['깜빡이'] * o['도감']
def stage(ch, st):
    g, k = need(ch, st); o = others(ch, st); A = W[g][k - 1] * mult(o)
    i = (ch - 1) * 10 + st
    hp_player = 100 * (1 + 0.06 * i) * (1 + [0.1, 0.1, 0.25, 0.25, 0.45, 0.45, 0.7, 0.7, 1.0, 1.0][ch - 1] * (1 + 0.05 * o['칸단계']) * 2)
    boss = st == 10
    return dict(ch=ch, st=st, g=g, k=k, A=A, D=0.3 * A, H=0.7 * A * (20 if boss else 1), atk=hp_player / (12 if boss else 30), gold=0.7 * A / 4 * (10 if boss else 1), php=hp_player, o=o)
def fmt(x):
    x = float(x)
    if x >= 1e8: return '%.2f억' % (x / 1e8)
    if x >= 1e4: return '%.1f만' % (x / 1e4)
    return '%d' % round(x)
def hits(A_have, s):                                           # 주는 피해 = 공격력 - 방어력, 적어도 공격력의 10%
    d = max(A_have - s['D'], A_have * 0.1); import math; return math.ceil(s['H'] / d - 1e-9)
def tables():
    print('무기 공격력 (강화 안 했을 때)')
    for g in range(5): print(' ', GRADE[g], ' '.join(fmt(x) for x in W[g]))
    print('\n장 | 스테이지 | 맞는 무기 | 기준 공격력 | 몬스터 체력 | 방어력 | 몬스터 공격력 | 한 마리 골드 | 다른 시스템 배수')
    for ch in range(1, 11):
        for st in (1, 5, 9, 10):
            s = stage(ch, st)
            print('%2d | %d-%d%s | %s %d단계 | %s | %s | %s | %s | %s | ×%.1f' % (ch, ch, st, ' 우두머리' if st == 10 else '', GRADE[s['g']], s['k'], fmt(s['A']), fmt(s['H']), fmt(s['D']), fmt(s['atk']), fmt(s['gold']), mult(s['o'])))
    print('\n무기가 모자랄 때 일반 몬스터 한 마리에 몇 방 (다른 것은 기준값)')
    for ch, st in ((2, 5), (5, 5), (6, 9)):
        s = stage(ch, st); g, k = s['g'], s['k']; m = mult(s['o']); row = []
        for d in range(0, 5):
            kk = k - d
            if kk < 1: break
            row.append('%d단계 아래 %d방' % (d, hits(W[g][kk - 1] * m, s)) if d else '맞는 무기 %d방' % hits(W[g][kk - 1] * m, s))
        print('  %d-%d:' % (ch, st), ', '.join(row))
    print('\n장의 끝에서 다른 시스템이 주는 배수')
    for ch in range(1, 11):
        o = others(ch, 10)
        print('  %2d장: 능력치 ×%.2f · 무기 칸 +%d ×%.2f · 목걸이 ×%.2f · 펫 ×%.2f · 깜빡이 %d레벨 ×%.2f · 도감 ×%.2f → 모두 ×%.1f' % (ch, o['능력치'], round(o['칸단계']), o['무기칸'], o['목걸이'], o['펫'], round(o['불씨']), o['깜빡이'], o['도감'], mult(o)))
    s = stage(10, 10); print('\n가장 큰 한 방(10-10 기준, 스킬 300%% × 치명타 2.3배): %s' % fmt(s['A'] * 3 * 2.3))
# ---- 무기 뽑기: 장마다 며칠 걸리나
TOP, NEXT = 0.22, 0.33; KW = 0.70                              # 가장 높은 등급 22%, 그 아래 33%, 나머지는 더 아래. 단계는 한 단계 오를 때마다 0.7배
def pull(T, rnd):
    r = rnd.random()
    if T == 0: g = 0
    elif r < TOP: g = T
    elif r < TOP + NEXT or T == 1: g = T - 1
    else: g = rnd.randrange(0, T - 1) if T >= 2 else 0
    ws = [KW ** k for k in range(8)]; x = rnd.random() * sum(ws)
    for k in range(8):
        x -= ws[k]
        if x <= 0: return g, k
    return g, 7
def sim(per_day, rnd):
    inv = [[0] * 8 for _ in range(5)]; best = (0, 0); day = 0; n = 0; ch = 1; out = {}
    goal = {1: (0, 4), 2: (0, 8), 3: (1, 4), 4: (1, 8), 5: (2, 8), 6: (3, 8)}
    topg = {1: 0, 2: 0, 3: 1, 4: 1, 5: 2, 6: 3, 7: 4}
    def add(g, k):
        nonlocal best
        inv[g][k] += 1
        while True:
            moved = False
            for gg in range(5):
                for kk in range(8):
                    if inv[gg][kk] >= 11 or (inv[gg][kk] >= 10 and (gg, kk) < best):   # 열 자루를 모으면 한 단계 위로
                        if kk < 7: inv[gg][kk] -= 10; inv[gg][kk + 1] += 1; moved = True
                        elif gg < topg[min(ch, 7)]: inv[gg][kk] -= 10; inv[gg + 1][0] += 1; moved = True
            if not moved: break
        for gg in range(5):
            for kk in range(8):
                if inv[gg][kk] and (gg, kk) > best: best = (gg, kk)
    while ch <= 6 and day < 400:
        day += 1
        for _ in range(per_day + (10 if day == 1 else 0)):
            n += 1; T = topg[ch]
            if n % 100 == 0: add(T, 0)
            else: add(*pull(T, rnd))
            while ch <= 6 and best >= (goal[ch][0], goal[ch][1] - 1): out[ch] = day; ch += 1
    return out
def gacha():
    rnd = random.Random(7)
    for per in (20, 30, 120):
        res = [sim(per, rnd) for _ in range(300)]
        print('하루 %d번:' % per, ' · '.join('%d장 %d일' % (c, sorted(r.get(c, 400) for r in res)[150]) for c in range(1, 7)))
if __name__ == '__main__':
    gacha() if len(sys.argv) > 1 and sys.argv[1] == '뽑기' else tables()
