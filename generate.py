"""NPM sidecar generator. Stdlib only. Reads hosts.csv, emits configs."""

import csv, sys, pathlib


def load_hosts(path):
    with open(path) as f:
        return list(csv.DictReader(f))


def caddy_snippet(h):
    host = h["host"]
    upstream = h.get("upstream", "127.0.0.1:8080")
    auth = h.get("auth", "none")
    extra = "  import authelia_proxy\n" if auth == "authelia" else ""
    return (
        f"{host} {{\n  reverse_proxy {upstream}\n{extra}"
        f"  rate_limit {{ zone dynamic 20r/s burst 40 }}\n"
        f'  handle_errors {{ respond "Down — try again" 502 }}\n}}\n'
    )


def authelia_acl(hosts):
    lines = [
        "# generated — paste into authelia configuration.yml access_control:",
        "access_control:",
    ]
    for h in hosts:
        if h.get("auth") == "authelia":
            lines.append(f"  - domain: '{h['host']}'\n    policy: two_factor")
    return "\n".join(lines) + "\n"


def worker_stub(host):
    return (
        f"// {host} — Cloudflare Worker free-tier per-subdomain WAF stub\n"
        "export default { async fetch(req) {\n"
        "  const url = new URL(req.url);\n"
        "  if (url.pathname.startsWith('/admin')) return new Response('blocked', {status: 403});\n"
        "  return fetch(req);\n} };\n"
    )


def main():
    src = sys.argv[1] if len(sys.argv) > 1 else "hosts.csv"
    outdir = pathlib.Path(sys.argv[2] if len(sys.argv) > 2 else "out")
    outdir.mkdir(exist_ok=True)
    hosts = load_hosts(src)
    (outdir / "Caddyfile.generated").write_text(
        "".join(caddy_snippet(h) for h in hosts)
    )
    (outdir / "authelia-acl.yml").write_text(authelia_acl(hosts))
    for h in hosts:
        (outdir / f"worker-{h['host']}.js").write_text(worker_stub(h["host"]))
    print(f"generated {len(hosts)} hosts -> {outdir}/")


if __name__ == "__main__":
    main()
