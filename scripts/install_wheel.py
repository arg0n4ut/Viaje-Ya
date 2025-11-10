#!/usr/bin/env python3
import glob, sys, subprocess, os

wheels = glob.glob(os.path.join('dist', '*.whl'))
if not wheels:
    sys.stderr.write("No wheel found in dist/ please run 'make build' first\n")
    sys.exit(1)

wheel = sorted(wheels)[-1]
print(f"Installing wheel: {wheel}")
subprocess.check_call([sys.executable, '-m', 'pip', 'install', '--upgrade', wheel])
