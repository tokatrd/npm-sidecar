"""NPM sidecar generator. Stdlib only. Reads hosts.csv, emits configs.

Topology this assumes: [client] -> Caddy (:80/:443, this output) -> your
upstreams. NPM keeps doing what it does; Caddy adds the extras per host.
"""

import argparse, csv, pathlib, sys

RATE_LIMIT_NOTE = (
    "  # rate limiting needs a plugin, e.g. mholt/caddy-ratelimit (Caddy v2)"
)


def load_hosts(path):
    try:
        with open(path, newline="") as f:
            return list(csv.DictReader(f))
    except FileNotFoundError:
        print(f"ERROR: {path} not found — copy hosts.csv and edit it", file=sys.stderr)
        sys.exit(2)


def caddy_snippet(h):
    host = (h.get("host") or "").strip()
    if not host:
        print(
            "ERROR: empty host in hosts.csv — every row needs a host", file=sys.stderr
        )
        sys.exit(2)
    upstream = h.get("upstream", "127.0.0.1:8080") or "127.0.0.1:8080"
    extra = "  import authelia_proxy\n" if h.get("auth") == "authelia" else ""
    return (
        f"{host} {{\n  reverse_proxy {upstream}\n{extra}"
        f"{RATE_LIMIT_NOTE}\n"
        f'  handle_errors {{ respond "Down — try again" 502 }}\n}}\n'
    )


def authelia_snippet():
    return (
        "(authelia_proxy) {\n"
        "  forward_auth authelia:9091 {\n"
        "    uri /api/verify?rd=https://login.example.com\n"
        "    copy_headers Remote-User Remote-Groups Remote-Name Remote-Email\n"
        "  }\n"
        "}\n"
    )


def authelia_acl(hosts):
    lines = [
        "# generated — merge into authelia configuration.yml (needs a default_policy too):",
        "access_control:",
    ]
    for h in hosts:
        if h.get("auth") == "authelia":
            lines.append(f"  - domain: '{h['host']}'\n    policy: two_factor")
    return "\n".join(lines) + "\n"


def worker_stub(host):
    return (
        f"// {host} — Cloudflare Worker stub (one per host).\n"
        "// Deploy: dash.cloudflare.com -> Workers -> Create -> paste -> Deploy.\n"
        "export default { async fetch(req) {\n"
        "  const url = new URL(req.url);\n"
        "  if (url.pathname.startsWith('/admin')) return new Response('blocked', {status: 403});\n"
        "  return fetch(req);\n} };\n"
    )


def main():
    ap = argparse.ArgumentParser(
        description="Generate Caddy/Authelia/Worker configs from hosts.csv."
    )
    ap.add_argument("csv", nargs="?", default="hosts.csv")
    ap.add_argument("out", nargs="?", default="out")
    a = ap.parse_args()
    outdir = pathlib.Path(a.out)
    outdir.mkdir(exist_ok=True)
    hosts = load_hosts(a.csv)
    if not hosts:
        print(f"ERROR: {a.csv} has no host rows", file=sys.stderr)
        sys.exit(2)
    (outdir / "Caddyfile.generated").write_text(
        "".join(caddy_snippet(h) for h in hosts)
    )
    (outdir / "authelia-snippet.caddy").write_text(authelia_snippet())
    (outdir / "authelia-acl.yml").write_text(authelia_acl(hosts))
    for h in hosts:
        (outdir / f"worker-{h['host']}.js").write_text(worker_stub(h["host"]))
    print(f"generated {len(hosts)} hosts -> {outdir}/")


if __name__ == "__main__":
    main()
