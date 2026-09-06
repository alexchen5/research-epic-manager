#!/usr/bin/env python3
"""Probe stdlib-readable real-data sources for Kaplan SST v2 anomalies.

Bounded to ~5 minutes total. Tries THREDDS DAP2 .ascii with corrected
constraint syntax and a few other genuinely stdlib-readable routes.
On success, writes the retrieved field(s) to results/raw/ and a
results/raw/data_mode.json marker. On failure, exits non-zero so the
pipeline falls back to the pre-committed synthetic-from-physics generator.
"""
import json
import os
import sys
import time
import urllib.request
import urllib.error

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
RAW = os.path.join(ROOT, "results", "raw")
os.makedirs(RAW, exist_ok=True)

DEADLINE = time.time() + 280.0  # ~4.7 min hard cap inside the 5-min allowance

# Candidate endpoints. DAP2 ascii constraint syntax is
# ?<var>[t0:stride:t1][y0:stride:y1][x0:stride:x1]
CANDIDATES = [
    {
        "name": "psl-thredds-dodsC-kaplan-sst-anom-ascii-small",
        "url": "https://psl.noaa.gov/thredds/dodsC/Datasets/kaplan_sst/sst.mon.anom.nc.ascii?sst[0:1:1][0:1:1][0:1:1]",
        "desc": "THREDDS DAP2 ascii, 1 time x 1 lat x 1 lon slice",
    },
    {
        "name": "psl-thredds-dodsC-kaplan-sst-monthly-ascii-small",
        "url": "https://psl.noaa.gov/thredds/dodsC/Datasets/kaplan_sst/sst.monthly.nc.ascii?sst[0:1:1][0:1:1][0:1:1]",
        "desc": "THREDDS DAP2 ascii (monthly non-anom file)",
    },
    {
        "name": "esrl-psd-thredds-kaplan-sst-ascii-small",
        "url": "https://www.esrl.noaa.gov/psd/thredds/dodsC/Datasets/kaplan_sst/sst.mon.anom.nc.ascii?sst[0:1:1][0:1:1][0:1:1]",
        "desc": "legacy ESRL host DAP2 ascii",
    },
]


def fetch(url, timeout=25):
    req = urllib.request.Request(url, headers={"User-Agent": "research-pipeline/1.0"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        data = resp.read()
    return resp.status, data


def main():
    log = []
    outcome = {"data_mode": "real", "source": None, "log": []}
    for cand in CANDIDATES:
        if time.time() > DEADLINE:
            break
        status = None
        err = None
        nbytes = 0
        try:
            status, data = fetch(cand["url"])
            nbytes = len(data)
            head = data[:200].decode("utf-8", errors="replace")
            log.append({"candidate": cand["name"], "status": status,
                        "bytes": nbytes, "head": head[:120]})
            if status == 200 and nbytes > 0 and "404" not in head:
                # a DAP2 ascii field response starts with a data block header
                print(f"[fetch] SUCCESS {cand['name']}: {nbytes} bytes")
                print(head[:500])
                # store as raw text for inspection
                path = os.path.join(RAW, "kaplan_probe_example.txt")
                with open(path, "wb") as f:
                    f.write(data)
                outcome["source"] = cand["url"]
                outcome["log"] = log
                outcome["probe_file"] = path
                # Now attempt the real slice we want: 1948-2023 monthly anoms
                # on the 5-degree 72x36 grid. Request full grid, single month
                # first to validate shape parsing.
                big = ("https://psl.noaa.gov/thredds/dodsC/Datasets/kaplan_sst/"
                       "sst.mon.anom.nc.ascii?sst[0:1:0][0:1:35][0:1:71]")
                try:
                    st, d = fetch(big, timeout=60)
                    bp = os.path.join(RAW, "kaplan_full_slice.txt")
                    with open(bp, "wb") as f:
                        f.write(d)
                    log.append({"candidate": "full-slice", "status": st,
                                "bytes": len(d), "head": d[:120].decode("utf-8", errors="replace")})
                    outcome["full_slice_file"] = bp
                except Exception as e:  # noqa: BLE001
                    log.append({"candidate": "full-slice", "error": repr(e)})
                with open(os.path.join(RAW, "data_mode.json"), "w") as f:
                    json.dump(outcome, f, indent=2)
                return 0
        except Exception as e:  # noqa: BLE001
            err = repr(e)
            log.append({"candidate": cand["name"], "error": err})
            print(f"[fetch] FAIL {cand['name']}: {err}")
    # All candidates failed
    outcome = {
        "data_mode": "synthetic-[simulated]",
        "source": None,
        "reason": "all stdlib-readable real-data routes failed within 5-min probe",
        "log": log,
    }
    with open(os.path.join(RAW, "data_mode.json"), "w") as f:
        json.dump(outcome, f, indent=2)
    print("[fetch] NO real-data route succeeded; synthetic fallback will fire.")
    return 1


if __name__ == "__main__":
    sys.exit(main())