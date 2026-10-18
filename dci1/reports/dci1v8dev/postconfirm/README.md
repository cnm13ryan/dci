# v8.1 post-confirmatory result tables

Everything under `data/` is copied from the **signed** confirmatory records
of the root `dci1/evidence/dci1v8p1-confirm`, bound to commit
`034fc7214762b6848d5d904b14fd82b317830667` under the preregistration hashed
`d3552f9f47e3f00800622f033cfad579dcd6085b1068f0bcb35c643e8bb1908d`. No file
here decides anything; each is a projection of
`<root>/durable/dci1v8/<model>/CONFIRMATORY_ANALYSIS/confirmatory_analysis.json`
into a shape a figure or a table can read.

Regenerate with:

```
python3 tools/v8_postconfirm_extract.py \
    --root evidence/dci1v8p1-confirm --out reports/dci1v8dev/postconfirm/data
python3 tools/v8_postconfirm_spectrum_points.py \
    --root evidence/dci1v8p1-confirm \
    --out reports/dci1v8dev/postconfirm/data/spectrum_points.csv
```

The second tool re-forms the registered spectrum fit's own input with the
frozen functions and **asserts** that it recovers the recorded slope,
prediction, δ_difficulty and every per-point residual to 1e-9; it fails
closed if it does not.

Every magnitude is in **percentage points**. `iota`, `difficulty_iota` and
`slope` are on the 0–1 scale. The decision interval on a primary claim is
the **joint** cross-frame simultaneous interval (`joint_lower_pp`,
`joint_upper_pp`); `within_frame_*` is the per-frame F1 interval and
`marginal_*` carries no multiplicity correction — do not substitute either
for the joint one.

`methodology_validation_final.csv` is the only file here not derived from a
confirmatory record: it digests
`reports/dci1v8dev/frame_aware_prescreen/prescreen_revalidation.md`, which is
**pre-freeze identification evidence**, and each row names its source
section.

Interpretation, registered readings, sensitivities and the manuscript
rewrite map: `manuscript/V8_1_POSTCONFIRM_PAPER_REWRITE_BUNDLE.md` in the repository
root.
