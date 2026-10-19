# Your own exporter

Card data is plain files under `/sys`, readable over SSH:
```bash
grep . "/sys/class/tenstorrent/tenstorrent!0"/tt_aiclk /sys/class/drm/card1/device/gpu_busy_percent   # n150, MI210 (card1-4)
```
Prometheus already has `node_hwmon_*`, `amd_gpu_*`, `tt_*`. `exporter.py` adds the rest as `sysfs_*`.
```bash
python3 k8s-llm-example/exporter/exporter.py --once           # try it on the VM
kubectl replace --force -f k8s-llm-example/exporter/job.yaml
kubectl apply -f k8s-llm-example/exporter/podmonitor.yaml      # Prometheus scrapes it (and the LLM servers)
```
