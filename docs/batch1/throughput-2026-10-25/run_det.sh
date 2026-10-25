#!/usr/bin/env bash
FS=/lambda/nfs/dci; B=$FS/repo/environments/cuda-vllm/.venv/bin/python
export HF_HOME=$FS/hf HF_HUB_OFFLINE=1 VLLM_WORKER_MULTIPROC_METHOD=spawn
cd $FS/bench
G2="google/gemma-3n-E2B-it 5e092ebca197cdcd8d8b195040accf22693501bc 0.85"
for cfg in "1 64" "1 512" "0 512"; do set -- $cfg; tag=e$1_c$2
  for p in 1 2; do rep=$([ $p = 1 ] && echo 2 || echo 1)
    CUDA_VISIBLE_DEVICES=0 $B -I $FS/bench_throughput.py $G2 $1 $2 1024 $rep det_${tag}_p$p.json 2>>err_det.log | grep "^RESULT " | cut -c8- >> det_results.jsonl
  done
  python3 -c "import json,sys; a=json.load(open(\"det_${tag}_p1.json\")); b=json.load(open(\"det_${tag}_p2.json\")); print(json.dumps({\"setting\":\"$tag\",\"fresh_process_identical\":sum(x==y for x,y in zip(a,b)),\"of\":len(a)}))" >> det_results.jsonl
done
echo DET_DONE >> det_results.jsonl
