# Tenstorrent n150

One card (12 GB). A Job gets it with `resourceClaimTemplateName: n150`.

## Script / shell
Edit `matmul.py`, or point `command` in `job.yaml` at your script.
```bash
kubectl replace --force -f k8s-llm-example/n150/job.yaml && kubectl logs -f job/n150-job
kubectl replace --force -f k8s-llm-example/n150/shell.yaml && kubectl exec -it job/n150-shell -- bash
kubectl delete job n150-shell
```

## LLM (Llama-3.2-1B, vLLM)
Needs your `hf-token` secret (main README). Settings (context length, batch) are in `llama-3.2-1b-n150.json`;
reload the configmap after each edit. Missing configmap = pod stuck in `Init`/`ContainerCreating` (`describe`: FailedMount)
and holds the n150 on every retry: delete the Job.
```bash
kubectl create configmap llm-spec --from-file=spec.json=k8s-llm-example/n150/llama-3.2-1b-n150.json --dry-run=client -o yaml | kubectl apply -f -
kubectl replace --force -f k8s-llm-example/n150/llm.yaml
kubectl get pods                 # READY 1/1 after ~3 min
kubectl port-forward job/n150-llm 8000:8000 &
python3 k8s-llm-example/chat.py "Hi"
kubectl delete job n150-llm
```

## Your own vLLM / SGLang
Python changes only; tt-metal comes from the image. Clone at the image's version once, then submit
`vllm-custom.yaml` (needs `llm-spec`) or `sglang-custom.yaml` (experimental) as above. Resubmit after each edit.
```bash
git clone https://github.com/tenstorrent/vllm ~/tt-vllm && git -C ~/tt-vllm checkout 222ee06
git clone -b v0.5.8.post1 https://github.com/sgl-project/sglang ~/tt-sglang
git clone -b v0.11.1 https://github.com/tenstorrent/tt-inference-server ~/tt-inference-server   # SGLang's TT plugin
```
