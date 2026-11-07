import random, statistics as st
from sim import make_patterns, commit_pick, resolve, draw_cat, draw_tool, FLAG, NC, NT

def grade_stats(design,n=3000,seed=5):
    """各グレードを(必要な枚数を全部ひき直して)出航した場合の成功率・平均報酬・費用"""
    r=random.Random(seed); out={}
    for g,d in design.items():
        succ=0; rew=0; sp=0
        for _ in range(n):
            pats=make_patterns(design,r)
            cats=[draw_cat(r) for _ in range(d['cc'])]
            tools=[draw_tool(r) for _ in range(d['ct'])]
            cats=commit_pick(cats,d['cc']); tl=[t for t in tools if t==FLAG][:1]
            card=r.choice(pats[g])
            if resolve(card,cats,tools):
                succ+=1; rew+=card['rw']; sp+= 1 if card['sp'] else 0
        cost=d['food']+d['cc']+d['ct']
        out[g]=dict(p=succ/n,rew=rew/n,cost=cost,net=rew/n-cost,spec=sp/n)
    return out

def play2(design,G,stats,r,maxturn=60,lower_ok=True,min_ev=0.0):
    pats=make_patterns(design,r)
    coins=3; hc=[]; ht=[]; food=0
    def cost_of(g):
        d=design[g]
        return max(0,d['food']-food),max(0,d['cc']-len(hc)),max(0,d['ct']-len(ht))
    for turn in range(1,maxturn+1):
        coins+=1
        choice=None
        if sum(cost_of(G))<=coins: choice=G
        elif lower_ok:
            cands=[]
            for g in design:
                if g>=G: continue
                c=sum(cost_of(g))
                if c<=coins and stats[g]['net']>min_ev: cands.append((stats[g]['net'],g))
            if cands: choice=max(cands)[1]
        if choice is None: continue
        g=choice; nf,nc,nt=cost_of(g); d=design[g]
        coins-=nf+nc+nt; food+=nf
        for _ in range(nc): hc.append(draw_cat(r))
        for _ in range(nt): ht.append(draw_tool(r))
        cats=commit_pick(hc,d['cc']); tl=[t for t in ht if t==FLAG][:1]
        rest=[t for t in ht if t!=FLAG]
        tools=tl+commit_pick(rest,max(0,d['ct']-len(tl)))
        food-=d['food']
        for c in cats: hc.remove(c)
        for t in tools: ht.remove(t)
        card=r.choice(pats[g])
        if resolve(card,cats,tools):
            coins+=card['rw']
            if card['sp']: return turn
    return maxturn+1

def report(design,n=4000,show=True):
    stt=grade_stats(design)
    if show:
        for g,v in stt.items():
            print(f" g{g}: 費用{v['cost']} 成功率{v['p']:.0%} 平均報酬{v['rew']:.2f} 差引{v['net']:+.2f} 特別財宝/回{v['spec']:.1%}")
    out={}
    for name,(G,low) in {'g1のみ':(1,False),'g2のみ':(2,False),'g3狙い(低は稼ぎ)':(3,True),'g4狙い(低は稼ぎ)':(4,True),'g4一直線':(4,False),'g3一直線':(3,False)}.items():
        r=random.Random(11)
        ts=[play2(design,G,stt,r,lower_ok=low) for _ in range(n)]
        def minN(k): return st.mean([min(ts[i:i+k]) for i in range(0,len(ts)-k+1,k)])
        win=sum(1 for t in ts if t<=60)/len(ts)
        out[name]=(st.mean(ts),st.median(ts),win,minN(2),minN(4))
        if show: print(f"  {name:14s} 平均{st.mean(ts):5.1f} 中央{st.median(ts):4.0f} 到達{win:4.0%} | 2人{minN(2):5.1f} 3人{minN(3):5.1f} 4人{minN(4):5.1f}")
    return out
