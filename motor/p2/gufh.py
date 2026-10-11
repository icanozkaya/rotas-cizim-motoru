"""Yerden ısıtma bağlantı ayakları için genel kesişme-en-aza-indirme (tepe tırmanma) yardımcıları."""
import itertools, random
from shapely.geometry import LineString


def count_x(paths):
    gs = [LineString(p) for p in paths]
    n = 0
    for i in range(len(gs)):
        for j in range(i + 1, len(gs)):
            if gs[i].distance(gs[j]) > 0.4:
                continue
            it = gs[i].buffer(0.3).intersection(gs[j])
            if it.is_empty:
                continue
            parts = list(it.geoms) if hasattr(it, 'geoms') else [it]
            n += sum(10 if p.length > 2 else 1 for p in parts)
    return n


def optimize(circ, build, keys=('lane', 'hlane', 'pidx'), room_keys=('yslot', 'xslot'), iters=6, seed=1, restarts=0):
    if restarts:
        return _restarts(circ, build, keys, room_keys, iters, seed, restarts)
    """circ: devre dict listesi; build(): yol listesi döndürür. keys: devreler arası permütasyon alanları,
    room_keys: oda içi (parça) permütasyon alanları. Değişkenler yerinde güncellenir."""
    rnd = random.Random(seed)
    best = count_x(build())
    n = len(circ)
    for it in range(iters):
        improved = False
        # devreler arası takas
        for key in keys:
            for i in range(n):
                for j in range(i + 1, n):
                    a, b = circ[i], circ[j]
                    a[key], b[key] = b[key], a[key]
                    v = count_x(build())
                    if v < best:
                        best, improved = v, True
                    else:
                        a[key], b[key] = b[key], a[key]
                    if best == 0:
                        return 0
        # oda içi
        rooms = {}
        for c in circ:
            rooms.setdefault(c['room'], []).append(c)
        for rm, cs in rooms.items():
            if len(cs) < 2:
                continue
            for key in room_keys:
                vals = [c[key] for c in cs]
                for perm in itertools.permutations(vals):
                    for c, v_ in zip(cs, perm):
                        c[key] = v_
                    v = count_x(build())
                    if v < best:
                        best, improved = v, True
                        vals = list(perm)
                for c, v_ in zip(cs, vals):
                    c[key] = v_
        if not improved:
            break
    return best


def _restarts(circ, build, keys, room_keys, iters, seed, restarts):
    rnd = random.Random(seed)
    allk = list(keys) + list(room_keys)
    best_v = optimize(circ, build, keys, room_keys, iters, seed)
    best = [{k: c[k] for k in allk} for c in circ]
    for r in range(restarts):
        if best_v == 0:
            break
        for key in keys:
            vals = [c[key] for c in circ]
            rnd.shuffle(vals)
            for c, v in zip(circ, vals):
                c[key] = v
        v = optimize(circ, build, keys, room_keys, iters, seed)
        if v < best_v:
            best_v = v
            best = [{k: c[k] for k in allk} for c in circ]
    for c, b in zip(circ, best):
        c.update(b)
    return best_v
