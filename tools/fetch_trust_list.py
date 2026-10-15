"""Fetch the official C2PA trust anchors into data/trust/anchors.pem (MANUAL INTEGRATION step).

Without this file only the demo root CA is trusted, so real-world Content Credentials (ChatGPT, Gemini, Firefly,
Pixel/Leica cameras …) validate as *Valid* (signature OK, identity unverified) instead of *Trusted*.

Sources (verify URLs against the C2PA conformance programme — they moved during 2025/26):
  - C2PA conformance trust list (Conforming Products / Trust Lists, conformance v0.2, 31 Jul 2026)
  - Content Credentials "known certificate list" published by the CAI for its Verify tool
You may also append your own enterprise anchors (e.g. your organisation's claim-signing CA).

Usage:  python tools/fetch_trust_list.py [--url URL ...] [--append file.pem]
"""
from __future__ import annotations

import argparse
import pathlib
import sys
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from app import config  # noqa: E402

DEFAULT_URLS = [
    # Current CAI/C2PA anchors (PEM bundle). Check https://contentcredentials.org/verify and the C2PA conformance
    # pages for the authoritative location; this URL is the one used by the open-source c2patool trust settings.
    "https://contentcredentials.org/trust/anchors.pem",
    "https://contentcredentials.org/trust/allowed.pem",
]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--url", action="append", help="PEM bundle URL (repeatable)")
    ap.add_argument("--append", action="append", help="local PEM file to append")
    args = ap.parse_args()
    urls = args.url or DEFAULT_URLS
    anchors, allowed = [], []
    for u in urls:
        try:
            req = urllib.request.Request(u, headers={"User-Agent": "Provenably/0.1 trust-list fetch"})
            with urllib.request.urlopen(req, timeout=30) as r:
                pem = r.read().decode("utf-8", "replace")
            if "-----BEGIN CERTIFICATE-----" not in pem:
                print(f"skip {u}: no PEM certificates in response")
                continue
            (allowed if "allowed" in u else anchors).append(pem)
            print(f"ok   {u}: {pem.count('-----BEGIN CERTIFICATE-----')} certificates")
        except Exception as e:
            print(f"fail {u}: {e}")
    for f in args.append or []:
        anchors.append(pathlib.Path(f).read_text())
        print(f"appended {f}")
    if anchors:
        config.TRUST_ANCHORS_PEM.write_text("\n".join(anchors))
        print(f"wrote {config.TRUST_ANCHORS_PEM}")
    if allowed:
        config.TRUST_ALLOWED_PEM.write_text("\n".join(allowed))
        print(f"wrote {config.TRUST_ALLOWED_PEM}")
    if not anchors:
        print("No anchors fetched. Reports will keep showing 'Valid' instead of 'Trusted' for real-world credentials.")
        sys.exit(1)
    print("Restart the server; each worker thread re-applies trust settings on first use.")


if __name__ == "__main__":
    main()
