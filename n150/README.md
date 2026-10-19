# Tenstorrent n150

One card (Wormhole, 12 GB DRAM). Jobs get it with `resourceClaimTemplateName: n150`; hugepages etc. are added for you.

## Your script
Edit `matmul.py` (or point `command` in `job.yaml` at your script). CPU-only: remove the `resourceClaims` lines.
```bash
kubectl replace --force -f k8s-llm-example/n150/job.yaml
kubectl logs -f job/n150-job
```

## Interactive shell
```bash
kubectl replace --force -f k8s-llm-example/n150/shell.yaml
kubectl exec -it job/n150-shell -- bash
kubectl delete job n150-shell             # free the card
```

## LLM (Llama-3.2-1B, vLLM, OpenAI API)
Settings (context length, batch) live in `llama-3.2-1b-n150.json`. Load it into configmap `llm-spec`
(again after every edit).
```bash
kubectl create configmap llm-spec --from-file=spec.json=k8s-llm-example/n150/llama-3.2-1b-n150.json --dry-run=client -o yaml | kubectl apply -f -
kubectl replace --force -f k8s-llm-example/n150/llm.yaml
kubectl get pods                          # READY 1/1 after ~3 min
kubectl port-forward job/n150-llm 8000:8000 &
python3 k8s-llm-example/chat.py "Hi"
kubectl delete job n150-llm
```
Knobs: `max_context`, `vllm_args.max_model_len/max_num_seqs/max_num_batched_tokens`; 8192 works, 128k runs out of memory.
Other models need a matching spec and image: ask the admin.

## Your own vLLM / SGLang
Your fork (Python only) in your home + the image's tt-metal. Clone at the image's version once:
```bash
git clone https://github.com/tenstorrent/vllm ~/tt-vllm && git -C ~/tt-vllm checkout 222ee06          # vllm-custom.yaml
git clone -b v0.5.8.post1 https://github.com/sgl-project/sglang ~/tt-sglang                           # sglang-custom.yaml
git clone -b v0.11.1 https://github.com/tenstorrent/tt-inference-server ~/tt-inference-server         #   (+ TT plugin)
```
Then as above with `vllm-custom.yaml` (Job `n150-vllm-custom`, needs `llm-spec`) or `sglang-custom.yaml`
(Job `n150-sglang-custom`, experimental, first run builds ~1 min). Resubmit after each edit.
