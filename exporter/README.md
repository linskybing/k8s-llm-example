# Your own exporter

Card data is plain sysfs files, readable over SSH:
```bash
grep . "/sys/class/tenstorrent/tenstorrent!0"/{tt_aiclk,tt_heartbeat} "/sys/class/tenstorrent/tenstorrent!0"/pcie_perf_counters/*   # n150
grep . /sys/class/drm/card1/device/{gpu_busy_percent,mem_info_vram_used,pp_dpm_sclk}                                              # MI210 (card1-4)
grep . /sys/class/hwmon/hwmon*/{name,temp1_input,power1_average}                                                                  # temps, power
```
Already in Prometheus: `node_hwmon_*`, `amd_gpu_*`, `tt_*`. `exporter.py` adds the rest (`sysfs_*`); add a file with one `read()` + `add()`.
```bash
python3 k8s-llm-example/exporter/exporter.py --once          # test on the VM
kubectl replace --force -f k8s-llm-example/exporter/job.yaml  # no card, no queue wait
kubectl apply -f k8s-llm-example/exporter/podmonitor.yaml     # scrapes pods labelled n150/metrics: "true" (also LLM servers)
```
Power sensors are averaged; a 15 s scrape misses spikes (arXiv:2312.02741).
