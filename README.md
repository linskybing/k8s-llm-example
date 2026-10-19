# n150 + MI210 user guide

One Tenstorrent n150 (Wormhole, 12 GB DRAM) and 4 AMD Instinct MI210 (64 GB each). Jobs queue for them, like Slurm:
**submit -> wait -> run -> delete when done -> card freed.** Everything below runs on the node.
You are cluster-admin: you can change anything in Kubernetes, so be careful with other people's namespaces.

```
k8s-llm-example/
├── n150/       Tenstorrent n150: script, shell, LLM (vLLM), your own vLLM / SGLang     -> n150/README.md
├── mi210/      AMD MI210 x4: script, multi-GPU, LLM (vLLM), your own vLLM              -> mi210/README.md
├── exporter/   your own metrics exporter (both cards)                                  -> exporter/README.md
└── chat.py     ask any LLM server on port 8000
```

## Login
```bash
ssh <you>@<machine public ip>
kubectl get pods        # ready to use; default namespace u-<you>
```

## Your home
The examples mount your home (`hostPath: /home/<you>`) and start there: same files as over SSH, nothing to copy.
Jobs run as the image's user (often root; you have sudo), so files they write may be root-owned.
Cloned this repo yourself? Fill in your name first: `sed -i "s/<you>/$USER/g" $(grep -rl '<you>' ~/k8s-llm-example)`.
LLM examples need your own Hugging Face token (accept the Llama 3.2 license on HF first), once:
`kubectl create secret generic hf-token --from-literal=token=hf_xxx`

## Queue
```bash
kubectl get workloads                   # yours; ADMITTED=True = got the card
kubectl get clusterqueue default        # pending / admitted counts (n150 and MI210 share this queue)
kubectl get --raw /apis/visibility.kueue.x-k8s.io/v1beta2/clusterqueues/default/pendingworkloads   # everyone's order
```

## Metrics
Prometheus scrapes the whole cluster (nodes, pods, control plane, network flows, queue, MI210, n150).
```bash
kubectl -n monitoring port-forward svc/kube-prometheus-stack-prometheus 9090 &   # http://127.0.0.1:9090
kubectl -n monitoring port-forward svc/kube-prometheus-stack-grafana 3000:80 &   # Grafana, ask the admin for the password
kubectl top pods -A
```
Your own exporter: add a ServiceMonitor or PodMonitor in any namespace; Prometheus picks it up. Example: `exporter/`.

## Rules
- Everything in `u-<you>` is queued by default (Jobs, Pods, Deployments). Jobs get no retries.
- No time limit: delete your Job when done, others wait for the card. Auto-stop: label `kueue.x-k8s.io/max-exec-time-seconds: "3600"`.
- You can create your own claims/templates, namespaces, operators, CRDs. Other namespaces aren't queued: if you grab a card there, tell the others.
- No IOMMU: code holding a card can read all VM memory. Keep no secrets here.

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
