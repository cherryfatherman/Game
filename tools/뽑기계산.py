#!/usr/bin/env python3
"""무기 뽑기 숫자를 넣고, 돈을 안 쓰는 사람이 며칠 만에 어디까지 가는지 여러 번 돌려 본다.

  python3 tools/뽑기계산.py

RATE: 뽑기 레벨마다 등급이 나올 확률(%). W: 등급 안에서 무기 여덟 종의 비율.
PITY: 이 횟수 동안 새 무기가 안 나오면 아직 없는 무기를 준다. NEED: 다음 등급을 여는 데 필요한 그 등급 무기 수.
"""
import random, statistics as st
W=[16,15,14,13,12,11,10,9]
RATE={1:[100],2:[70,30],3:[55,35,10],4:[50,33,14,3],5:[50,32,14,3.5,0.3]}
PITY={1:10,2:30,3:100,4:300,5:850}
NEED=88; PER_DAY=30
def run():
    lv=1; own=[[0]*8 for _ in range(5)]; n=0; since=0; ev={}
    while True:
        n+=1; since+=1
        g=random.choices(range(lv),RATE[lv])[0]; top=lv-1
        if since>=PITY[lv] and 0 in own[top]:
            g=top; k=own[top].index(0); since=0
        else:
            k=random.choices(range(8),W)[0]
            if g==top and own[top][k]==0: since=0
        own[g][k]+=1
        if lv<5 and 0 not in own[top] and sum(own[top])>=NEED:
            lv+=1; ev['lv%d'%lv]=n; since=0
        if lv==5:
            if own[4][7] and 'mem' not in ev: ev['mem']=n
            if 0 not in own[4]: ev['all']=n; return ev
R=[run() for _ in range(3000)]
for k in ['lv2','lv3','lv4','lv5','mem','all']:
    v=sorted(r[k]/PER_DAY for r in R); print(k,'중간 %.0f일'%st.median(v),'빠른10%% %.0f'%v[len(v)//10],'느린10%% %.0f'%v[len(v)*9//10],'최악 %.0f'%v[-1])
