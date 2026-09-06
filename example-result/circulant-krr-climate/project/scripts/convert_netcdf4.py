#!/usr/bin/env python3
"""External-validation roadmap: convert real Kaplan SST v2 (netCDF-4/HDF5) to
the accepted .npy/.npz format.

NOT executed in this project: the host stack (NumPy/SciPy/scikit-learn only)
cannot read netCDF-4/HDF5. This script documents and provides the conversion
path for a subsequent real-data validation run in an environment where
h5py (or netCDF4) IS available. Purpose per the analysis-gate revision
feedback: make the synthetic-only skill numbers transferable to real data.

Usage (roadmap):  python3 scripts/convert_netcdf4.py [url-or-path]
Writes:           results/raw/real/fields.npy  (float32, (n_month, lat, lon))
                  results/raw/real/index.npy   (Nino3.4 index, Trenberth box)
                  results/raw/real/meta.json   (dataset.origin = "real-kaplan-sst-v2")

Input source: NOAA PSL Kaplan SST v2 monthly anomalies,
  https://psl.noaa.gov/thredds/fileServer/Datasets/kaplan_sst/sst.mon.anom.nc
  (netCDF-4/HDF5; variables approx: sst/lat/lon/time).

After conversion, run `make run-all` again; the pipeline's load_data()
prefers results/raw/real/ and will mark every artifact
dataset.origin = "real-kaplan-sst-v2" (no [simulated] markers).
"""
from __future__ import annotations

import json
import os
import sys


def main(path=None):
    src = path or ("https://psl.noaa.gov/thredds/fileServer/Datasets/"
                   "kaplan_sst/sst.mon.anom.nc")
    try:
        import h5py  # not in the allowed stack; available in the roadmap env
    except ImportError as e:
        sys.exit("h5py unavailable here (expected): " + str(e) +
                 "\nThis is the documented external-validation roadmap; "
                 "run on a host with h5py/netCDF4 to produce real data.")

    out = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                       "results", "raw", "real")
    os.makedirs(out, exist_ok=True)

    local = src
    if src.startswith("http"):
        import urllib.request
        local = os.path.join(out, "sst.mon.anom.nc")
        urllib.request.urlretrieve(src, local)

    with h5py.File(local, "r") as f:
        # Kaplan SST v2 layout (typical netCDF-4 mapping); adjust names as needed
        var = "sst" if "sst" in f else [k for k in f.keys() if "sst" in k.lower()][0]
        sst = f[var][:]          # (time, lat, lon)
        lat = f["lat"][:]
        lon = f["lon"][:]
        time = f["time"][:] if "time" in f else None

    # Nino3.4 box (Trenberth 1997): |lat| <= 5, 190E..240E (170W-120W)
    rows = [i for i, la in enumerate(lat) if abs(float(la)) <= 5.0]
    cols = [j for j, lo in enumerate(lon) if 190.0 <= float(lo) % 360.0 <= 240.0]
    index = sst[:, rows][:, :, cols].mean(axis=(1, 2))

    np_save = __import__("numpy").save
    np_save(os.path.join(out, "fields.npy"), sst.astype("float32"))
    np_save(os.path.join(out, "index.npy"), index.astype("float64"))
    meta = {
        "dataset.origin": "real-kaplan-sst-v2",
        "simulation_marker": None,
        "source": src,
        "grid": {"lat": lat.tolist(), "lon": lon.tolist()},
        "n_months": int(sst.shape[0]),
        "nino34_box": {"rows": rows, "cols": cols},
        "note": "external-validation roadmap conversion (h5py required; not executed on the CPU-only stack)",
    }
    with open(os.path.join(out, "meta.json"), "w") as fh:
        json.dump(meta, fh, indent=1)
    print("converted real Kaplan SST v2 ->", out)


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else None)