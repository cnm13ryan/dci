# The ROCm vLLM backend used for the reasoning-compute experiment

These scripts are run with the **other** project's interpreter, so the DCI venv
is never modified and Rounds 1-8 stay reproducible:

    VLLM=/home/cnm13ryan/git/inoculation-prompting/gcd_sycophancy/.venv/bin/python

Two settings are mandatory on 2x RX 7900 XTX. Without them a `tp>1` run allocates
on both cards and then stalls indefinitely in a collective:

    disable_custom_all_reduce=True          # vLLM's kernel assumes peer access
    NCCL_P2P_DISABLE=1                      # RCCL stages through host memory

Always clear inherited visibility variables first; a stale `HIP_VISIBLE_DEVICES`
silently lands both workers on one card.

    env -u ROCR_VISIBLE_DEVICES -u HIP_VISIBLE_DEVICES -u CUDA_VISIBLE_DEVICES \
      VLLM_WORKER_MULTIPROC_METHOD=spawn NCCL_P2P_DISABLE=1 \
      $VLLM -u reasoning_vllm.py Qwen/Qwen3-4B <revision> 0,256,512,1024,4096 \
        <design.jsonl> out.jsonl 512

`reasoning_vllm.py` generates only. Scoring is always done back in the study venv
by `../reasoning_score.py`, against the same registry, from the answer field —
the reasoning channel never reaches a verifier.

`Qwen3_5ForCausalLM` is NOT in vLLM 0.15.1's model registry; `Qwen3ForCausalLM`
is. That is why the reasoning programme runs on `Qwen/Qwen3-4B`.
