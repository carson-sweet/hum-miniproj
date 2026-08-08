#!/usr/bin/env python3
"""Write a bundle record. The token proves the script ran rather than being described."""
import argparse
import hashlib
import json
import time
from pathlib import Path


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=".")
    ap.add_argument("--name", required=True)
    args = ap.parse_args()

    token = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()[:16]
    record = {
        "marker": "MP-P0.2-BUNDLE-RECORD",
        "token": token,
        "name": args.name,
        "recorded_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }
    out = Path(args.out).expanduser().resolve() / "bundle-record.json"
    out.write_text(json.dumps(record, indent=2))
    print(f"wrote {out}")
    print(f"token={token}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
