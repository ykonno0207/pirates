"""バランス試算 第11版(最初のコイン0/低いグレードでは ねこ・どうぐが 手に入りにくい)
sim10 から変えたところ:
- 最初のコインは0枚(食料1こはそのまま)。
- ねこは「ねこの印がある冒険カード」をめくったときだけ、山からランダムに1匹もらう(山は計10匹)。
  印の数:グレード1=1枚、2=2枚、3=3枚、4=4枚(案A)。
- どうぐのほうび:グレード1は2枚だけ(シャベル2)。グレード2・3は全部のカードにある。グレード4はなし。
  おうえんのはたは1枚(バミューダ)。
道具: 0シャベル 1ロープ 2ランタン 3ぼうえんきょう 4きゅうきゅうばこ 5コンパス 6おうえんのはた"""
import random, statistics as st, sys
import sim10
from sim10 import FOOD, BASE, RARE, meets
from sim7 import FLAG
from sim9 import CARDS as BASECARDS

TOOLS = {1: [0, 0, None, None, None], 2: [1, 2, 1, 2, 5], 3: [4, 5, 3, 3, FLAG], 4: [None] * 5}
CATMARK = {'A': {1: [0, 0, 1, 0, 0], 2: [1, 0, 0, 1, 0], 3: [1, 1, 0, 1, 0], 4: [1, 1, 1, 1, 0]},
           'B': {1: [1, 0, 1, 0, 0], 2: [1, 0, 0, 1, 0], 3: [1, 1, 0, 1, 0], 4: [1, 1, 1, 0, 0]},
           'old': {g: [1] * 5 for g in (1, 2, 3, 4)}}

def cards(mark):
    out = {}
    for g in (1, 2, 3, 4):
        out[g] = [dict(c, reward=TOOLS[g][k], cat=CATMARK[mark][g][k]) for k, c in enumerate(BASECARDS[g])]
    return out

def game(pols, cost, target, r, mark='A', start=0, max_rounds=40):
    C = cards(mark)
    decks = {g: r.sample(C[g], 5) for g in C}
    catdeck = [c for c in range(6) for _ in range(1 if c in RARE else 2)]; r.shuffle(catdeck)
    ps = [dict(coins=start, food=1, cats=[], tools=[], L=1, maxL=m) for m in pols]
    turns = 0
    for rnd in range(1, max_rounds + 1):
        for i, p in enumerate(ps):
            turns += 1; p['coins'] += 1; p['food'] += 1
            while p['L'] < 4:
                stuck = not any(decks[g] for g in range(1, p['L'] + 1))
                c = cost[p['L'] + 1]
                if (p['L'] < p['maxL'] or stuck) and p['coins'] >= c and any(decks[g] for g in range(p['L'] + 1, 5)):
                    p['coins'] -= c; p['L'] += 1
                else: break
            ge = next((g for g in range(p['L'], 0, -1) if decks[g]), None)
            if ge is None: continue
            need = max(0, FOOD[p['L']] - p['food'])
            if need > p['coins'] or need >= BASE[p['L']]: continue
            p['coins'] -= need; p['food'] += need - FOOD[p['L']]
            card = decks[ge].pop()
            ok = card['bonus'] > 0 and meets(card, p['cats'], p['tools'])
            if card['bonus'] > 0 and not ok and FLAG in p['tools']: p['tools'].remove(FLAG); ok = True
            p['coins'] += BASE[p['L']] + (card['bonus'] if ok else 0)
            p.setdefault('bon', []).append(ok)
            if card['reward'] is not None: p['tools'].append(card['reward'])
            if card['cat'] and catdeck: p['cats'].append(catdeck.pop())
            if p['coins'] >= target: return dict(end='goal', winner=[i], turns=turns, ps=ps)
            if not any(decks.values()):
                top = max(x['coins'] for x in ps)
                return dict(end='empty', winner=[j for j, x in enumerate(ps) if x['coins'] == top], turns=turns, ps=ps)
    top = max(x['coins'] for x in ps)
    return dict(end='cap', winner=[j for j, x in enumerate(ps) if x['coins'] == top], turns=turns, ps=ps)

def wr_table(cost, target, games, r, **kw):
    m = {}
    for a in range(1, 5):
        for b in range(a + 1, 5):
            w = 0
            for k in range(games):
                pols = [a, b] if k % 2 == 0 else [b, a]; me = k % 2
                g = game(pols, cost, target, r, **kw)
                if me in g['winner']: w += 1 / len(g['winner'])
            m[(a, b)] = w / games
    wr = lambda a, b: 0.5 if a == b else (m[(a, b)] if a < b else 1 - m[(b, a)])
    return {a: st.mean(wr(a, b) for b in range(1, 5)) for a in range(1, 5)}

def stats(pol, n, cost, target, games, r, **kw):
    rs = [game([pol] * n, cost, target, r, **kw) for _ in range(games)]
    bon = [b for x in rs for p in x['ps'] for b in p.get('bon', [])]
    return st.mean(x['turns'] for x in rs), sum(x['end'] == 'goal' for x in rs) / games, sum(bon) / max(1, len(bon))

if __name__ == '__main__':
    cost = {2: 2, 3: 4, 4: 6}
    for mark, start in (('old', 3), ('old', 0), ('A', 0), ('B', 0)):
        r = random.Random(5)
        avg = wr_table(cost, 20, 500, r, mark=mark, start=start)
        best = max(avg, key=avg.get)
        out = []
        for n, g in ((2, 20), (2, 25), (3, 15), (3, 20), (4, 15)):
            t, gl, b = stats(best, n, cost, g, 400, r, mark=mark, start=start)
            out.append(f'{n}人{g}枚:{t:.1f}T({gl:.0%})')
        b = stats(best, 2, cost, 25, 400, r, mark=mark, start=start)[2]
        print(f'ねこの印{mark} 最初のコイン{start} | ' + ' '.join(f'〜G{a}:{avg[a]:.0%}' for a in range(1, 5)) + f' | ボーナス率{b:.0%} | ' + ' '.join(out))
        sys.stdout.flush()
