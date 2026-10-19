# AMD Instinct MI210

Four GPUs (64 GB each). A Job gets one with `resourceClaimTemplateName: mi210`; PyTorch sees them as `torch.cuda`.

## Script
Edit `matmul.py`, or point `command` in `job.yaml` at your script.
```bash
kubectl replace --force -f k8s-llm-example/mi210/job.yaml && kubectl logs -f job/mi210-job
```
More GPUs: `kubectl apply -f k8s-llm-example/mi210/mi210x4.yaml`, then `resourceClaimTemplateName: mi210x4`.
Keep `resources.claims` in the container (as in `job.yaml`), or it holds the GPUs but sees none.
n150 + MI210 in one Job: list both claims; it starts when both are free (never holds just one).

## LLM (Llama-3.2-1B, vLLM)
Needs your `hf-token` secret (main README).
```bash
kubectl replace --force -f k8s-llm-example/mi210/vllm.yaml
kubectl get pods                 # READY 1/1 when the model is loaded
kubectl port-forward job/mi210-vllm 8000:8000 &
python3 k8s-llm-example/chat.py "Hi"
kubectl delete job mi210-vllm
```

## Your own vLLM
Python changes only; compiled kernels come from the image. Clone once, then submit `vllm-custom.yaml` as above:
```bash
git clone -b v0.32.0 https://github.com/vllm-project/vllm ~/vllm
```
SGLang doesn't run on MI210 (its ROCm builds are MI300+ only).
