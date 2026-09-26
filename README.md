# npm-sidecar

I use Nginx Proxy Manager and kept missing a few extras (per-host rules, 2FA on dashboards without auth), so I wrote this sidecar script that generates the extra configs for me instead of forking NPM.

Topology: `[client] → Caddy (:80/:443, the files below) → your upstreams`. NPM keeps doing what it does; Caddy sits in front and adds the extras. Caddy is not read by NPM — run it as its own container/service.

## hosts.csv format

```csv
host,upstream,auth
jellyfin.lan,127.0.0.1:8096,none
ha.lan,127.0.0.1:8123,authelia
```

- `host` — required, the public hostname.
- `upstream` — where Caddy proxies to (default `127.0.0.1:8080`).
- `auth` — `none` (plain proxy) or `authelia` (adds the forward-auth import + a `two_factor` ACL rule).

## Run

```bash
python3 generate.py hosts.csv out
python3 test_gen.py  # expect: npm-sidecar smoke OK
```

Requires Python 3.x, stdlib only (`csv`, `pathlib`, `argparse`).

## Use the output (`out/`)

- `Caddyfile.generated` → include from your `Caddyfile` (Caddy v2). Rate limiting is a commented note — stock Caddy has no `rate_limit`; use e.g. `mholt/caddy-ratelimit` if you want it live.
- `authelia-snippet.caddy` → import it too; it defines the `(authelia_proxy)` snippet (edit the `login.example.com` URL). Needs Authelia v4+.
- `authelia-acl.yml` → merge into Authelia's `configuration.yml` (you still need your own `default_policy`).
- `worker-<host>.js` → one stub per host; paste at dash.cloudflare.com → Workers → Create → Deploy. Blocks `/admin` as an example.

MIT — see LICENSE.

*Put together with some AI help.*
