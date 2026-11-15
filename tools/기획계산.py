#!/usr/bin/env python3
"""기획 문서(기획/)의 숫자를 확인하는 계산 도구.

  python3 tools/기획계산.py          # 전부
  python3 tools/기획계산.py 뽑기     # 무기·동료 뽑기: 며칠 걸리나 (무료 / 월정액 / 많이 쓰는 사람)
  python3 tools/기획계산.py 성장     # 무기·동료·골드 강화를 합친 공격력으로 몇 구역까지 가나

무기 뽑기 규칙은 tools/뽑기계산.py(무기 도감의 1차 값)와 같다. 여기서는 하루 횟수를 바꿔 가며 돌리고,
같은 방식으로 동료 뽑기와 공격력까지 셈한다. 모든 값은 '제안'이고, 실제 사람이 해 본 값이 아니다.
"""
import random, statistics as st, sys, math

# ───────── 무기 뽑기 (무기 도감 1차 값 그대로) ─────────
W_IN = [16, 15, 14, 13, 12, 11, 10, 9]
W_RATE = {1: [100], 2: [70, 30], 3: [55, 35, 10], 4: [50, 33, 14, 3], 5: [50, 32, 14, 3.5, 0.3]}
W_PITY = {1: 10, 2: 30, 3: 100, 4: 300, 5: 850}
W_NEED = 88                      # 8종 + 겹친 것 80자루(8종 모두 강화 5)

# ───────── 동료 뽑기 (제안) ─────────
C_IN = [36, 33, 31]              # 등급 안 세 마리의 비율
C_RATE = {1: [100], 2: [65, 35], 3: [50, 35, 15], 4: [47, 33, 15, 5], 5: [47, 32, 15.4, 5, 0.6]}
C_PITY = {1: 10, 2: 20, 3: 50, 4: 150, 5: 500}
C_NEED_EACH = 11                 # 한 마리마다 1 + 겹친 것 10 (강화 5)

# ───────── 능력치 (제안) ─────────
W_BASE = [10, 60, 360, 2000, 20000]          # 등급 첫 무기의 공격력
W_STEP = [0.5, 3, 18, 100, 1000]             # 한 칸 뒤로 갈 때마다 더해지는 값
W_OWN = [2, 4, 8, 15, 30]                    # 무기 보유 효과 % (한 자루)
C_EQUIP = [[10, 11, 12], [20, 22, 24], [40, 44, 48], [70, 77, 84], [120, 130, 140]]  # 동료 장착 효과 %
C_OWN = [1, 2, 4, 8, 15]                     # 동료 보유 효과 % (한 마리)
LV_GAIN = 0.20                               # 강화 1레벨마다 장착·보유 효과가 처음 값의 20%씩 (5레벨 2배, 10레벨 3배)
ZONE_MULT = 5                                # 구역마다 몬스터 체력 배수 (보고서: 지금 5, 제안 4)
KILLS_PER_DAY = 3000                         # 가정: 하루에 잡는 몬스터 수
GOLD_PRICE0, GOLD_GROW = 32, 1.07            # 골드 강화 값 (게임의 TUNE 값)


class Weapons:
    def __init__(s):
        s.lv = 1; s.own = [[0] * 8 for _ in range(5)]; s.n = 0; s.since = 0; s.ev = {}

    def pull(s):
        s.n += 1; s.since += 1
        lv = s.lv; top = lv - 1
        g = random.choices(range(lv), W_RATE[lv])[0]
        if s.since >= W_PITY[lv] and 0 in s.own[top]:
            g = top; k = s.own[top].index(0); s.since = 0
        else:
            k = random.choices(range(8), W_IN)[0]
            if g == top and s.own[top][k] == 0: s.since = 0
        s.own[g][k] += 1
        if lv < 5 and 0 not in s.own[top] and sum(s.own[top]) >= W_NEED:
            s.lv += 1; s.ev['lv%d' % s.lv] = s.n; s.since = 0
        if s.lv == 5:
            if s.own[4][7] and 'mem' not in s.ev: s.ev['mem'] = s.n
            if 0 not in s.own[4] and 'all' not in s.ev: s.ev['all'] = s.n

    def levels(s, g):            # 등급 g 무기들의 강화 레벨(고르게 올린다고 봄). 1~5레벨은 2자루, 6~10레벨은 4자루
        k = sum(1 for c in s.own[g] if c)
        if not k: return 0
        pool = sum(s.own[g]) - k
        return pool / (2 * k) if pool < 10 * k else 5 + min(5, (pool - 10 * k) / (4 * k))

    def power(s):                # (장착한 무기 공격력, 보유 효과 합 %)
        best = 0; own = 0
        for g in range(5):
            lv = math.floor(s.levels(g))
            for i, c in enumerate(s.own[g]):
                if c:
                    best = max(best, (W_BASE[g] + W_STEP[g] * i) * (1 + LV_GAIN * lv))
                    own += W_OWN[g] * (1 + LV_GAIN * lv)
        return best, own


class Companions:
    def __init__(s):
        s.lv = 1; s.own = [[0] * 3 for _ in range(5)]; s.own[0][0] = 1   # 냄비 다람쥐는 1구역 보스 보상
        s.n = 0; s.since = 0; s.ev = {}

    def pull(s):
        s.n += 1; s.since += 1
        lv = s.lv; top = lv - 1
        g = random.choices(range(lv), C_RATE[lv])[0]
        if s.since >= C_PITY[lv] and 0 in s.own[top]:
            g = top; k = s.own[top].index(0); s.since = 0
        else:
            k = random.choices(range(3), C_IN)[0]
            if g == top and s.own[top][k] == 0: s.since = 0
        s.own[g][k] += 1
        if lv < 5 and min(s.own[top]) >= C_NEED_EACH:
            s.lv += 1; s.ev['lv%d' % s.lv] = s.n; s.since = 0
        if s.lv == 5:
            if s.own[4].count(0) <= 2 and 'first' not in s.ev: s.ev['first'] = s.n
            if 0 not in s.own[4] and 'all' not in s.ev: s.ev['all'] = s.n

    @staticmethod
    def level(c):                # 같은 동료가 겹칠 때마다 쌓인다. 1~5레벨은 2마리, 6~10레벨은 4마리
        d = c - 1
        return d // 2 if d < 10 else 5 + min(5, (d - 10) // 4)

    def power(s):                # 장착 + 보유 효과 합 %
        best = 0; own = 0
        for g in range(5):
            for i, c in enumerate(s.own[g]):
                if c:
                    lv = s.level(c)
                    best = max(best, C_EQUIP[g][i] * (1 + LV_GAIN * lv))
                    own += C_OWN[g] * (1 + LV_GAIN * lv)
        return best + own


def days(cls, per_day, keys, runs=2000):
    out = {k: [] for k in keys}
    for _ in range(runs):
        x = cls()
        while 'all' not in x.ev: x.pull()
        for k in keys: out[k].append(x.ev[k] / per_day)
    return {k: sorted(v) for k, v in out.items()}


def show(title, cls, per_day, keys, names):
    print('\n%s · 하루 %s번' % (title, per_day))
    r = days(cls, per_day, keys)
    for k, nm in zip(keys, names):
        v = r[k]
        print('  %-14s 보통 %4.0f일(%.1f달)  느린 10%% %4.0f일  가장 늦음 %4.0f일' % (nm, st.median(v), st.median(v) / 30, v[len(v) * 9 // 10], v[-1]))


def gacha():
    wk = ['lv2', 'lv3', 'lv4', 'lv5', 'mem', 'all']; wn = ['고급 열림', '희귀 열림', '영웅 열림', '전설 열림', '기억의 검', '전설 8종']
    ck = ['lv2', 'lv3', 'lv4', 'lv5', 'first', 'all']; cn = ['고급 열림', '희귀 열림', '영웅 열림', '전설 열림', '첫 전설 동료', '전설 3마리']
    for name, w, c in [('무료', 30, 10), ('월정액', 40, 13), ('월정액+시즌 패스', 47.5, 15.5), ('살 수 있는 만큼 모두', 77.5, 25.5)]:
        print('\n════ %s ════' % name)
        show('무기', Weapons, w, wk, wn)
        show('동료', Companions, c, ck, cn)
    print('\n════ 무료 + 한 번만 받는 퀘스트 보상(무기 600장, 동료 160장)을 모두 쓴 경우 ════')
    for cls, per, bonus, key, nm in [(Weapons, 30, 600, 'all', '전설 8종'), (Companions, 10, 160, 'all', '전설 3마리')]:
        v = sorted(max(0, (n * per - bonus)) / per for n in days(cls, per, [key])[key])
        print('  %s 보통 %.0f일, 가장 늦음 %.0f일' % (nm, st.median(v), v[-1]))


def need(z):                     # 그 구역 9번 몬스터를 다섯 번에 잡는 공격력 (보고서의 잣대)
    return 20 * 1.2 ** 8 * ZONE_MULT ** (z - 1) / 5


def gold_level(z):               # 그 구역에서 하루 사냥한 골드로 살 수 있는 공격력 강화 레벨
    per_kill = 20 * 1.2 ** 4 * ZONE_MULT ** (z - 1) / 4          # 구역 가운데(5번) 몬스터의 골드
    total = per_kill * KILLS_PER_DAY
    return math.floor(math.log(total * (GOLD_GROW - 1) / GOLD_PRICE0 + 1) / math.log(GOLD_GROW))


def growth(w_per=30, c_per=10, runs=300, last=420):
    hist = [[] for _ in range(last + 1)]          # 날마다: (무기, 무기 보유 %, 동료 %)
    for _ in range(runs):
        w = Weapons(); c = Companions()
        for d in range(1, last + 1):
            for _ in range(w_per): w.pull()
            for _ in range(c_per): c.pull()
            a, o = w.power(); hist[d].append((a, o, c.power()))
    print('\n구역 배수 %d · 하루 무기 %d번, 동료 %d번 · 골드는 하루 %d마리 사냥으로 가정' % (ZONE_MULT, w_per, c_per, KILLS_PER_DAY))
    print('구역 | 필요한 공격력 | 골드 강화 레벨(배수) | 골드 말고 채울 배수 | 보통 며칠째 | 느린 10% | 그때 무기 · 무기 보유 · 동료')
    for z in range(1, 11):
        n = gold_level(z); gm = 1 + 0.1 * n; rest = need(z) / gm
        def day_of(pick):
            for d in range(1, last + 1):
                p = sorted(a * (1 + o / 100) * (1 + cc / 100) for a, o, cc in hist[d])
                if p[pick] >= rest: return d
            return None
        dm = day_of(runs // 2); ds = day_of(runs // 10)
        a, o, cc = sorted(hist[dm], key=lambda t: t[0] * (1 + t[1] / 100) * (1 + t[2] / 100))[runs // 2] if dm else (0, 0, 0)
        print('%2d | %10.0f | %3d (×%.1f) | %9.1f | %s | %s | %.0f · +%.0f%% · +%.0f%%' % (z, need(z), n, gm, rest, dm, ds, a, o, cc))
    for d in [1, 3, 13, 42, 135, 225, 270, 365]:
        a, o, cc = sorted(hist[d], key=lambda t: t[0] * (1 + t[1] / 100) * (1 + t[2] / 100))[runs // 2]
        print('  %3d일째 보통: 무기 %.0f · 무기 보유 +%.0f%% · 동료 +%.0f%% → 골드 빼고 %.0f' % (d, a, o, cc, a * (1 + o / 100) * (1 + cc / 100)))


if __name__ == '__main__':
    random.seed(20261115)
    what = sys.argv[1] if len(sys.argv) > 1 else ''
    if what in ('', '뽑기'): gacha()
    if what in ('', '성장'):
        growth()
        if what == '성장' and len(sys.argv) > 2:
            ZONE_MULT = int(sys.argv[2]); growth()
