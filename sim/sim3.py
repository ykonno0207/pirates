import random, statistics as st
from sim import make_patterns, commit_pick, resolve, draw_cat, draw_tool, FLAG
from sim2 import grade_stats

def play3(design,G,stats,r,maxturn=60,lower_ok=True):
    pats=make_patterns(design,r)
    coins=3; hc=[]; ht=[]; food=0; att={g:0 for g in design}; succ={g:0 for g in design}; fails4=0
    def cost_of(g):
        d=design[g]; return max(0,d['food']-food),max(0,d['cc']-len(hc)),max(0,d['ct']-len(ht))
    for turn in range(1,maxturn+1):
        coins+=1; choice=None
        if sum(cost_of(G))<=coins: choice=G
        elif lower_ok:
            c=[(stats[g]['net'],g) for g in design if g<G and sum(cost_of(g))<=coins and stats[g]['net']>0]
            if c: choice=max(c)[1]
        if choice is None: continue
        g=choice; nf,nc,nt=cost_of(g); d=design[g]
        coins-=nf+nc+nt; food+=nf
        for _ in range(nc): hc.append(draw_cat(r))
        for _ in range(nt): ht.append(draw_tool(r))
        cats=commit_pick(hc,d['cc']); tl=[t for t in ht if t==FLAG][:1]
        rest=[t for t in ht if t!=FLAG]; tools=tl+commit_pick(rest,max(0,d['ct']-len(tl)))
        food-=d['food']
        for c in cats: hc.remove(c)
        for t in tools: ht.remove(t)
        card=r.choice(pats[g]); att[g]+=1
        if resolve(card,cats,tools):
            succ[g]+=1; coins+=card['rw']
            if card['sp']: return turn,att,succ
    return maxturn+1,att,succ

def report3(design,n=4000):
    stt=grade_stats(design)
    for g,v in stt.items():
        print(f" g{g}: 費用{v['cost']} 成功率{v['p']:.0%} 平均報酬{v['rew']:.2f} 差引{v['net']:+.2f} 特別財宝/回{v['spec']:.1%}")
    for name,(G,low) in {'g4狙い(低は稼ぎ)':(4,True),'g4一直線':(4,False),'g3狙い(低は稼ぎ)':(3,True)}.items():
        r=random.Random(11); res=[play3(design,G,stt,r,lower_ok=low) for _ in range(n)]
        ts=[x[0] for x in res]
        def minN(k): return st.mean([min(ts[i:i+k]) for i in range(0,len(ts)-k+1,k)])
        att={g:st.mean([x[1][g] for x in res]) for g in design}
        print(f"  {name:14s} 中央{st.median(ts):4.0f}T 平均{st.mean(ts):5.1f}T 到達{sum(t<=60 for t in ts)/n:4.0%} | 2人{minN(2):4.1f} 3人{minN(3):4.1f} 4人{minN(4):4.1f} | 出航回数 "+" ".join(f"g{g}:{a:.1f}" for g,a in att.items()))
