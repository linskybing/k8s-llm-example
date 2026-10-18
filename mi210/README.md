# AMD Instinct MI210

Four GPUs (gfx90a, 64 GB each). Jobs get one with `resourceClaimTemplateName: mi210`; PyTorch on ROCm sees them as `torch.cuda`.

## Your script
Edit `matmul.py` (or point `command` in `job.yaml` at your script):
```bash
kubectl replace --force -f k8s-llm-example/mi210/job.yaml
kubectl logs -f job/mi210-job
```
More GPUs: `kubectl apply -f k8s-llm-example/mi210/mi210x4.yaml` (your template, `count: 4`; any 1-4 works), then
`resourceClaimTemplateName: mi210x4`. The container must list the claim under `resources.claims` (as in `job.yaml`),
or it holds the GPUs but sees none ("No CUDA GPUs are available"). n150 + MI210 in one Job: list both claims.

## LLM (Llama-3.2-1B, vLLM, OpenAI API)
```bash
kubectl replace --force -f k8s-llm-example/mi210/vllm.yaml
kubectl get pods                          # READY 1/1 when the model is loaded
kubectl port-forward job/mi210-vllm 8000:8000 &
python3 k8s-llm-example/chat.py "Hi"
kubectl delete job mi210-vllm
```
4 GPUs: `mi210x4` + `--tensor-parallel-size 4`.

## Your own vLLM
Your fork (Python only) in your home + the image's compiled kernels. Clone at the image's version once:
```bash
git clone -b v0.32.0 https://github.com/vllm-project/vllm ~/vllm
```
Then as above with `vllm-custom.yaml` (Job `mi210-vllm-custom`). Resubmit after each edit; C++/HIP changes need a full build (not covered).

SGLang doesn't run on MI210: its ROCm images and kernels are built for MI300+ (gfx942) only.
