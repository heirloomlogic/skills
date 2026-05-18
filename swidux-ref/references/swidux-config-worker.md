# Swidux ConfigWorker — set up & deploy remote config

How to scaffold and deploy the backend that answers `SwiduxKillswitch` and
`SwiduxFeatureFlags`. Read this when the task is "host / deploy / onboard
remote config" — not needed for ordinary plugin wiring (that's
`swidux-patterns.md`). Everything here is self-contained: write the two files
below into a fresh directory and run the `wrangler` commands; you do **not**
need the Swidux repo checked out.

## What & why

**One Worker + one Workers KV namespace serves the whole portfolio.** Don't
create per-app Workers or namespaces. Every app's killswitch and feature-flag
config are paths under a single URL base, so there is never a second URL to
remember and onboarding an app is just adding KV keys — no redeploy, no DNS.

The control plane is the **Cloudflare KV dashboard** (Workers & Pages → KV →
`CONFIG`). Keys read as `<appID>/<resource>` and sort alphabetically, so the
portfolio is one list grouped by app. Editing a value (the emergency block, a
flag flip) is: open the key, edit JSON, save.

Routing model:

```
GET /<appID>/<resource>   ->   KV key  "<appID>/<resource>"

GET /counter/killswitch   ->   KV key  "counter/killswitch"  (KillswitchConfig)
GET /counter/flags        ->   KV key  "counter/flags"       (FeatureFlagsConfig)
GET /                     ->   "swidux-config: ok"  (health target)
```

- `appID` and `resource` are lowercase slugs (`^[a-z0-9][a-z0-9-]*$`). Anything
  else → `404`. `GET`/`HEAD` only; else `405`.
- **Missing key → type-aware fail-open default**, so a not-yet-seeded app is
  never blocked and never breaks decode: `killswitch` → `{}` (empty
  `KillswitchConfig` = allow everyone), `flags` → `{"version":1,"flags":{}}`
  (valid v1, no flags), any other resource → `{}`.
- Per-resource edge cache: `killswitch` is the incident lever, kept short at
  `max-age=60`; `flags`/other `max-age=300`.

Key-naming convention (keep canonical JSON in `seeds/<appID>/<resource>.json`
in the repo so there's reviewable history and a known-good to paste back):

```
<appID>/killswitch     KillswitchConfig     (gate / force-update)
<appID>/flags          FeatureFlagsConfig   (rollouts, variants, values)
<appID>/<future>       arbitrary JSON       (room to grow; defaults to {})
```

`appID` is the app's stable slug. Pick it once and keep it forever — it's
baked into the shipped app's endpoint URLs.

## The runnable artifacts

Write these verbatim into a new directory (e.g. `ConfigWorker/`). They are
vendor-neutral (`swidux-config`).

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
// `FeatureFlagsConfig`. Both are fail-open, so a not-yet-seeded app must get a
// *decodable* default rather than an error (see DEFAULTS below).
//
// Onboarding a new app = adding its KV keys in the dashboard. No redeploy, no
// new Worker, no new URL. See README.md / DEPLOY.md.

// Segment grammar: lowercase slug. Rejecting anything else keeps the KV key
// space exactly `<slug>/<slug>` — no traversal, no injection, no surprise reads.
const SEGMENT = /^[a-z0-9][a-z0-9-]*$/;

// Type-aware fail-open defaults for a key that isn't seeded yet. `{}` decodes
// to an allow-everyone KillswitchConfig; the flags default decodes to a valid
// v1 config with no flags. Unknown resources fall back to `{}`.
// `__proto__: null` so an attacker-shaped resource like "constructor" can't
// resolve up Object.prototype and defeat the `?? FALLBACK` chain.
const DEFAULTS = {
  __proto__: null,
  killswitch: "{}",
  flags: '{"version":1,"flags":{}}',
};
const FALLBACK = "{}";

// Per-resource edge cache. Killswitch is the incident lever — keep it short so
// a flip reaches edge caches fast. (The client's `cacheLifetime` still
// dominates effective propagation; see README "Freshness".)
const CACHE_CONTROL = {
  __proto__: null,
  killswitch: "public, max-age=60",
  flags: "public, max-age=300",
};
const DEFAULT_CACHE_CONTROL = "public, max-age=300";

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

    // Expect exactly `/<appID>/<resource>`.
    const parts = path.split("/").filter((s) => s.length > 0);
    if (
      parts.length !== 2 ||
      !SEGMENT.test(parts[0]) ||
      !SEGMENT.test(parts[1])
    ) {
      return new Response("Not Found", { status: 404 });
    }

    const [appID, resource] = parts;
    const stored = await env.CONFIG.get(`${appID}/${resource}`);
    const body = stored ?? DEFAULTS[resource] ?? FALLBACK;

    return new Response(body, {
      headers: {
        "Content-Type": "application/json",
        "Cache-Control": CACHE_CONTROL[resource] ?? DEFAULT_CACHE_CONTROL,
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

`KillswitchConfig` shape. An empty `{}` means "allow everyone"; populate to
gate. Replace `<App>` / the App Store id when you use it.

```json
{
    "minimumSupportedVersion": "1.2.0",
    "blockedTitle": "Update required",
    "blockedMessage": "Please update <App> to keep using it.",
    "updateURL": "https://apps.apple.com/app/id000000000"
}
```

### `seeds/<appID>/flags.json`

`FeatureFlagsConfig` shape — one of each flag kind (boolean rollout, weighted
variant, tunable value). `version` is always `1`.

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

Note the printed `https://swidux-config.<your-subdomain>.workers.dev` URL (or
attach a custom domain in the dashboard, e.g. `https://config.example.com`).
**One URL for the whole portfolio** — this is the `<host>` every app's
endpoints hang off.

## Smoke test

```sh
host=https://swidux-config.<your-subdomain>.workers.dev
curl -i $host/                      # 200 text/plain "swidux-config: ok"
curl -i $host/counter/killswitch    # 200 application/json, max-age=60
curl -i $host/counter/flags         # 200 application/json, max-age=300
curl -i $host/counter               # 404 (needs <appID>/<resource>)
curl -i -X POST $host/counter/killswitch   # 405
```

A seeded key returns its blob verbatim; an unseeded one returns the type-aware
default. Include `curl -i $host/counter/constructor` as a regression — it must
return `{}` (the `__proto__: null` lookup tables defeat the
`constructor`/`__proto__` input class).

## Onboarding a new app (no redeploy)

1. Choose a stable lowercase `appID` (`[a-z0-9-]`). It is baked into the
   shipped endpoint URLs — pick once, keep forever.
2. Add `seeds/<appID>/killswitch.json` and `seeds/<appID>/flags.json` (copy
   `seeds/counter/*` as a starting point), commit.
3. Seed the keys — dashboard, or:
   ```sh
   wrangler kv key put --binding=CONFIG <appID>/killswitch "$(cat seeds/<appID>/killswitch.json)"
   wrangler kv key put --binding=CONFIG <appID>/flags      "$(cat seeds/<appID>/flags.json)"
   ```
4. Point that app's `Store.configured()` at `…/<appID>/killswitch` and
   `…/<appID>/flags` (see `swidux-patterns.md` killswitch / feature-flags
   wiring).

No `wrangler deploy`, no new Worker, no DNS. An unseeded key already serves the
safe fail-open default, so step 3 isn't even blocking for launch — it just
means "no rules yet."

## Incident runbook — block a bad build

1. Cloudflare dashboard → Workers & Pages → KV → `CONFIG` →
   `<appID>/killswitch`.
2. Set the gate:
   ```json
   {
     "minimumSupportedVersion": "1.4.1",
     "blockedTitle": "Update required",
     "blockedMessage": "Please update <App> to keep using it.",
     "updateURL": "https://apps.apple.com/app/idXXXXXXXXX"
   }
   ```
3. Save. Mirror it back into `seeds/<appID>/killswitch.json` and commit so the
   repo stays the source of truth.

## Freshness: the backend can't fix client staleness

Effective propagation = **max(edge cache, client `cacheLifetime`)**. The
killswitch plugin caches the fetched config for `cacheLifetime`
(**default 3600s**) regardless of endpoint freshness — so a perfectly deployed
emergency block still won't reach an already-launched app for up to an hour
with the default. If fast emergency response matters:

- Lower `cacheLifetime` to ~300–900s in `KillswitchService.live(...)`.
- Dispatch `.killswitch(.forceFetch)` on app-foreground (it bypasses the
  freshness gate) so a returning user re-checks immediately.
- Keep the Worker's edge `Cache-Control` (`killswitch` is `max-age=60`) at or
  below the client `cacheLifetime` — caching longer at the edge than the
  client will re-ask buys nothing.

## What this Worker deliberately is not

- **No write API.** Writes go through the dashboard or `wrangler` only — the
  Worker is read-only public config (`GET`/`HEAD`). Nothing to authenticate,
  nothing to abuse.
- **No per-user logic.** Flag bucketing is client-side in the plugin; the
  Worker just serves the config document. Keeping it dumb is exactly why it
  never needs a redeploy.

Free tier covers a portfolio comfortably (100k Worker requests/day, generous
KV read quota); each request is one edge-cached KV read, so origin load stays
near zero.
