"""バランス試算(道具が「使うグレード」ごとに決まっている版)
道具: 0シャベル 1ロープ 2ランタン 3ぼうえんきょう 4きゅうきゅうばこ 5コンパス 6おうえんのはた(ぜんぶ)
猫: 0おとぼけ 1わるだくみ 2にこにこ 3やるき 4ぼんやり 5きりり
カード = (指定の猫[...], なんでも猫の数, 指定の道具[...], 報酬, 特別な財宝0/1)"""
import random, statistics as st, itertools
W=[8,8,8,8,8,8,4]; TW=sum(W); FLAG=6
GT={1:[],2:[0],3:[1,2],4:[3,4,5]}          # 各グレードで使う道具
SHIP={1:dict(food=1,xc=0,tl=0),2:dict(food=2,xc=1,tl=1),3:dict(food=4,xc=2,tl=2),4:dict(food=6,xc=3,tl=4)}
def card(cs,ca,ts,rw,sp=0): return dict(cs=list(cs),ca=ca,ts=list(ts),rw=rw,sp=sp)

def resolve(c,cats,tools):
    if FLAG in tools: return True
    a=list(cats)
    for x in c['cs']:
        if x in a: a.remove(x)
        else: return False
    if len(a)<c['ca']: return False
    t=list(tools)
    for x in c['ts']:
        if x in t: t.remove(x)
        else: return False
    return True

def distinct_first(h,n):
    seen=set();f=[];r=[]
    for x in h:
        if x not in seen: seen.add(x);f.append(x)
        else: r.append(x)
    return (f+r)[:n]

def est_draws(g,miss):   # 欲しい道具を miss 個そろえるのに必要な引き数の目安
    if miss<=0: return 0
    if not GT[g]: return 0
    p=sum(W[t] for t in GT[g])/TW
    return miss/p

def grade_net(design,g,C,T,n=1500,seed=3):
    r=random.Random(seed); ok=0; rew=0
    for _ in range(n):
        cats=distinct_first([r.randrange(6) for _ in range(C[g])],C[g])
        tools=[]
        k=int(round(est_draws(g,T[g])))
        for _ in range(k):
            x=r.choices(range(7),weights=W)[0]
            if x in GT[g] or (x==FLAG and g>=3): tools.append(x)
        tools=distinct_first(tools,SHIP[g]['tl'])
        c=r.choice(design[g])
        if resolve(c,cats,tools): ok+=1; rew+=c['rw']
    cost=C[g]+int(round(est_draws(g,T[g])))
    return dict(p=ok/n,rew=rew/n,cost=cost,net=rew/n-cost)

def play(design,G,C,T,stats,r,lower=True,maxturn=60):
    coins=3;food=1;hc=[];ht=[]
    def useful(g): return [t for t in ht if t in GT[g] or (t==FLAG and g>=3)]
    def plan(g):
        mf=max(0,SHIP[g]['food']-food); mc=max(0,C[g]-len(hc))
        miss=max(0,T[g]-len(useful(g))); dr=int(round(est_draws(g,miss)))
        return mf,mc,dr
    for turn in range(1,maxturn+1):
        coins+=1; food+=1; ch=None
        mf,mc,dr=plan(G)
        if mf+mc+dr<=coins: ch=G
        elif lower:
            cand=[]
            for g in range(1,G):
                a,b,d=plan(g)
                if a+b+d<=coins and stats[g]['net']-a>0.6: cand.append((stats[g]['net']-a,g))
            if cand: ch=max(cand)[1]
        if ch is None: continue
        g=ch; mf,mc,dr=plan(g); coins-=mf+mc+dr; food+=mf
        for _ in range(mc): hc.append(r.randrange(6))
        for _ in range(dr): ht.append(r.choices(range(7),weights=W)[0])
        cats=distinct_first(hc,C[g])
        us=useful(g); tools=distinct_first(us,SHIP[g]['tl'])
        food-=SHIP[g]['food']
        for x in cats: hc.remove(x)
        for x in tools: ht.remove(x)
        c=r.choice(design[g])
        if resolve(c,cats,tools):
            coins+=c['rw']
            if c['sp']: return turn
    return maxturn+1

def evaluate(design,C,T,n=1500,seed=11,show=False):
    stt={g:grade_net(design,g,C,T) for g in range(1,5)}
    out={}
    for name,(G,low) in {'g4狙い(低は稼ぎ)':(4,True),'g4一直線':(4,False),'g3狙い(低は稼ぎ)':(3,True)}.items():
        r=random.Random(seed); ts=[play(design,G,C,T,stt,r,low) for _ in range(n)]
        def minN(k): return st.mean([min(ts[i:i+k]) for i in range(0,len(ts)-k+1,k)])
        out[name]=dict(med=st.median(ts),mean=st.mean(ts),reach=sum(t<=60 for t in ts)/len(ts),n2=minN(2),n3=minN(3),n4=minN(4))
    if show:
        for g,v in stt.items(): print(f" g{g}: 費用{v['cost']} 成功率{v['p']:.0%} 平均報酬{v['rew']:.2f} 差引{v['net']:+.2f}")
        for k,v in out.items(): print(f"  {k:12s} 中央{v['med']:4.0f}T 平均{v['mean']:5.1f}T 到達{v['reach']:4.0%} | 2人{v['n2']:4.1f} 3人{v['n3']:4.1f} 4人{v['n4']:4.1f}")
    return out,stt

def search(design,n=800):
    best=None
    for c3,c4,t2,t3,t4 in itertools.product([2,3],[3,4],[0,1],[1,2],[1,2,3]):
        C={1:1,2:1,3:c3,4:c4}; T={1:0,2:t2,3:t3,4:t4}
        o,_=evaluate(design,C,T,n=n)
        sc=o['g4狙い(低は稼ぎ)']['mean']
        if best is None or sc<best[0]: best=(sc,C,T)
    return best
