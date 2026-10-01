# Hosting Swidux remote config

Read this when the task is to host, deploy, or review the server behind `SwiduxKillswitch` and `SwiduxFeatureFlags`. Plugin wiring is in `swidux-patterns.md`.

Swidux ships no server code. The full contract, the deployment factors, and a conformance checklist are in the DocC article [Host Remote Config](https://heirloomlogic.github.io/Swidux/documentation/swidux/hostingremoteconfig). Build from that article and run its checklist against the result. This page is the summary.

## What the clients do with a response

`KillswitchService.live` and `HTTPFeatureFlagsService` fetch with a plain HTTPS `GET`, bypass the device URL cache, and abandon the fetch after 10 s or 1 MB.

- A 2xx with a decodable body replaces the cached config.
- Anything else keeps the last-known-good config. With nothing cached, the killswitch stays unblocked and flags read their Swift defaults.

The server sends a 2xx only when it knows the answer.

## Responses

| Case | Response |
|---|---|
| Config stored | `200`, the stored JSON verbatim |
| Known app, nothing stored | `200` with `{}` (killswitch) or `{"version":1,"flags":{}}` (flags), plus `X-Config-Source: default` |
| Storage failed or timed out | `503`, non-JSON body, `Cache-Control: no-store` |
| Stored value isn't a JSON object | `502`, non-JSON body, `no-store` |
| Unknown resource or malformed path | `404` |
| Unknown app ID | `404`, without a storage read |
| Not `GET` or `HEAD` | `405` |

## Rules that are easy to get wrong

- **Never serve a default on a storage error.** A decodable 200 overwrites every client's cache, so an outage would lift every killswitch block and reset every flag.
- **Never answer unknown resources with `200 {}`.** A typo in a shipped URL becomes a killswitch that can't fire.
- **Never onboard an app with a gated killswitch.** Start from `{}`. Copying an incident config as a template blocks every user.
- **Validate before publishing.** Versions must be strict `MAJOR.MINOR.PATCH`; reject unknown killswitch keys (a misspelled key reads as no rule); flags `version` stays `1`.
- **Reject unknown app IDs before reading storage, rate-limit per IP at the edge, and serve from one origin.** The endpoint is public and unauthenticated.
- **On a plan with a daily cap** (Cloudflare Workers Free: 100k requests and 100k KV reads a day, account-wide), those measures keep one IP under the cap, but two IPs can exhaust it, and then no killswitch block can be delivered until 00:00 UTC. A metered plan with no cap (Workers Paid) turns that into a bill instead. Present both; the choice belongs to the owner.
- **Confirm every write reached production.** `wrangler kv key put` writes to local storage unless you pass `--remote`; `GET` the URL afterwards.
- **App IDs are permanent.** They are baked into shipped URLs. Use a lowercase slug, not a bundle ID.

## Existing deployments

If the project already has a config endpoint, onboard apps through its own tooling and runbook. Don't run a setup guide against an account that already serves config: redeploying a Worker under its existing name with a new, empty namespace makes every key read as unseeded.
