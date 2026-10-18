# Low-level card metrics straight from sysfs, in Prometheus text format (stdlib only).
# Only what the cluster doesn't already scrape (node_hwmon_*, amd_gpu_*, tt_* cover temps, power, VRAM, busy %).
#   python3 k8s-llm-example/exporter/exporter.py --once   print once and self-check (works on the VM too)
#   python3 k8s-llm-example/exporter/exporter.py          serve http://0.0.0.0:9400/metrics
import glob
import os
import re
import sys
from http.server import BaseHTTPRequestHandler, HTTPServer


def read(path):
    try:
        with open(path) as f:
            return f.read().strip()
    except OSError:  # file missing on this driver/firmware, or busy: skip the metric
        return None


def collect():
    out = []

    def add(name, kind, help_, samples):
        out.append(f"# HELP {name} {help_}\n# TYPE {name} {kind}")
        for labels, value in samples:
            out.append(name + "{" + ",".join(f'{k}="{v}"' for k, v in labels.items()) + "} " + value)

    clocks, beats, pcie, dpm = [], [], [], []
    for d in sorted(glob.glob("/sys/class/tenstorrent/tenstorrent!*")):
        card = {"card": d.rsplit("!", 1)[1], "serial": read(f"{d}/tt_serial"), "type": read(f"{d}/tt_card_type")}
        for clk in ("aiclk", "axiclk", "arcclk"):
            if (v := read(f"{d}/tt_{clk}")) is not None:
                clocks.append(({**card, "clock": clk}, v))
        if (v := read(f"{d}/tt_heartbeat")) is not None:
            beats.append((card, v))
        for f in sorted(glob.glob(f"{d}/pcie_perf_counters/*")):
            if (v := read(f)) is not None:
                pcie.append(({**card, "counter": os.path.basename(f)}, v))

    for d in sorted(glob.glob("/sys/class/drm/card[0-9]*/device")):
        if read(f"{d}/vendor") != "0x1002":  # AMD only
            continue
        card = {"card": d.split("/")[4], "serial": read(f"{d}/serial_number")}
        for clk in ("sclk", "mclk"):
            # "0: 500Mhz\n1: 800Mhz *\n..." -> the level marked * is the current one
            if m := re.search(r"(\d+)Mhz \*", read(f"{d}/pp_dpm_{clk}") or ""):
                dpm.append(({**card, "clock": clk}, m.group(1)))

    add("sysfs_tt_clock_mhz", "gauge", "Tenstorrent clock (tt_aiclk/axiclk/arcclk)", clocks)
    add("sysfs_tt_heartbeat", "gauge", "Tenstorrent ARC firmware heartbeat; stops increasing if the firmware hangs", beats)
    add("sysfs_tt_pcie_perf_words_total", "counter", "Tenstorrent PCIe perf counters (pcie_perf_counters/*)", pcie)
    add("sysfs_amdgpu_dpm_mhz", "gauge", "AMD GPU current DPM clock level (pp_dpm_sclk/mclk)", dpm)
    return "\n".join(out) + "\n"


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        body = collect().encode()
        self.send_response(200)
        self.send_header("Content-Type", "text/plain; version=0.0.4")
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *args):  # no log line per scrape
        pass


if __name__ == "__main__":
    if "--once" in sys.argv:
        text = collect()
        print(text, end="")
        samples = [l for l in text.splitlines() if not l.startswith("#")]
        assert samples, "no cards found under /sys/class/tenstorrent or /sys/class/drm"
        assert all(re.fullmatch(r"sysfs_\w+\{.*\} -?\d+(\.\d+)?", l) for l in samples), "malformed sample"
    else:
        HTTPServer(("0.0.0.0", 9400), Handler).serve_forever()
