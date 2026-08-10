# Lambda CUDA environment

Mode A (recommended, mirrors the attached Lambda runbook): on the instance,

```bash
bash scripts/lambda_bootstrap.sh     # venv --system-site-packages, keeps
                                     # Lambda Stack torch; installs dci core
python scripts/cloud_doctor.py       # CUDA tier + frozen hardware class
```

Mode B (hermetic lock): `cd environments/cuda && uv sync` against the
pinned PyTorch CUDA index. Choose ONE mode per study and record it; the
environment identity (mode, image tag, `pip freeze` hash) enters run
provenance either way.

The per-GPU-hour prices, instance names and API shapes are the ones in
LAMBDA_CLOUD.md / the research guide (checked 2026-07/08); `lambda_cloud.py
instance-types` reads the live API before any launch, and a different GPU SKU
is a different hardware class, never a silent substitution.
