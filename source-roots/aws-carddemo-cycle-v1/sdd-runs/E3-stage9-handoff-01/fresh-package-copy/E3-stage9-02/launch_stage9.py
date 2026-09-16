#!/usr/bin/env python3
"""Reproduce Stage 9 package build/start smoke from this run directory."""
from pathlib import Path
import os, subprocess, sys
root = Path(__file__).resolve().parent
p2b = root / "execution/isolated-cycle/aws-carddemo-cycle-v1/P2b"
python = Path(os.environ.get("STAGE9_PYTHON", '<REDACTED_LOCAL_PATH>/casos/aws-carddemo-cycle-v1/P2a/.venv/bin/python'))
env = dict(os.environ)
registry = root / "execution/isolated-cycle/aws-carddemo-cycle-v1/P3/technical-packages-v3-argument/registry.json"
if registry.exists():
    env["P2B_FIXTURE_REGISTRY"] = str(registry)
cmd = [str(python), str(p2b / "p2b_binding.py"), "smoke"]
raise SystemExit(subprocess.call(cmd, cwd=p2b, env=env))
