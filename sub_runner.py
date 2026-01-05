#!/usr/bin/env python3
import os
import subprocess
import sys
from datetime import datetime

BASE = "scan_results"

def run(cmd):
    p = subprocess.run(
        cmd,
        shell=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.PIPE,
        text=True
    )
    if p.returncode != 0:
        print(p.stderr, file=sys.stderr)

def main(domain):
    scan_id = datetime.now().strftime("%d")
    outdir = f"{BASE}/{domain}_{scan_id}"
    os.makedirs(outdir, exist_ok=True)

    ctfr = f"{outdir}/subdomains_ctfr.txt"
    sublister = f"{outdir}/subdomains_sublister.txt"
    subfinder = f"{outdir}/subdomains_subfinder.txt"
    findomain = f"{outdir}/subdomains_findomain.txt"

    # CTFR
    run(
        f"python3 tools/ctfr/ctfr.py -d {domain} -o {ctfr} && "
        f"sed 's/\\*.//g' {ctfr} | tail -n +12 | sort -u > {ctfr}.tmp && mv {ctfr}.tmp {ctfr}"
    )

    # Sublist3r
    run(f"python3 tools/Sublist3r/sublist3r.py -d {domain} -t 30 -o {sublister}")

    # Subfinder
    run(f"tools/subfinder -d {domain} -silent -timeout 5 -t 30 -o {subfinder}")

    # Findomain (FIXED)
    findomain_bin = "tools/findomain"
    if os.path.exists(findomain_bin):
        run(
            f"cd {outdir} && "
            f"{os.path.abspath(findomain_bin)} "
            f"-t {domain} -q -u subdomains_findomain.txt"
        )
    else:
        print("[!] findomain binary not found, skipping", file=sys.stderr)

    # Merge
    final_out = f"{outdir}/subdomain_{domain}.txt"
    run(f"cat {outdir}/subdomains_*.txt | sort -u > {final_out}")

    # Alive check
    alive_out = f"{outdir}/alive_httpx_{domain}.txt"
    run(f"tools/httpx -l {final_out} -silent -threads 50 -timeout 10 -o {alive_out}")

    if not os.path.exists(alive_out):
        open(alive_out, "w").close()

    print(final_out)

if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit(1)
    main(sys.argv[1])
