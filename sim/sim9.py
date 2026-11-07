"""バランス試算 第9版(船はグレードアップ/いつも いちばん新しい船で出航/レアねこ)
sim8 から変えたところ:
- 船は「グレードアップ」。持っている一番高いグレードの船でしか出航できない(低い船は選べない)。
- いまのグレードの冒険カードがなくなったら、下のグレードで残っている一番高い山からめくる
  (食料・基本コインは自分の船のグレードのまま。ボーナスの条件とほうびはめくったカードのもの)。
- 猫の山: ふつうの猫 8枚ずつ、レアの猫(やるきねこ・わるだくみねこ)は RARE 枚ずつ。
- 指定の猫の入れかえ:レアの猫を、ボーナスの大きいカードに。
  マチュピチュ=にこにこ、イースター島=やるき、グランドキャニオン=ぼんやり、サハラ砂漠=やるき。
猫: 0おとぼけ 1わるだくみ 2にこにこ 3やるき 4ぼんやり 5きりり"""
import random, statistics as st, sys
import sim7
from sim7 import SHIP, meets, FLAG, NONE, C

CARDS = {
 1: sim7.CARDS[1],
 2: sim7.CARDS[2],
 3: [C([], 2, [], 3, 4), C([], 2, [2], 4, 5), C([2], 1, [1], 4, 3), C([3], 1, [1], 5, FLAG), C([1], 1, [2], 6, FLAG)],
 4: [C([0], 2, [5], 5, NONE), C([5], 2, [4], 6, NONE), C([4], 2, [3], 6, NONE), C([3], 2, [3], 7, NONE), C([1], 2, [5], 8, NONE)],
}
RARE_IDS = (1, 3)

def cat_deck(r, rare):
    d = [c for c in range(6) for _ in range(rare if c in RARE_IDS else 8)]
    r.shuffle(d); return d

def game(pols, cost, target, r, rare=3, max_rounds=40):
    decks = {g: r.sample(CARDS[g], len(CARDS[g])) for g in CARDS}
    cats = cat_deck(r, rare)
    ps = [dict(coins=3, food=1, hc=[], ht=[], L=1, maxL=m, trips=0, bt={}) for m in pols]
    turns = 0
    for rnd in range(1, max_rounds + 1):
        for i, p in enumerate(ps):
            turns += 1
            p['coins'] += 1; p['food'] += 1
            while p['L'] < 4:
                stuck = not any(decks[g] for g in range(1, p['L'] + 1))
                want = p['L'] < p['maxL'] or stuck
                c = cost[p['L'] + 1]
                if want and p['coins'] >= c and any(decks[g] for g in range(p['L'] + 1, 5)):
                    p['coins'] -= c; p['L'] += 1; p['bt'][p['L']] = rnd
                else: break
            ge = next((g for g in range(p['L'], 0, -1) if decks[g]), None)
            if ge is None: continue
            vis = {g: (decks[ge] if g == p['L'] else []) for g in decks}
            b = sim7.plan(p, vis)
            if b is None or b[0] <= 0: continue
            _, g, ncat, buy, mf, tools = b
            p['coins'] -= buy + mf; p['food'] += mf
            for _ in range(buy):
                if not cats: cats = cat_deck(r, rare)
                p['hc'].append(cats.pop())
            on = p['hc'][:ncat]; p['hc'] = p['hc'][ncat:]
            for t in tools: p['ht'].remove(t)
            p['food'] -= SHIP[g]['food']
            card = decks[ge].pop()
            p['coins'] += SHIP[g]['base'] + (card['bonus'] if meets(card, on, tools) else 0)
            if card['reward'] is not None: p['ht'].append(card['reward'])
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
    return st.mean(x['turns'] for x in rs), sum(x['end'] == 'goal' for x in rs) / games

if __name__ == '__main__':
    target = 20
    # 採用した食料(1・2・3・4)。prototype/index.html の SHIPS と同じ
    for g, f in zip((1, 2, 3, 4), (1, 2, 3, 4)): SHIP[g]['food'] = f
    for cost in [(2, 3, 4), (2, 4, 6), (3, 5, 7)]:
        r = random.Random(5); c = {2: cost[0], 3: cost[1], 4: cost[2]}
        avg = wr_table(c, target, 800, r)
        best = max(avg, key=avg.get)
        lens = ' '.join(f'{n}人{g}枚:{length(best, n, c, g, 400, r)[0]:.1f}T' for n, g in ((2, 20), (3, 15), (4, 15)))
        print(f'G2={cost[0]} G3={cost[1]} G4={cost[2]} | ' + ' '.join(f'〜G{a}:{avg[a]:.0%}' for a in range(1, 5)) + f' | 最強〜G{best}: {lens}')
        sys.stdout.flush()
