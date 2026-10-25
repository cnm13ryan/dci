"""Posterior 'infinite-precision' coverage for the current library, from the
pilot's stored counts. Independent re-implementation of D09/D10/D11/D08 rules
(scratch analysis; validated against the stored verdict with point estimates)."""
import json, sys
import numpy as np
R = sys.argv[1]; DCI = sys.argv[2]
A_CID = sys.argv[3] if len(sys.argv) > 3 else "A.however.6"
TOL = float(sys.argv[4]) if len(sys.argv) > 4 else 0.10
S = int(sys.argv[5]) if len(sys.argv) > 5 else 4000
c = json.load(open(f"{R}/calibration.json"))
man = json.load(open(f"{DCI}/docs/batch1/library_manifest.json"))
compat = json.load(open(f"{DCI}/docs/batch1/compatibility_matrix.json"))["compatible_by_limit"]
refs = [r for r in man["references"]]
info = {r["cid"]: r for r in refs}
MF = sorted(c["eligibility"][refs[0]["cid"]]["cells"])
models = sorted({k.split("|")[0] for k in MF})
B = [8, 10]
K = np.array([[c["eligibility"][r["cid"]]["cells"][mf]["k"] for mf in MF] for r in refs])
N = np.array([[c["eligibility"][r["cid"]]["cells"][mf]["n"] for mf in MF] for r in refs])
arank = next(x for x in c["a"]["ranking"] if x["a"] == A_CID)["cells"]
NA = np.array([arank[mf]["n"] for mf in MF]); KA = np.rint(np.array([arank[mf]["p"] for mf in MF]) * NA).astype(int)
word = [r["params"].get("word") if r["family_id"] == "exact_word_count" else None for r in refs]
same = np.array([r["operation"] == "exact_count" and r["object_type"] == "word" for r in refs])
oobj = np.array([r["operation"] == "exact_count" and r["object_type"] != "word" for r in refs])
oop = np.array([r["operation"] != "exact_count" for r in refs])
comp = {b: np.array([r["cid"] in set(compat[str(b)]) for r in refs]) for b in B}
words = sorted({w for w in word if w}); W = np.array([[w == x for x in word] for w in words])  # words x refs

def verdict(th, ta):
    elig = (th >= 0.2).any(axis=1)                         # D09: >= 20% in any model-frame
    sup = {p: [] for p in ("P1", "P2", "P3")}
    for j, mf in enumerate(MF):
        m = mf.split("|")[0]
        ainf = 0.10 <= ta[j] <= 0.90                       # D08 headroom band
        matched = np.abs(th[:, j] - ta[j]) <= TOL + 1e-12  # D10
        for b in B:
            pool = elig & comp[b]
            g1 = pool & same & matched; g2 = pool & same
            g3 = pool & (same | oobj) & matched; g5 = pool & matched
            nwords = int((W[:, g1].any(axis=1)).sum())
            g1ok = nwords >= 3
            p1 = g1ok and int((g2 & ~g1).sum()) >= 2
            p2 = g1ok and int((g3 & ~g1 & oobj).sum()) >= 2
            p3 = int(g3.sum()) >= 3 and int((g5 & ~g3 & oop).sum()) >= 3
            for name, ok in (("P1", p1), ("P2", p2), ("P3", p3)):
                if ok and ainf: sup[name].append((m, b))
    out = {}
    for name, lst in sup.items():
        out[name] = (len(lst), len(lst) >= 12 and len({x[0] for x in lst}) >= 3 and sorted({x[1] for x in lst}) == B)
    return out

point = verdict(K / N, KA / NA)
print("point estimates:", {k: v[0] for k, v in point.items()}, "feasible:", {k: v[1] for k, v in point.items()})
rng = np.random.default_rng(20261025)
counts = {p: [] for p in ("P1", "P2", "P3")}; feas = {p: 0 for p in counts}; allf = 0
for s in range(S):
    th = rng.beta(K + 1, N - K + 1); ta = rng.beta(KA + 1, NA - KA + 1)
    v = verdict(th, ta)
    for p in counts:
        counts[p].append(v[p][0]); feas[p] += v[p][1]
    allf += all(v[p][1] for p in counts)
for p in counts:
    a = np.array(counts[p])
    print(f"{p}: true-coverage posterior mean {a.mean():.1f}/16, 90% interval [{np.percentile(a,5):.0f}, {np.percentile(a,95):.0f}], P(feasible) {feas[p]/S:.3f}")
print(f"P(all three feasible) {allf/S:.3f}   [A={A_CID}, tolerance={TOL}, draws={S}]")
