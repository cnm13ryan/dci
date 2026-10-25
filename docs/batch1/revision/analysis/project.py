"""Projection (HYPOTHESIS, not evidence): coverage under an expanded library
whose new references behave like resampled existing ones.

Assumptions, stated in the proposal:
- a new reference's 8-cell difficulty profile is exchangeable with an
  existing reference of the same group (whole profiles are resampled, so
  correlations across models and frames are kept); 'graded' pools exclude
  profiles at floor (<0.10) or ceiling (>0.95) in every model-frame;
- new target words are short enough for both B limits (<= 8 letters), so
  every synthetic word is B-compatible; their count ladders are resampled
  whole from the existing B-compatible words;
- profiles are drawn from the posterior (Beta(k+1, n-k+1)) of the pilot cells;
- 'measured at n' adds binomial noise at n per cell for references and A.
"""
import json, sys
import numpy as np
R, DCI = sys.argv[1], sys.argv[2]
c = json.load(open(f"{R}/calibration.json"))
man = json.load(open(f"{DCI}/docs/batch1/library_manifest.json"))
refs = man["references"]; e = c["eligibility"]
MF = sorted(e[refs[0]["cid"]]["cells"]); models = [k.split("|")[0] for k in MF]
A = next(x for x in c["a"]["ranking"] if x["a"] == "A.however.6")["cells"]
KA = np.array([round(A[m]["p"] * A[m]["n"]) for m in MF]); NA = np.array([A[m]["n"] for m in MF])
def kn(cid): return (np.array([e[cid]["cells"][m]["k"] for m in MF]), np.array([e[cid]["cells"][m]["n"] for m in MF]))
short = {"indeed", "instead", "perhaps", "although", "moreover"}  # <= 8 letters
ladders = {w: [r["cid"] for r in refs if r["params"].get("word") == w] for w in short}
oobj = [r["cid"] for r in refs if r["operation"] == "exact_count" and r["object_type"] != "word"]
oop = [r["cid"] for r in refs if r["operation"] != "exact_count"]
def graded(cids):
    out = []
    for cid in cids:
        k, n = kn(cid); p = k / n
        if not ((p < 0.10).all() or (p > 0.95).all()): out.append(cid)
    return out
pools = {"all": (oobj, oop), "graded": (graded(oobj), graded(oop))}
rng = np.random.default_rng(1)
def draw(cid):
    k, n = kn(cid); return rng.beta(k + 1, n - k + 1)
def run(W, Mobj, Mop, pool, n_meas, S=600, tol=0.10):
    po, pp = pools[pool]; ok = {"P1": 0, "P2": 0, "P3": 0}; allok = 0; cover = {p: [] for p in ok}
    for _ in range(S):
        ta = rng.beta(KA + 1, NA - KA + 1)
        words = [[draw(cid) for cid in ladders[rng.choice(sorted(short))]] for _ in range(W)]
        objs = [draw(rng.choice(po)) for _ in range(Mobj)]
        ops = [draw(rng.choice(pp)) for _ in range(Mop)]
        if n_meas:
            meas = lambda th: rng.binomial(n_meas, th) / n_meas
            ta_m = meas(ta); words = [[meas(t) for t in wl] for wl in words]; objs = [meas(t) for t in objs]; ops = [meas(t) for t in ops]
        else:
            ta_m = ta
        sup = {p: [] for p in ok}
        for j, m in enumerate(MF):
            if not (0.10 <= ta_m[j] <= 0.90): continue
            elig = lambda prof: (prof >= 0.2).any()
            mt = lambda prof: abs(prof[j] - ta_m[j]) <= tol
            wm = [any(mt(t) for t in wl if elig(t)) for wl in words]
            g1 = sum(sum(1 for t in wl if elig(t) and mt(t)) for wl in words)
            g2 = sum(sum(1 for t in wl if elig(t)) for wl in words)
            om = sum(1 for t in objs if elig(t) and mt(t)); pm = sum(1 for t in ops if elig(t) and mt(t))
            g1ok = sum(wm) >= 3
            p1 = g1ok and g2 - g1 >= 2; p2 = g1ok and om >= 2; p3 = (g1 + om) >= 3 and pm >= 3
            for name, v in (("P1", p1), ("P2", p2), ("P3", p3)):
                if v: sup[name] += [(m, 8), (m, 10)]  # synthetic words are compatible with both limits
        good = True
        for name in ok:
            lst = sup[name]; f = len(lst) >= 12 and len({x[0] for x in lst}) >= 3
            ok[name] += f; good &= f; cover[name].append(len(lst))
        allok += good
    return {k: v / S for k, v in ok.items()}, allok / S, {k: float(np.mean(v)) for k, v in cover.items()}
print("W words (3 counts each, <=8 letters) | other-object refs | other-op refs | pool | measured at n | P(P1,P2,P3 feasible) | P(all) | mean coverage")
for W, Mo, Mp in ((5, 8, 21), (8, 12, 24), (10, 16, 30), (12, 20, 36), (15, 24, 40)):
    for pool in ("all", "graded"):
        for n in (0, 96, 192):
            f, a, cv = run(W, Mo, Mp, pool, n)
            print(f"{W:2} | {Mo:2} | {Mp:2} | {pool:6} | {n or 'exact':5} | " + ", ".join(f"{k} {v:.2f}" for k, v in f.items()) + f" | {a:.2f} | " + ", ".join(f"{k} {v:.1f}" for k, v in cv.items()))
