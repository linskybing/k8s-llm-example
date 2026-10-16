# n150 user guide

One Tenstorrent n150 (Wormhole, 12 GB DRAM). Jobs queue for it, like Slurm: **submit -> wait -> run -> delete when done -> card freed.**
One Job uses the card at a time. Everything below runs on the node.

```
k8s-n150-example/
├── run/     your script on the n150     job.yaml, matmul.py
├── shell/   interactive shell + n150    job.yaml
└── llm/     LLM server + client         job.yaml, chat.py, llama-3.2-1b-n150.json
```

## Login
```bash
ssh <you>@10.121.252.117
kubectl get pods        # ready to use; only your namespace u-<you>
```

## Your home
Every Job sees your home at `/home/<you>`, starts there, and runs as you.
Same files as over SSH, live. Nothing to upload or copy. Write output to home and it stays.

## Run code on the n150
Edit `run/matmul.py` (or point `command` in `run/job.yaml` at your script):
```bash
kubectl replace --force -f k8s-n150-example/run/job.yaml  # submit / resubmit
kubectl logs -f job/n150-job
```
CPU-only job: remove the `resourceClaims` lines. It won't wait for the card.

## Interactive shell
```bash
kubectl replace --force -f k8s-n150-example/shell/job.yaml
kubectl exec -it job/shell -- bash      # n150 + your home; prompt says "I have no name!": harmless
kubectl delete job shell                # free the card when done
```

## LLM (Llama-3.2-1B, OpenAI API)
Settings (model, context length, batch) live in `llm/llama-3.2-1b-n150.json`, your own copy.
The vLLM container runs as its own user and can't read your home, so first copy the file into configmap `llm-spec`.
The Job mounts it at `/spec`. Run that line again after every edit.
```bash
kubectl create configmap llm-spec --from-file=spec.json=k8s-n150-example/llm/llama-3.2-1b-n150.json --dry-run=client -o yaml | kubectl apply -f -
kubectl replace --force -f k8s-n150-example/llm/job.yaml
kubectl get pods                        # wait for READY 1/1 (~3 min)
kubectl port-forward job/llm-exp 8000:8000 &
python3 k8s-n150-example/llm/chat.py "Hi"
kubectl delete job llm-exp              # free the card
```
- Knobs: `max_context`, `vllm_args.max_model_len`, `vllm_args.max_num_seqs`, `vllm_args.max_num_batched_tokens`. 8192 works; 128k runs out of memory.
- More than one spec: `kubectl create configmap llm-spec-4k --from-file=spec.json=<file>`, then set `configMap: {name: llm-spec-4k}` in the Job.
- No spec (remove `RUNTIME_MODEL_SPEC_JSON_PATH` and the `spec` volume): image defaults, 128k context, out of memory.
- Other model: needs a matching spec and image. Ask the admin.
- HF token: already in secret `hf-token`.

## Queue
```bash
kubectl get workloads                   # yours; ADMITTED=True = got the card
kubectl get clusterqueue n150           # pending / admitted counts
kubectl get --raw /apis/visibility.kueue.x-k8s.io/v1beta2/clusterqueues/n150/pendingworkloads   # everyone's order
```

## Rules
- Jobs only. `kubectl run`, Pods and Deployments stay stuck in the queue.
- No time limit: delete your Job when done, others wait for the card. Auto-stop: label `kueue.x-k8s.io/max-exec-time-seconds: "3600"`.
- No retries on failure.
- No privileged, hostPath, hostNetwork. Your home is mounted for you.
- Image needs its own user (like vLLM)? Label the Job `n150/home: "false"`: no home mount.
- No IOMMU: code holding the card can read all VM memory. Keep no secrets here.

## kubectl cheatsheet
```bash
kubectl replace --force -f job.yaml     # submit / resubmit (apply says "unchanged" on finished Jobs)
kubectl get jobs,pods,workloads         # what's running
kubectl describe pod <pod>              # why Pending / failing (see Events)
kubectl get events --sort-by=.lastTimestamp
kubectl logs -f job/<job>               # follow output
kubectl exec -it job/<job> -- bash      # shell in a running Job
kubectl port-forward job/<job> 8000:8000
kubectl get job <job> -o yaml           # full spec, incl. what the platform added
kubectl delete job <job>                # cancel / stop / free the card
kubectl explain job.spec.template.spec  # field docs
```
