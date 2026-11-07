"""バランス試算 第8版(船は買って育てる)
sim7 のルールに加えて:
- 最初はみんなグレード1の船だけを持っている。
- コインで1つ上のグレードの船を買える(1回に1つずつ。買った船はずっと使える)。
- 持っている船のグレード以下なら、どの船でも出航できる(低い船なら食料が少なくてすむ)。
- 勝ちは今までどおり、手元のコインが目標枚数になった人(船を買うとコインが減る)。

プレイヤーの動き(方針): 「グレード maxL まで、買えるようになったらすぐ買う」。
いま持っている船で行ける山が全部なくなったら、maxL に関係なく上の船を買う。
出航のしかたは sim7 と同じ(期待コインが一番大きい選び方)。"""
import random, statistics as st, itertools, sys
import sim7
from sim7 import SHIP, CARDS, meets

def plan(p, decks):
    vis = {g: (decks[g] if g <= p['L'] else []) for g in decks}
    return sim7.plan(p, vis)

def game(pols, cost, target, r, max_rounds=40):
    decks = {g: r.sample(CARDS[g], len(CARDS[g])) for g in CARDS}
    ps = [dict(coins=3, food=1, hc=[], ht=[], L=1, maxL=m, trips=0, buy_turn={}) for m in pols]
    turns = 0
    for rnd in range(1, max_rounds + 1):
        for i, p in enumerate(ps):
            turns += 1
            p['coins'] += 1; p['food'] += 1
            # 船を買う
            while p['L'] < 4:
                stuck = not any(decks[g] for g in range(1, p['L'] + 1))
                want = p['L'] < p['maxL'] or stuck
                c = cost[p['L'] + 1]
                if want and p['coins'] >= c and decks_any_above(decks, p['L']):
                    p['coins'] -= c; p['L'] += 1; p['buy_turn'][p['L']] = rnd
                else: break
            b = plan(p, decks)
            if b is None or b[0] <= 0: continue
            _, g, ncat, buy, mf, tools = b
            p['coins'] -= buy + mf; p['food'] += mf
            for _ in range(buy): p['hc'].append(r.randrange(6))
            cats = p['hc'][:ncat]; p['hc'] = p['hc'][ncat:]
            for t in tools: p['ht'].remove(t)
            p['food'] -= SHIP[g]['food']
            card = decks[g].pop()
            p['coins'] += SHIP[g]['base'] + (card['bonus'] if meets(card, cats, tools) else 0)
            if card['reward'] is not None: p['ht'].append(card['reward'])
            p['trips'] += 1
            if p['coins'] >= target: return dict(end='goal', winner=[i], rounds=rnd, turns=turns, ps=ps)
            if not any(decks.values()):
                top = max(x['coins'] for x in ps)
                return dict(end='empty', winner=[j for j, x in enumerate(ps) if x['coins'] == top], rounds=rnd, turns=turns, ps=ps)
    top = max(x['coins'] for x in ps)
    return dict(end='cap', winner=[j for j, x in enumerate(ps) if x['coins'] == top], rounds=max_rounds, turns=turns, ps=ps)

def decks_any_above(decks, L): return any(decks[g] for g in range(L + 1, 5))

def winrate(a, b, cost, target, games, r):
    """方針 a の人が 方針 b の人に勝つ割合(席は交互)。引き分けは0.5"""
    w = 0
    for k in range(games):
        pols = [a, b] if k % 2 == 0 else [b, a]
        me = 0 if k % 2 == 0 else 1
        g = game(pols, cost, target, r)
        if me in g['winner']: w += 1 / len(g['winner'])
    return w / games

def length(pol, n, cost, target, games, r):
    rs = [game([pol] * n, cost, target, r) for _ in range(games)]
    return (st.mean(x['turns'] for x in rs), sum(x['end'] == 'goal' for x in rs) / games,
            {L: st.mean([x['ps'][0]['buy_turn'].get(L, 99) for x in rs]) for L in (2, 3, 4)})

def survey(costs, target=25, games=1500, seed=5):
    for cost in costs:
        r = random.Random(seed)
        c = {2: cost[0], 3: cost[1], 4: cost[2]}
        m = {(a, b): winrate(a, b, c, target, games, r) for a in range(1, 5) for b in range(1, 5) if a < b}
        def wr(a, b): return 0.5 if a == b else (m[(a, b)] if a < b else 1 - m[(b, a)])
        avg = {a: st.mean(wr(a, b) for b in range(1, 5)) for a in range(1, 5)}
        best = max(avg, key=avg.get)
        t2, g2, bt = length(best, 2, c, target, games // 2, r)
        print(f'船の値段 G2={cost[0]} G3={cost[1]} G4={cost[2]} | 方針ごとの平均勝率 '
              + ' '.join(f'〜G{a}:{avg[a]:.0%}' for a in range(1, 5))
              + f' | 3対4 {wr(3, 4):.0%} 2対3 {wr(2, 3):.0%} | 最強〜G{best}同士の2人戦 合計{t2:.1f}ターン')
        sys.stdout.flush()

if __name__ == '__main__':
    survey([(2, 4, 6), (3, 5, 7), (3, 6, 9), (4, 6, 8), (4, 7, 10), (5, 8, 12), (3, 5, 8), (2, 5, 8)])
