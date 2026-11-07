"""バランス試算 第10版(ねこ・どうぐは冒険のほうび/持っていれば条件達成)
sim9 から変えたところ:
- ねこ・どうぐは買えない。冒険カードのほうびでだけ手に入る。
  ・どうぐ:カードに描かれたもの(グレード1〜3)。
  ・ねこ:冒険カードをめくるたびに、ねこの山から1匹ランダムにもらう(山がなくなったらもらえない)。
    ねこの山はレア(やるき・わるだくみ)1匹ずつ、ほかは2匹ずつの計10匹。
- ねこ・どうぐは船に乗せない。冒険カードをめくったときに持っていれば、条件を満たす。使ってもなくならない。
  ・おうえんのはただけは、ほかでは条件が足りないときに自動で使い、なくなる。
- 出航に必要なのは食料だけ(猫1匹の必須もなし)。食料が足りなければ、1コインで1こ自動で買う。
- 船はグレードアップ式(sim9 と同じ)。今のグレードの山がなければ下の山からめくる。
猫: 0おとぼけ 1わるだくみ 2にこにこ 3やるき 4ぼんやり 5きりり"""
import random, statistics as st, sys
from sim7 import FLAG
from sim9 import CARDS

FOOD = {1: 1, 2: 2, 3: 3, 4: 4}
BASE = {1: 2, 2: 3, 3: 4, 4: 5}
RARE = (1, 3)

def meets(c, cats, tools):
    a = list(cats)
    for x in c['cs']:
        if x in a: a.remove(x)
        else: return False
    if len(cats) < len(c['cs']) + c['ca']: return False
    return all(t in tools for t in c['ts'])

def game(pols, cost, target, r, food=FOOD, max_rounds=40):
    decks = {g: r.sample(CARDS[g], len(CARDS[g])) for g in CARDS}
    catdeck = [c for c in range(6) for _ in range(1 if c in RARE else 2)]; r.shuffle(catdeck)
    ps = [dict(coins=3, food=1, cats=[], tools=[], L=1, maxL=m, trips=0) for m in pols]
    turns = 0
    for rnd in range(1, max_rounds + 1):
        for i, p in enumerate(ps):
            turns += 1
            p['coins'] += 1; p['food'] += 1
            while p['L'] < 4:
                stuck = not any(decks[g] for g in range(1, p['L'] + 1))
                c = cost[p['L'] + 1]
                if (p['L'] < p['maxL'] or stuck) and p['coins'] >= c and any(decks[g] for g in range(p['L'] + 1, 5)):
                    p['coins'] -= c; p['L'] += 1
                else: break
            ge = next((g for g in range(p['L'], 0, -1) if decks[g]), None)
            if ge is None: continue
            need = max(0, food[p['L']] - p['food'])
            if need > p['coins'] or need >= BASE[p['L']]: continue   # 買ってまで行くと損なら見送る
            p['coins'] -= need; p['food'] += need - food[p['L']]
            card = decks[ge].pop()
            ok = card['bonus'] > 0 and meets(card, p['cats'], p['tools'])
            if card['bonus'] > 0 and not ok and FLAG in p['tools']:
                p['tools'].remove(FLAG); ok = True
            p['coins'] += BASE[p['L']] + (card['bonus'] if ok else 0)
            if card['reward'] is not None: p['tools'].append(card['reward'])
            if catdeck: p['cats'].append(catdeck.pop())
            p['trips'] += 1
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

def length(pol, n, cost, target, games, r, **kw):
    rs = [game([pol] * n, cost, target, r, **kw) for _ in range(games)]
    bon = []
    return st.mean(x['turns'] for x in rs), sum(x['end'] == 'goal' for x in rs) / games

if __name__ == '__main__':
    for cost in [(2, 4, 6), (3, 5, 7), (2, 3, 4)]:
        r = random.Random(5); c = {2: cost[0], 3: cost[1], 4: cost[2]}
        avg = wr_table(c, 20, 800, r)
        best = max(avg, key=avg.get)
        lens = ' '.join(f'{n}人{g}枚:{length(best, n, c, g, 500, r)[0]:.1f}T({length(best, n, c, g, 300, r)[1]:.0%})'
                        for n, g in ((2, 20), (2, 25), (3, 15), (3, 20), (4, 15)))
        print(f'値段 G2={cost[0]} G3={cost[1]} G4={cost[2]} | ' + ' '.join(f'〜G{a}:{avg[a]:.0%}' for a in range(1, 5)) + f' | 最強〜G{best}: {lens}')
        sys.stdout.flush()
