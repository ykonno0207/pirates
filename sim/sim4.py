import random, statistics as st, copy
from sim import make_patterns, commit_pick, resolve, draw_cat, draw_tool, FLAG

def grade_stats4(design,n=3000,seed=5):
    r=random.Random(seed); out={}
    for g,d in design.items():
        succ=rew=sp=0
        for _ in range(n):
            pats=make_patterns(design,r)
            cats=[draw_cat(r) for _ in range(d['cc'])]
            tools=[draw_tool(r) for _ in range(d['ct'])]
            cats=commit_pick(cats,d['cc'])
            card=r.choice(pats[g])
            if resolve(card,cats,tools):
                succ+=1; rew+=card['rw']; sp+=1 if card['sp'] else 0
        # 食料は無料で入る分があるので、費用は猫・道具(コインで買うもの)のみ。食料は別に数える
        out[g]=dict(p=succ/n,rew=rew/n,cost=d['cc']+d['ct'],food=d['food'],net=rew/n-(d['cc']+d['ct']),spec=sp/n)
    return out

def play4(design,G,stats,r,start_food=1,food_income=1,maxturn=60,lower_ok=True,hold_food=True):
    pats=make_patterns(design,r)
    coins=3; food=start_food; hc=[]; ht=[]; att={g:0 for g in design}
    def need(g):
        d=design[g]; return max(0,d['food']-food),max(0,d['cc']-len(hc)),max(0,d['ct']-len(ht))
    for turn in range(1,maxturn+1):
        coins+=1
        food+=food_income   # コインと同じく毎ターン食料1枚をもらう(ターン1も含む)
        choice=None
        if sum(need(G))<=coins: choice=G
        elif lower_ok:
            c=[]
            for g in design:
                if g>=G: continue
                nf,nc,nt=need(g)
                if nf+nc+nt>coins: continue
                if stats[g]['net']<=0: continue
                # 高いグレードのために食料をためたいので、低いグレードは食料を新たに買ってまでは行かない(買うなら差引が+1以上)
                if nf>0 and stats[g]['net']-nf<1: continue
                c.append((stats[g]['net']-nf,g))
            if c: choice=max(c)[1]
        if choice is None: continue
        g=choice; nf,nc,nt=need(g); d=design[g]
        coins-=nf+nc+nt; food+=nf
        for _ in range(nc): hc.append(draw_cat(r))
        for _ in range(nt): ht.append(draw_tool(r))
        cats=commit_pick(hc,d['cc']); tl=[t for t in ht if t==FLAG][:1]
        rest=[t for t in ht if t!=FLAG]; tools=tl+commit_pick(rest,max(0,d['ct']-len(tl)))
        food-=d['food']
        for c_ in cats: hc.remove(c_)
        for t in tools: ht.remove(t)
        card=r.choice(pats[g]); att[g]+=1
        if resolve(card,cats,tools):
            coins+=card['rw']
            if card['sp']: return turn,att
    return maxturn+1,att

def report4(design,n=4000,show_stats=True,**kw):
    stt=grade_stats4(design)
    if show_stats:
        for g,v in stt.items():
            print(f" g{g}: 食料{v['food']} 猫・道具{v['cost']} 成功率{v['p']:.0%} 平均報酬{v['rew']:.2f} 差引(猫道具のみ){v['net']:+.2f} 特別/回{v['spec']:.1%}")
    res={}
    for name,(G,low) in {'g4狙い(低は稼ぎ)':(4,True),'g4一直線':(4,False),'g3狙い(低は稼ぎ)':(3,True)}.items():
        r=random.Random(11); rr=[play4(design,G,stt,r,lower_ok=low,**kw) for _ in range(n)]
        ts=[x[0] for x in rr]
        def minN(k): return st.mean([min(ts[i:i+k]) for i in range(0,len(ts)-k+1,k)])
        att={g:st.mean([x[1][g] for x in rr]) for g in design}
        res[name]=(st.median(ts),minN(2),minN(3),minN(4))
        print(f"  {name:14s} 中央{st.median(ts):4.0f}T 平均{st.mean(ts):5.1f}T 到達{sum(t<=60 for t in ts)/n:4.0%} | 2人{minN(2):4.1f} 3人{minN(3):4.1f} 4人{minN(4):4.1f} | "+" ".join(f"g{g}:{a:.1f}" for g,a in att.items()))
    return res
