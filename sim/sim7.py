"""バランス試算 第7版(道具は冒険のほうび/冒険カード・道具カードは1回きり)
- 冒険カードは各グレード5枚(1種類1枚)。めくったカードはその人がもらい、山にもどらない。
- 冒険カードには「ほうびの道具」が1つ描いてあり(グレード4はなし)、めくると必ずもらえる。
- 道具は買えない。乗せた道具は使ったらなくなる(山にもどらない)。
- 猫の山は今までどおり(なくなったらまぜなおす)。食料・猫は1コインで買える。
- 終わり: だれかのコインが目標枚数になる、または冒険カードが全部なくなる(→コインが一番多い人の勝ち)。
プレイヤーの動き: 残っている冒険カードを見て、期待コイン(基本+ボーナス+道具の価値)-買い物の費用 が
いちばん大きい選び方をする(マイナスなら出航しない)。
道具: 0シャベル 1ロープ 2ランタン 3ぼうえんきょう 4きゅうきゅうばこ 5コンパス 6おうえんのはた
猫:   0おとぼけ 1わるだくみ 2にこにこ 3やるき 4ぼんやり 5きりり"""
import random, statistics as st, sys
FLAG = 6
GT = {1: [], 2: [0], 3: [1, 2], 4: [3, 4, 5]}
SHIP = {1: dict(food=1, xc=0, tl=0, base=2), 2: dict(food=2, xc=1, tl=1, base=3),
        3: dict(food=4, xc=2, tl=2, base=4), 4: dict(food=6, xc=3, tl=4, base=5)}
NONE = None
def C(cs, ca, ts, bonus, reward): return dict(cs=cs, ca=ca, ts=ts, bonus=bonus, reward=reward)
# prototype/index.html の CARDS と同じ内容
CARDS = {
 1: [C([], 0, [], 0, 0), C([], 0, [], 0, 0), C([], 0, [], 0, 0), C([], 0, [], 0, 1), C([], 0, [], 0, 2)],
 2: [C([], 2, [], 2, 1), C([], 2, [], 2, 2), C([], 1, [0], 3, 5), C([], 2, [], 3, 3), C([], 1, [0], 4, 4)],
 3: [C([], 2, [], 3, 4), C([], 2, [2], 4, 5), C([3], 1, [1], 4, 3), C([2], 1, [1], 5, FLAG), C([1], 1, [2], 6, FLAG)],
 4: [C([0], 2, [5], 5, NONE), C([5], 2, [4], 6, NONE), C([3], 2, [3], 6, NONE), C([5], 2, [3], 7, NONE), C([1], 2, [5], 8, NONE)],
}
TOOL_VALUE = 1.0   # 道具をもらうことの価値(コイン換算)。動きを決めるためだけに使う

def fits(t, g): return t == FLAG or t in GT[g]

def meets(c, cats, tools):
    if FLAG in tools: return True
    a = list(cats)
    for x in c['cs']:
        if x in a: a.remove(x)
        else: return False
    if len(a) < c['ca']: return False
    return all(x in tools for x in c['ts'])

def choose_tools(c_list, ht, g):
    """その船で使える道具のうち、残りのカードの条件に合うものを優先して乗せる(はたは最後の手段)"""
    usable = [t for t in ht if fits(t, g) and t != FLAG]
    need = [t for c in c_list for t in c['ts']]
    picked = []
    for t in sorted(set(usable), key=lambda t: -need.count(t)):
        if len(picked) < SHIP[g]['tl'] and need.count(t): picked.append(t)
    return picked

def plan(p, decks):
    best = None
    for g in range(1, 5):
        deck = decks[g]
        if not deck: continue
        sh = SHIP[g]
        mf = max(0, sh['food'] - p['food'])
        tools0 = choose_tools(deck, p['ht'], g)
        flag_opts = [False] + ([True] if FLAG in p['ht'] and sh['tl'] > len(tools0) and g >= 2 else [])
        for useflag in flag_opts:
            tools = tools0 + ([FLAG] if useflag else [])
            for ncat in range(1, 1 + sh['xc'] + 1):
                owned = p['hc'][:ncat]
                buy = max(0, ncat - len(p['hc']))
                cost = mf + buy
                if cost > p['coins']: continue
                cats = owned + [-1] * buy   # 買った猫は「なんでも」としてだけ数える
                ev = sum(sh['base'] + (c['bonus'] if meets(c, cats, tools) else 0)
                         + (TOOL_VALUE if c['reward'] is not None else 0) for c in deck) / len(deck)
                # はた・持っている道具を使うことの損(あとで使えたかもしれない)
                ev -= 1.5 * useflag + 0.3 * len(tools0)
                val = ev - cost
                if best is None or val > best[0]:
                    best = (val, g, ncat, buy, mf, tools)
    return best

def game(n, target, r, max_rounds=40):
    decks = {g: r.sample(CARDS[g], len(CARDS[g])) for g in CARDS}
    ps = [dict(coins=3, food=1, hc=[], ht=[], trips=0, used_tools=0, got_tools=0) for _ in range(n)]
    turns = 0
    for rnd in range(1, max_rounds + 1):
        for p in ps:
            turns += 1
            p['coins'] += 1; p['food'] += 1
            b = plan(p, decks)
            if b is None or b[0] <= 0: continue
            _, g, ncat, buy, mf, tools = b
            p['coins'] -= buy + mf; p['food'] += mf
            for _ in range(buy): p['hc'].append(r.randrange(6))
            cats = p['hc'][:ncat]; p['hc'] = p['hc'][ncat:]
            for t in tools: p['ht'].remove(t)
            p['used_tools'] += len(tools)
            p['food'] -= SHIP[g]['food']
            c = decks[g].pop()
            p['coins'] += SHIP[g]['base'] + (c['bonus'] if meets(c, cats, tools) else 0)
            if c['reward'] is not None: p['ht'].append(c['reward']); p['got_tools'] += 1
            p['trips'] += 1
            if p['coins'] >= target: return dict(end='goal', rounds=rnd, turns=turns, ps=ps)
            if not any(decks.values()): return dict(end='empty', rounds=rnd, turns=turns, ps=ps)
    return dict(end='cap', rounds=max_rounds, turns=turns, ps=ps)

def evaluate(n, target, games=3000, seed=7):
    r = random.Random(seed)
    rs = [game(n, target, r) for _ in range(games)]
    ends = {k: sum(x['end'] == k for x in rs) / games for k in ('goal', 'empty', 'cap')}
    turns = [x['turns'] for x in rs]
    rounds = [x['rounds'] for x in rs]
    used = st.mean(sum(p['used_tools'] for p in x['ps']) / max(1, sum(p['got_tools'] for p in x['ps'])) for x in rs)
    win = [max(p['coins'] for p in x['ps']) for x in rs]
    return dict(ends=ends, turns=st.mean(turns), rounds=st.mean(rounds), used=used, win=st.mean(win))

if __name__ == '__main__':
    for n in (2, 3, 4):
        for target in (20, 25, 30):
            e = evaluate(n, target)
            print(f'{n}人 目標{target}枚: 目標で決着{e["ends"]["goal"]:.0%} 山切れ{e["ends"]["empty"]:.0%} '
                  f'上限{e["ends"]["cap"]:.0%} | 平均{e["rounds"]:.1f}周(合計{e["turns"]:.1f}ターン) '
                  f'勝者のコイン{e["win"]:.1f} 道具の使用率{e["used"]:.0%}')
