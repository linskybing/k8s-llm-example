# n150 + MI210 user guide

One Tenstorrent n150 and four AMD MI210s, shared through a queue (like Slurm): **submit -> wait -> run -> delete**.
You have sudo and are cluster-admin: be careful with other people's namespaces.

```
n150/       Tenstorrent n150: script, shell, LLM, your own vLLM / SGLang   -> n150/README.md
mi210/      AMD MI210 x4: script, multi-GPU, LLM, your own vLLM            -> mi210/README.md
exporter/   your own metrics exporter                                    -> exporter/README.md
chat.py     ask any LLM server on port 8000
```

## Start
```bash
ssh <you>@<machine public ip>
kubectl get pods                 # works right away; your namespace is u-<you>
```
Jobs mount your home (`/home/<you>`) and start there. They run as the image's user (often root), so their output may be root-owned.
Cloned this repo yourself? Fill in your name first: `sed -i "s/<you>/$USER/g" $(grep -rl '<you>' ~/k8s-llm-example)`

## Hugging Face token (LLM examples, once)
1. Create a read token: https://huggingface.co/settings/tokens
2. Accept the Llama 3.2 license: https://huggingface.co/meta-llama/Llama-3.2-1B-Instruct
3. Store it in your namespace (not in shell history):
```bash
read -s HF_TOKEN && kubectl create secret generic hf-token --from-literal=token=$HF_TOKEN --dry-run=client -o yaml | kubectl apply -f -
```
Run it again to change the token. Missing secret = LLM pod stuck in `CreateContainerConfigError`.

## Queue and metrics
One queue for both cards: a Job waits only for the cards it asks for.
```bash
kubectl get clusterqueue default -o jsonpath='n150 in use: {.status.flavorsUsage[0].resources[?(@.name=="tenstorrent.com/chip")].total}/{.spec.resourceGroups[0].flavors[0].resources[?(@.name=="tenstorrent.com/chip")].nominalQuota}   MI210 in use: {.status.flavorsUsage[0].resources[?(@.name=="amd.com/gpu")].total}/{.spec.resourceGroups[0].flavors[0].resources[?(@.name=="amd.com/gpu")].nominalQuota}   waiting: {.status.pendingWorkloads}{"\n"}'
kubectl get workloads            # ADMITTED=True: your Job got its card
kubectl get --raw /apis/visibility.kueue.x-k8s.io/v1beta2/clusterqueues/default/pendingworkloads   # everyone waiting
kubectl -n monitoring port-forward svc/kube-prometheus-stack-prometheus 9090 &   # Prometheus at http://127.0.0.1:9090
```

## Rules
- Everything in `u-<you>` is queued. No retries, no time limit: **delete your Job when done**, others wait for the card.
- Auto-stop: label the Job `kueue.x-k8s.io/max-exec-time-seconds: "3600"`.
- Other namespaces aren't queued: if you grab a card there, tell the others.
- No IOMMU: code holding a card can read all VM memory. Keep no secrets here.

## kubectl
```bash
kubectl replace --force -f job.yaml     # submit / resubmit
kubectl get jobs,pods                   # what's running
kubectl describe pod <pod>              # why Pending / failing (Events)
kubectl logs -f job/<job>
kubectl exec -it job/<job> -- bash
kubectl delete job <job>                # stop + free the card
```
