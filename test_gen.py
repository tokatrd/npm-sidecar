"""Smoke: outputs exist and agree with hosts.csv."""

import os, subprocess, pathlib

os.chdir(pathlib.Path(__file__).parent)

subprocess.run(["python3", "generate.py", "hosts.csv", "out"], check=True)
out = pathlib.Path("out")
caddy = (out / "Caddyfile.generated").read_text()
acl = (out / "authelia-acl.yml").read_text()
assert "jellyfin.lan" in caddy and "ha.lan" in caddy and "files.lan" in caddy
assert "rate_limit {" not in caddy, (
    "must not emit plugin-only directives as live config"
)
assert "import authelia_proxy" in caddy
assert (out / "authelia-snippet.caddy").exists(), "must define the snippet it imports"
assert caddy.count("import authelia_proxy") == acl.count("two_factor") == 2
assert len(list(out.glob("worker-*.js"))) == 3
import shutil

shutil.rmtree(out)
print("npm-sidecar smoke OK")
