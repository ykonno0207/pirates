"""バランス試算 第6版(失敗なし+ボーナス制/コイン目標でクリア)
- 冒険は必ず「基本コイン」がもらえる。カードの条件(猫・道具)を満たすと「ボーナス」が追加。
- おうえんのはたを乗せると、ボーナスは必ずもらえる。
- 乗せたものは、ボーナスの有無にかかわらず なくなる。
- いまの手持ちコインが TARGET 枚以上になった人が勝ち(コインは買い物で減る)。
道具: 0シャベル 1ロープ 2ランタン 3ぼうえんきょう 4きゅうきゅうばこ 5コンパス 6おうえんのはた
猫:   0おとぼけ 1わるだくみ 2にこにこ 3やるき 4ぼんやり 5きりり
カード = (指定の猫[], なんでも猫の数(合計に数える), 指定の道具[], ボーナス)"""
import random, statistics as st, itertools
W=[8,8,8,8,8,8,4]; FLAG=6
GT={1:[],2:[0],3:[1,2],4:[3,4,5]}
SHIP={1:dict(food=1,xc=0,tl=0),2:dict(food=2,xc=1,tl=1),3:dict(food=4,xc=2,tl=2),4:dict(food=6,xc=3,tl=4)}
def card(cs,ca,ts,bonus): return dict(cs=list(cs),ca=ca,ts=list(ts),bonus=bonus)
def meets(c,cats,tools):
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
def dfirst(h,n):
    seen=set();f=[];r=[]
    for x in h:
        if x not in seen: seen.add(x);f.append(x)
        else: r.append(x)
    return (f+r)[:n]
def pdraw(g): return sum(W[t] for t in GT[g])/sum(W)
CMAX={1:1,2:2,3:2,4:3}; TMAX={1:0,2:1,3:2,4:3}
MODES=('min','cats','full')
def loadout(g,mode):
    if mode=='min': return 1,0
    if mode=='cats': return CMAX[g],0
    return CMAX[g],TMAX[g]
def play(design,base,target,r,stats,maxturn=60,start_coin=3,start_food=1,food_inc=1):
    coins=start_coin;food=start_food;hc=[];ht=[]
    def useful(g): return [t for t in ht if t in GT[g] or (t==FLAG and g>=3)]
    for turn in range(1,maxturn+1):
        coins+=1;food+=food_inc
        best=None
        for g in range(1,5):
            for mode in MODES:
                if g==1 and mode!='min': continue
                nc,nt=loadout(g,mode)
                mf=max(0,SHIP[g]['food']-food); mc=max(0,nc-len(hc))
                mt=max(0,nt-len(useful(g)))
                dr=int(round(mt/pdraw(g))) if (mt>0 and pdraw(g)>0) else 0
                cost=mf+mc+dr
                if cost>coins: continue
                val=stats[(g,mode)]-cost
                key=(val,-cost)
                if best is None or key>best[0]: best=(key,g,mode,nc,nt,mf,mc,dr)
        if best is None: continue
        _,g,mode,nc,nt,mf,mc,dr=best
        coins-=mf+mc+dr;food+=mf
        for _ in range(mc):hc.append(r.randrange(6))
        for _ in range(dr):ht.append(r.choices(range(7),weights=W)[0])
        cats=dfirst(hc,nc);tools=dfirst(useful(g),nt) if nt else []
        food-=SHIP[g]['food']
        for x in cats:hc.remove(x)
        for x in tools:ht.remove(x)
        c=r.choice(design[g]);coins+=base[g]
        if meets(c,cats,tools):coins+=c['bonus']
        if coins>=target:return turn,g
    return maxturn+1,0
def mode_stats(design,base,n=2000,seed=3):
    r=random.Random(seed);out={}
    for g in range(1,5):
        for mode in MODES:
            if g==1 and mode!='min':continue
            nc,nt=loadout(g,mode)
            tot=0
            for _ in range(n):
                cats=dfirst([r.randrange(6) for _ in range(nc)],nc)
                tools=[]
                if nt:
                    k=int(round(nt/pdraw(g)))
                    for _ in range(k):
                        x=r.choices(range(7),weights=W)[0]
                        if x in GT[g] or (x==FLAG and g>=3):tools.append(x)
                    tools=dfirst(tools,nt)
                c=r.choice(design[g]);tot+=base[g]+(c['bonus'] if meets(c,cats,tools) else 0)
            out[(g,mode)]=tot/n
    return out
def evaluate(design,base,target,n=3000,seed=11,show=True):
    stt=mode_stats(design,base)
    r=random.Random(seed);rr=[play(design,base,target,r,stt) for _ in range(n)];ts=[x[0] for x in rr]
    def minN(k):return st.mean([min(ts[i:i+k]) for i in range(0,len(ts)-k+1,k)])
    res=dict(med=st.median(ts),mean=st.mean(ts),reach=sum(t<=60 for t in ts)/n,n2=minN(2),n3=minN(3),n4=minN(4))
    if show:
        print(' 1回の期待コイン(基本+ボーナス、買い物前):',{f'g{k[0]}{k[1]}':round(v,2) for k,v in stt.items()})
        print(f' 目標{target}枚: 中央{res["med"]:.0f}T 平均{res["mean"]:.1f}T 到達{res["reach"]:.0%} | 2人{res["n2"]:.1f} 3人{res["n3"]:.1f} 4人{res["n4"]:.1f}')
    return res,stt
