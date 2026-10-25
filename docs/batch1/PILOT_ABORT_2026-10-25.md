# Batch 1 pilot: the stopped first run (2026-10-25)

**Run root:** `/lambda/nfs/dci/runs/pilot-2026-10-25` on the 2x H100 instance,
Freeze 1 `d81726970d6212fa0480097dd9a64ab8f2bd4395fb2b53228cccac9a4d2af6fb`,
commit `c174be8`. **Status:** abandoned at the researcher's instruction, not
failed. It is kept as a record and must never be resumed, scored or reused
as evidence. The D12 amendment below means a new Freeze 1 and a new root.

## What happened

| item | value |
|---|---|
| Freeze 1 | matched the Mac preview exactly; `pilot_authorizable` true, nothing blocking |
| Stage 1 start | 09:36:54 UTC, `execute --accelerator cuda --devices 0,1` |
| stopped | 09:45:12 UTC, by the researcher, because GPU utilisation was too low |
| accepted rows | 7,808 of 15,616. Both Gemma groups were complete (3,904 each); both Qwen groups were interrupted and none of their rows accepted |
| technical failures | 0; none exhausted |
| GPU use | ~45% utilisation and ~200 W of 700 W per GPU; Gemma at 11.7 (E2B) and 9.6 (E4B) rows/s |

## Cause and the change

- **Cause.** The runner sends 64 requests per `llm.generate` call
  (`chunk_size`). Each call waits for its longest answer, so the GPU sat
  partly idle.
- **CUDA graphs** were also off (`enforce_eager`), a workaround carried over
  from the ROCm workstation.
- **Benchmark.** A throwaway benchmark on the instance, on synthetic prompts
  outside any run root, compared the settings. The note and data are in
  [`throughput-2026-10-25/`](throughput-2026-10-25/NOTE.md).

| rows/s (3,904 prompts, pilot decoding) | graphs off, 64 | graphs off, 512 | graphs on, 512 |
|---|---|---|---|
| Qwen3-4B | 39.2 | 142.7 (3.6x) | 157.2 |
| Gemma 3n E4B | 10.7 | 58.1 (5.4x) | 79.2 |
| Gemma 3n E2B (1,024 prompts) | 12.4 | 64.2 (5.2x) | 95.4 |

- **Outcomes.** Every setting gave 100% `finish_reason` stop, 0 truncated,
  0 empty, and mean answer length unchanged to within 1 token.
- **Batch ceiling.** Sending one model's whole group in one call is no faster
  than 512, because vLLM keeps at most 256 sequences in flight.

**Decision (the researcher, 2026-10-25):**

- `chunk_size` 64 → **512**;
- CUDA graphs **stay off**;
- both are now explicit in D12's payload (`config.DECODING`).

CUDA graphs were rejected because they added 10-50% speed but cut
fresh-process regeneration agreement to 11%.

## Disclosure: regeneration is not byte-exact

The test was Gemma E2B on 1,024 prompts, run twice in separate fresh
processes, which is what `resume` does. Identical answers:

- **graphs off, chunk 64** (the setting approved before this change): 978 of
  1,024 (95.5%);
- **graphs off, chunk 512** (the new setting): 995 of 1,024 (97.2%);
- **graphs on, chunk 512:** 114 of 1,024 (11.1%).

vLLM is not batch-invariant here. So a row regenerated after a crash is
usually, not always, the same text as the first attempt would have been. The
smoke tests' 72 of 72 identical answers was too small a sample to show this.
The evidence is the stored records bound by Freeze 2, never a regeneration
from seeds, and Batch 1 makes no claim of byte-for-byte reproducibility from
seeds.

## What changes downstream

- **Re-approval:** D12's payload hash changes. The researcher re-approves
  D12; the other 13 decisions are unchanged.
- **No rebuild:** the backend code, environments and lock are unchanged, so
  there is no rebuild and no re-attestation.
- **New run:**
  - a new smoke test (the smoke plan hash changes with the decoding);
  - a new Freeze 1;
  - a new root (`runs/pilot-2026-10-25b`);
  - then Stage 1 and Stage 2.
- **Projected time:** about 3-4 minutes per stage on both GPUs, including
  model loads, against about 35-40 minutes before.
- **Batch 2** must use the same generation settings, because its references
  are chosen from Batch 1's results under them. Binding them in D12 ensures
  that.
