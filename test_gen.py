"""Smoke: generate.py emits all expected artifacts."""
import os, subprocess, pathlib
os.chdir(pathlib.Path(__file__).parent)


subprocess.run(["python3", "generate.py", "hosts.csv", "out"], check=True)
out = pathlib.Path("out")
assert (out / "Caddyfile.generated").exists()
assert "two_factor" in (out / "authelia-acl.yml").read_text()
print("npm-sidecar smoke OK")
