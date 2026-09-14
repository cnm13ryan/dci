"""Fixtures for the v8 development-candidate suite. Fixture data only."""
from __future__ import annotations

import gzip
import hashlib
import json
import os
from collections.abc import Sequence
from pathlib import Path

import pytest

from dci1v7.protocol import constants as C
from dci1v7.stages.calibration_table import CalibrationRow
from dci1v7.stages.interaction import KappaUnderBSource
from dci1v8dev.prescreen.schema import ARung, PrescreenRung

FIXTURE_MODEL = "fixture-model"
FIXTURE_M_STAR = 9

#: The stored evidence root, when the suite runs where one exists. Every
#: evidence-dependent test skips otherwise (the tree is gitignored).
EVIDENCE = Path(os.environ.get(
    "DCI1_EVIDENCE_ROOT",
    str(Path(__file__).resolve().parents[1] / "evidence")))


def kappa_source(candidate: str, *, m_star: int = FIXTURE_M_STAR,
                 split: str = "pooled", n_topics: int = C.N_CALIBRATION,
                 n_draws: int = C.M_CAL) -> KappaUnderBSource:
    return KappaUnderBSource(load=1, present=(f"B:{m_star}",),
                             candidate=candidate, model_key=FIXTURE_MODEL,
                             m_star=m_star, split=split, n_topics=n_topics,
                             n_draws=n_draws)


def calibration_row(kind: str, severity: int, *, solo: float,
                    chance: float = 0.0, split: str = "pooled",
                    kappa_b: float | None = 0.0, vacuity: float = 0.0,
                    n_topics: int = C.N_CALIBRATION,
                    per_topic: Sequence[float] = ()) -> CalibrationRow:
    label = f"{kind}:{severity}"
    source = (kappa_source(label, split=split, n_topics=n_topics)
              if kappa_b is not None else None)
    return CalibrationRow(
        kind=kind, severity=severity, split=split, model_key=FIXTURE_MODEL,
        solo_compliance=solo, chance_compliance=chance, solo_vacuity=vacuity,
        kappa_under_b=kappa_b, kappa_under_b_source=source,
        n_topics=n_topics, per_topic_solo=tuple(per_topic))


def rung(kind: str, severity: int, k: int, *, n: int = 24, chance: float = 0.0,
         vac: int = 0, reserve: bool = False) -> PrescreenRung:
    return PrescreenRung(kind=kind, severity=severity, solo_k=k, solo_n=n,
                         chance_k=chance * n, chance_n=float(n),
                         vacuous_k=vac, n_topics=n, draws_per_topic=1,
                         reserve=reserve)


def ladder(kind: str, rates: Sequence[float], *, n: int = 24,
           chance: float = 0.0) -> list[PrescreenRung]:
    from dci1v7.verifiers.constraints import LADDERS
    return [rung(kind, q, round(r * n), n=n, chance=chance)
            for q, r in zip(LADDERS[kind], rates)]


def a_grid(rates: Sequence[float] = (0.92, 0.71, 0.58, 0.54, 0.50, 0.46,
                                     0.42, 0.33), *, n: int = 24
           ) -> list[ARung]:
    return [ARung(severity=q, solo_k=round(r * n), solo_n=n,
                  chance_k=0.0, chance_n=float(n), n_topics=n,
                  draws_per_topic=1)
            for q, r in zip(C.TARGET_GRID, rates)]


def split_rows(kind: str, severity: int, *, solo_a: float, solo_b: float,
               chance: float = 0.0, kappa_b: float = 0.0,
               n_topics: int = C.N_CALIBRATION_A,
               noise: float = 0.0) -> tuple[CalibrationRow, CalibrationRow]:
    """Two split rows with per-topic vectors whose means are the solo rates.
    A deterministic alternating pattern keeps the split difference small."""
    import numpy as np
    rng = np.random.default_rng(severity + 7)

    def vec(p):
        base = np.clip(np.round(rng.normal(p, 0.25, size=n_topics) * 4) / 4,
                       0, 1)
        base = base - base.mean() + p
        return tuple(float(np.clip(v, 0, 1)) for v in base)

    return (calibration_row(kind, severity, solo=solo_a, chance=chance,
                            split=C.CALIBRATION_A, kappa_b=kappa_b,
                            n_topics=n_topics, per_topic=vec(solo_a)),
            calibration_row(kind, severity, solo=solo_b, chance=chance,
                            split=C.CALIBRATION_B, kappa_b=kappa_b,
                            n_topics=n_topics, per_topic=vec(solo_b)))


#: The signed records a few evidence checks need, committed so they run in CI
#: and a fresh clone (``tools/v8_ci_evidence_fixture.py``; the manifest names
#: each source and its hashes, and ``test_evidence_subset`` checks them).
SUBSET = Path(__file__).resolve().parent / "fixtures" / "evidence_subset"


def subset_manifest() -> dict:
    return json.loads((SUBSET / "MANIFEST.json").read_text())


def pilot_eligibility_inputs() -> dict:
    """Per pilot lane, the fields of ``GATE_3_REFERENCES.by_frame`` the LOCAL
    eligibility rule reads."""
    return json.loads((SUBSET / subset_manifest()["local_eligibility"]["fixture"])
                      .read_text())


@pytest.fixture(scope="session")
def v7_replication_root(tmp_path_factory) -> Path:
    """An evidence root holding the committed v7 ``qwen3-4b`` stage records,
    each checked against the manifest's SHA-256 before a loader opens it."""
    root = tmp_path_factory.mktemp("evidence_subset")
    for rel, entry in subset_manifest()["backtest"]["files"].items():
        data = gzip.decompress((SUBSET / entry["fixture"]).read_bytes())
        assert hashlib.sha256(data).hexdigest() == entry["sha256"], rel
        (root / rel).parent.mkdir(parents=True, exist_ok=True)
        (root / rel).write_bytes(data)
    return root
