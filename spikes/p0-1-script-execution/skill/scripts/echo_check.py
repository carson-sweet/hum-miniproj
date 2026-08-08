#!/usr/bin/env python3
"""Write a sentinel that only real execution can produce.

Fields are runtime-derived on purpose: a host that describes running this script
instead of running it cannot fill them in correctly without executing something.
"""
import argparse
import hashlib
import json
import os
import platform
import sys
import time
from pathlib import Path


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=".")
    args = ap.parse_args()

    source = Path(__file__).read_bytes()
    payload = {
        "marker": "MP-P0.1-SENTINEL",
        "token": hashlib.sha256(source).hexdigest()[:16],
        "python_version": platform.python_version(),
        "executable": sys.executable,
        "pid": os.getpid(),
        "cwd": os.getcwd(),
        "script_path": str(Path(__file__).resolve()),
        "wrote_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }

    out = Path(args.out).expanduser().resolve() / "probe-sentinel.json"
    out.write_text(json.dumps(payload, indent=2))
    print(f"wrote {out}")
    print(f"token={payload['token']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
