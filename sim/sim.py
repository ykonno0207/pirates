import random, statistics as st
NC=6; NT=7; FLAG=6
TOOL_W=[1,1,1,1,1,1,0.5]
def draw_cat(r): return r.randrange(NC)
def draw_tool(r): return r.choices(range(NT),weights=TOOL_W)[0]

def make_patterns(design,r):
    # design[g]['patterns'] = list of (cs,ca,ts,ta,reward,special)
    out={}
    for g,d in design.items():
        ps=[]
        for (cs,ca,ts,ta,rw,sp) in d['patterns']:
            ps.append(dict(cats=r.sample(range(NC),cs),ca=ca,tools=r.sample(range(NT-1),ts),ta=ta,rw=rw,sp=sp))
        out[g]=ps
    return out

def commit_pick(hand,n,distinct_pref=True):
    # choose n from hand preferring distinct types
    seen=set(); first=[]; rest=[]
    for x in hand:
        if x not in seen: seen.add(x); first.append(x)
        else: rest.append(x)
    pick=(first+rest)[:n]
    return pick

def resolve(card,cats,tools):
    if FLAG in tools: return True
    cs=set(cats)
    for t in card['cats']:
        if t not in cs: return False
    spare=len(cats)-len(card['cats'])
    if spare<card['ca']: return False
    ts=set(tools)
    for t in card['tools']:
        if t not in ts: return False
    if len(tools)-len(card['tools'])<card['ta']: return False
    return True

def play(design,policy,r,maxturn=60):
    pats=make_patterns(design,r)
    coins=3; hc=[]; ht=[]; food=0
    for turn in range(1,maxturn+1):
        coins+=1
        # choose grade
        best=None
        for g in sorted(design,reverse=True):
            if not policy(g): continue
            d=design[g]
            need_f=max(0,d['food']-food)
            need_c=max(0,d['cc']-len(hc))
            need_t=max(0,d['ct']-len(ht))
            cost=need_f+need_c+need_t
            if coins>=cost+policy.margin(g) if hasattr(policy,'margin') else coins>=cost:
                best=(g,cost,need_f,need_c,need_t); break
        if not best: continue
        g,cost,nf,nc,nt=best
        coins-=cost; food+=nf
        for _ in range(nc): hc.append(draw_cat(r))
        for _ in range(nt): ht.append(draw_tool(r))
        d=design[g]
        cats=commit_pick(hc,d['cc']); 
        tl=[t for t in ht if t==FLAG][:1]
        rest=[t for t in ht if t!=FLAG]
        tools=tl+commit_pick(rest,max(0,d['ct']-len(tl)))
        food-=d['food']
        for c in cats: hc.remove(c)
        for t in tools: ht.remove(t)
        card=r.choice(pats[g])
        if resolve(card,cats,tools):
            coins+=card['rw'] if not isinstance(card['rw'],tuple) else r.randint(*card['rw'])
            if card['sp']: return turn,coins
    return maxturn+1,coins

class Pol:
    def __init__(s,grades,m=0): s.grades=set(grades); s.m=m
    def __call__(s,g): return g in s.grades
    def margin(s,g): return s.m

def run(design,n=4000,seed=1):
    res={}
    pols={'g1のみ':Pol([1]),'g2のみ':Pol([2]),'g3のみ':Pol([3]),'g4のみ':Pol([4]),'上から可能なもの':Pol([1,2,3,4]),'g1-g3':Pol([1,2,3])}
    for name,p in pols.items():
        r=random.Random(seed)
        ts=[play(design,p,r)[0] for _ in range(n)]
        res[name]=ts
    return res

def summarize(res,verbose=True):
    for name,ts in res.items():
        win=[t for t in ts if t<=60]
        # N人対戦での勝利ターン(最短)
        def minN(k):
            m=[min(ts[i:i+k]) for i in range(0,len(ts)-k+1,k)]
            return st.mean(m)
        print(f"{name:10s} 平均{st.mean(ts):5.1f}T 中央{st.median(ts):4.0f}T 到達率{len(win)/len(ts):.0%} 2人:{minN(2):4.1f} 4人:{minN(4):4.1f}")
