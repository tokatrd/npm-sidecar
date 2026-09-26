# npm-sidecar

I use Nginx Proxy Manager and kept missing a few extras (per-host rules, 2FA on dashboards without auth), so I wrote this sidecar script that generates the extra configs for me instead of forking NPM.

**What it does:** `generate.py` reads `hosts.csv` and emits:
- per-host Caddy snippet with rate-limit + custom error page,
- Authelia access-control snippet (2FA for dashboards that lack auth),
- Cloudflare Workers per-subdomain dispatcher stub.

Pure stdlib Python, no server cost.

## Run
```bash
python3 generate.py hosts.csv out
python3 test_gen.py
```

*Put together with some AI help.*
