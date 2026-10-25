#!/usr/bin/env bash
FS=/lambda/nfs/dci; B=$FS/repo/environments/cuda-vllm/.venv/bin/python
export HF_HOME=$FS/hf HF_HUB_OFFLINE=1 VLLM_WORKER_MULTIPROC_METHOD=spawn
cd $FS/bench
one(){ gpu=$1; m=$2; r=$3; u=$4; e=$5; c=$6; rep=${7:-1}; CUDA_VISIBLE_DEVICES=$gpu $B -I $FS/bench_throughput.py $m $r $u $e $c 3904 $rep 2>>err_gpu$gpu.log | grep "^RESULT " | cut -c8- >> results.jsonl; }
Q="Qwen/Qwen3-4B 1cfa9a7208912126459214e8b04321603b3df60c 0.85"
G4="google/gemma-3n-E4B-it c1221e9c62e34a43ab7ffacd1be0ea71f126ef10 0.95"
G2="google/gemma-3n-E2B-it 5e092ebca197cdcd8d8b195040accf22693501bc 0.85"
( for cfg in "1 64" "1 512" "0 64" "0 512" "0 0"; do one 0 $Q $cfg; done; one 0 $G2 0 512 2 ) &
( for cfg in "1 64" "1 512" "0 64" "0 512" "0 0"; do one 1 $G4 $cfg; done ) &
wait; echo BENCH_DONE >> results.jsonl
