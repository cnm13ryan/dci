"""The v5 execution layer: one runner per registered stage.

Eighteen stages, eighteen runners, one driver. ``run/lifecycle.run_stage`` is
the only way a stage record is written, so the five steps every stage
performs --- guard, compute, sign, mirror, log --- cannot be skipped by a
runner that forgets one.

Nothing here can execute today. ``PROTOCOL_REGISTERED`` depends on all
nineteen of §34's decisions and every later stage depends on its predecessor
having passed, so the first ``run`` command fails at stage 1 with
``REGISTRATION_INCOMPLETE`` and a list of what is open. That is the intended
state: the layer exists so that the lifecycle is complete and auditable
before adoption, not so that anything can be measured before it.

``run/contracts.py`` is the audit that every field a stage reads is a field
some earlier stage writes. It runs statically and again against the real
payloads of ``tests_v5/test_synthetic_lifecycle.py``.
"""
