# Swidux ConfigWorker — set up & deploy remote config

How to scaffold and deploy the backend that answers `SwiduxKillswitch` and `SwiduxFeatureFlags`. Read this when the task is "host / deploy / onboard remote config" — not needed for ordinary plugin wiring (that's `swidux-patterns.md`). Everything here is self-contained: write the two files below into a fresh directory and run the `wrangler` commands; you do **not** need the Swidux repo checked out.

## What & why

**One Worker + one Workers KV namespace serves the whole portfolio.** Don't create per-app Workers or namespaces. Every app's killswitch and feature-flag config are paths under a single URL base, so there is never a second URL to remember and onboarding an app is just adding KV keys — no redeploy, no DNS.

The control plane is the **Cloudflare KV dashboard** (Workers & Pages → KV → `CONFIG`). Keys read as `<appID>/<resource>` and sort alphabetically, so the portfolio is one list grouped by app. Editing a value (the emergency block, a flag flip) is: open the key, edit JSON, save.

Routing model:

```
GET /<appID>/<resource>   ->   KV key  "<appID>/<resource>"

GET /counter/killswitch   ->   KV key  "counter/killswitch"  (KillswitchConfig)
GET /counter/flags        ->   KV key  "counter/flags"       (FeatureFlagsConfig)
GET /                     ->   "swidux-config: ok"  (health target)
```

- `appID` and `resource` are lowercase slugs, ≤ 64 chars each (`^[a-z0-9][a-z0-9-]{0,63}$`). Anything else — including `//` or trailing-slash aliases and segments long enough to trip KV's 512-byte key limit — → `404`. `GET`/`HEAD` only; else `405`.
- **Missing key → type-aware fail-open default**, so a not-yet-seeded app is never blocked and never breaks decode: `killswitch` → `{}` (empty `KillswitchConfig` = allow everyone), `flags` → `{"version":1,"flags":{}}` (valid v1, no flags), any other resource → `{}`. A failed KV read serves the same default (with `Cache-Control: no-store`) — never a 500. The `X-Config-Source` response header says which case you hit: `kv` (seeded), `default` (unseeded), `error` (KV read failed).
- Per-resource `Cache-Control` governs *client* HTTP caches (URLSession — Cloudflare's CDN does not cache Worker responses): `killswitch` is the incident lever, kept short at `max-age=60`; `flags`/other `max-age=300`. Server-side, the KV read passes a matching per-PoP `cacheTtl` (60/300).

Key-naming convention (keep canonical JSON in `seeds/<appID>/<resource>.json` in the repo so there's reviewable history and a known-good to paste back):

```
<appID>/killswitch     KillswitchConfig     (gate / force-update)
<appID>/flags          FeatureFlagsConfig   (rollouts, variants, values)
<appID>/<future>       arbitrary JSON       (room to grow; defaults to {})
```

`appID` is the app's stable slug. Pick it once and keep it forever — it's baked into the shipped app's endpoint URLs.

## The runnable artifacts

Write these verbatim into a new directory (e.g. `ConfigWorker/`). They are vendor-neutral (`swidux-config`).

### `worker.js`

```js
// Shared config endpoint — one Cloudflare Worker, backed by Workers KV,
// serving killswitch + feature-flag (+ arbitrary future) config for every app
// in a portfolio.
//
// Route: GET /<appID>/<resource>  ->  KV key `<appID>/<resource>`
//   e.g.  GET /counter/killswitch ->  KV key "counter/killswitch"
//         GET /counter/flags     ->  KV key "counter/flags"
//
// The contract each Swidux plugin expects is unchanged: a plain GET that
// returns the resource's config-shaped JSON. SwiduxKillswitch decodes
// `KillswitchConfig`; SwiduxFeatureFlags' HTTPFeatureFlagsService decodes
// `FeatureFlagsConfig`. Both are fail-open, so every config request must get a
// *decodable* body — an unseeded key AND a failed KV read both serve the
// type-aware default rather than an error (see DEFAULTS below).
//
// Onboarding a new app = adding its KV keys in the dashboard. No redeploy, no
// new Worker, no new URL. See README.md.

// Route grammar: exactly `/<slug>/<slug>`, lowercase, each segment ≤ 64 chars.
// One anchored regex keeps the KV key space exactly `<slug>/<slug>` — no
// traversal, no injection, no `//`/trailing-slash aliases, and no key long
// enough to trip KV's 512-byte key limit (an oversized `get()` key throws).
const ROUTE = /^\/([a-z0-9][a-z0-9-]{0,63})\/([a-z0-9][a-z0-9-]{0,63})$/;

// Type-aware fail-open defaults, served when a key isn't seeded yet or KV
// itself errors. `{}` decodes to an allow-everyone KillswitchConfig; the flags
// default decodes to a valid v1 config with no flags. Unknown resources fall
// back to `{}`. `__proto__: null` so an attacker-shaped resource like
// "constructor" can't resolve up Object.prototype and defeat the
// `?? FALLBACK` chain.
const DEFAULTS = {
  __proto__: null,
  killswitch: "{}",
  flags: '{"version":1,"flags":{}}',
};
const FALLBACK = "{}";

// Client cache hint (URLSession/browser — Cloudflare's CDN does not cache
// Worker responses). Killswitch is the incident lever — keep it short so a
// flip reaches re-fetching clients fast. (The client's `cacheLifetime` still
// dominates effective propagation; see README "Freshness".)
const CACHE_CONTROL = {
  __proto__: null,
  killswitch: "public, max-age=60",
  flags: "public, max-age=300",
};
const DEFAULT_CACHE_CONTROL = "public, max-age=300";

// KV's own per-PoP read cache (seconds; platform minimum 60). This is the
// only server-side cache in play; keep killswitch at the floor so a flip
// propagates fast, let everything else sit longer to cut KV origin reads.
const KV_CACHE_TTL = {
  __proto__: null,
  killswitch: 60,
};
const DEFAULT_KV_CACHE_TTL = 300;

export default {
  async fetch(request, env) {
    // Read-only public config — only GET/HEAD make sense.
    if (request.method !== "GET" && request.method !== "HEAD") {
      return new Response("Method Not Allowed", {
        status: 405,
        headers: { Allow: "GET, HEAD" },
      });
    }

    const path = new URL(request.url).pathname;

    // Health target for smoke tests / uptime monitors.
    if (path === "/") {
      return new Response("swidux-config: ok\n", {
        headers: { "Content-Type": "text/plain" },
      });
    }

    const match = ROUTE.exec(path);
    if (!match) {
      return new Response("Not Found", {
        status: 404,
        headers: { "Cache-Control": "public, max-age=60" },
      });
    }
    const [, appID, resource] = match;

    // Fail open on KV errors too: a client that can't decode gets nothing a
    // client that got a 500 wouldn't, so serve the default and mark it
    // no-store so recovery isn't delayed by caches.
    let stored = null;
    let kvError = false;
    try {
      stored = await env.CONFIG.get(`${appID}/${resource}`, {
        cacheTtl: KV_CACHE_TTL[resource] ?? DEFAULT_KV_CACHE_TTL,
      });
    } catch {
      kvError = true;
    }

    const body = stored ?? DEFAULTS[resource] ?? FALLBACK;
    return new Response(body, {
      headers: {
        "Content-Type": "application/json",
        "Cache-Control": kvError
          ? "no-store"
          : (CACHE_CONTROL[resource] ?? DEFAULT_CACHE_CONTROL),
        // Where the body came from: "kv" (seeded), "default" (unseeded), or
        // "error" (KV read failed, default served). Purely diagnostic —
        // `curl -i` shows at a glance whether a key is really seeded.
        "X-Config-Source": kvError ? "error" : stored === null ? "default" : "kv",
        "X-Content-Type-Options": "nosniff",
        "Access-Control-Allow-Origin": "*",
      },
    });
  },
};
```

### `wrangler.toml`

```toml
name = "swidux-config"
main = "worker.js"
compatibility_date = "2026-05-17"

[observability]
enabled = true

# One namespace holds the whole portfolio. Keys are `<appID>/<resource>`
# (e.g. "counter/killswitch", "counter/flags"). Create the namespace once,
# then paste the printed ids below:
#
#   wrangler kv namespace create CONFIG
#   wrangler kv namespace create CONFIG --preview
#
# Each command prints an id. `binding` must stay "CONFIG" — the Worker
# reads `env.CONFIG`.
[[kv_namespaces]]
binding = "CONFIG"
id = "REPLACE_WITH_KV_NAMESPACE_ID"
preview_id = "REPLACE_WITH_KV_PREVIEW_NAMESPACE_ID"
```

### `seeds/<appID>/killswitch.json`

`KillswitchConfig` shape. An empty `{}` means "allow everyone"; populate to gate. Replace `<App>` / the App Store id when you use it.

```json
{
    "minimumSupportedVersion": "1.2.0",
    "blockedTitle": "Update required",
    "blockedMessage": "Please update <App> to keep using it.",
    "updateURL": "https://apps.apple.com/app/id000000000"
}
```

### `seeds/<appID>/flags.json`

`FeatureFlagsConfig` shape — one of each flag kind (boolean rollout, weighted variant, tunable value). `version` is always `1`.

```json
{
  "version": 1,
  "flags": {
    "show_celebration_emoji": {
      "type": "boolean",
      "rollout": 100
    },
    "counter_button_style": {
      "type": "variant",
      "variants": [
        { "value": "control", "weight": 50 },
        { "value": "treatment", "weight": 50 }
      ]
    },
    "max_counters": {
      "type": "value",
      "value": 5
    }
  }
}
```

## One-time org setup

Run once for the whole portfolio:

```sh
npm i -g wrangler
wrangler login

# Each prints an id. Paste into wrangler.toml's [[kv_namespaces]]:
wrangler kv namespace create CONFIG            # -> id
wrangler kv namespace create CONFIG --preview  # -> preview_id

wrangler deploy
```

Note the printed `https://swidux-config.<your-subdomain>.workers.dev` URL (or attach a custom domain in the dashboard, e.g. `https://config.example.com`). **One URL for the whole portfolio** — this is the `<host>` every app's endpoints hang off.

## Smoke test

```sh
host=https://swidux-config.<your-subdomain>.workers.dev
curl -i $host/                      # 200 text/plain "swidux-config: ok"
curl -i $host/counter/killswitch    # 200 application/json, max-age=60
curl -i $host/counter/flags         # 200 application/json, max-age=300
curl -i $host/counter               # 404 (needs <appID>/<resource>)
curl -i -X POST $host/counter/killswitch   # 405
```

A seeded key returns its blob verbatim (`X-Config-Source: kv`); an unseeded one returns the type-aware default (`X-Config-Source: default`). Two regressions to include:

```sh
curl -i $host/counter/constructor                 # must be {} — __proto__: null
                                                  # defeats constructor/__proto__ input
curl -i $host/$(printf 'a%.0s' {1..600})/flags    # must be 404, never 500 — bounded
                                                  # route regex stops KV's 512-byte
                                                  # key limit from throwing
curl -i "$host//counter//killswitch"              # must be 404 — no path aliases
```

## Onboarding a new app (no redeploy)

1. Choose a stable lowercase `appID` (`[a-z0-9-]`). It is baked into the shipped endpoint URLs — pick once, keep forever.
2. Add `seeds/<appID>/killswitch.json` and `seeds/<appID>/flags.json` (copy `seeds/counter/*` as a starting point), commit.
3. Seed the keys — dashboard, or:
   ```sh
   wrangler kv key put --binding=CONFIG <appID>/killswitch "$(cat seeds/<appID>/killswitch.json)"
   wrangler kv key put --binding=CONFIG <appID>/flags      "$(cat seeds/<appID>/flags.json)"
   ```
4. Point that app's `Store.configured()` at `…/<appID>/killswitch` and `…/<appID>/flags` (see `swidux-patterns.md` killswitch / feature-flags wiring).

No `wrangler deploy`, no new Worker, no DNS. An unseeded key already serves the safe fail-open default, so step 3 isn't even blocking for launch — it just means "no rules yet."

## Incident runbook — block a bad build

1. Cloudflare dashboard → Workers & Pages → KV → `CONFIG` → `<appID>/killswitch`.
2. Set the gate:
   ```json
   {
     "minimumSupportedVersion": "1.4.1",
     "blockedTitle": "Update required",
     "blockedMessage": "Please update <App> to keep using it.",
     "updateURL": "https://apps.apple.com/app/idXXXXXXXXX"
   }
   ```
3. Save. Mirror it back into `seeds/<appID>/killswitch.json` and commit so the repo stays the source of truth.

## Freshness: the backend can't fix client staleness

Effective propagation = **max(KV per-PoP `cacheTtl`, client HTTP cache, client `cacheLifetime`)** — the last term dominates. The killswitch plugin caches the fetched config for `cacheLifetime` (**default 3600s**) regardless of endpoint freshness — so a perfectly deployed emergency block still won't reach an already-launched app for up to an hour with the default. If fast emergency response matters:

- Lower `cacheLifetime` to ~300–900s in `KillswitchService.live(...)`.
- Dispatch `.killswitch(.forceFetch)` on app-foreground (it bypasses the freshness gate) so a returning user re-checks immediately.
- Keep the Worker's `Cache-Control` (`killswitch` is `max-age=60`) at or below the client `cacheLifetime` — telling the client's HTTP cache to hold the response longer than the plugin will re-ask buys nothing. (Cloudflare's CDN does not cache Worker responses; the only server-side cache is KV's per-PoP `cacheTtl` on the read, which the Worker keeps at 60 s for killswitch.)

## What this Worker deliberately is not

- **No write API.** Writes go through the dashboard or `wrangler` only — the Worker is read-only public config (`GET`/`HEAD`). Nothing to authenticate, nothing to abuse.
- **No per-user logic.** Flag bucketing is client-side in the plugin; the Worker just serves the config document. Keeping it dumb is exactly why it never needs a redeploy.

Free tier covers a portfolio comfortably (100k Worker requests/day, 100k KV reads/day); each request is one KV read served from the PoP-local KV cache when hot (`cacheTtl`), so KV origin load stays near zero. Note the free-tier KV read cap is also the availability ceiling — a widely-installed portfolio belongs on the paid plan.
