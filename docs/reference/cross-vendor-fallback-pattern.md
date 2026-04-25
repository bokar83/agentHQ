# Cross-vendor fallback pattern

A small architectural note for anywhere we depend on a single API vendor whose
credits, rate limits, or uptime are not under our control. Pulled from
RoboNuggets R57's `tools/providers/` design and generalized for agentsHQ.

This is a reference pattern, not a library. Implement it case by case where
the win is real.

## Where this applies in agentsHQ

| Capability | Primary | Suggested fallbacks (in order) | Status |
|---|---|---|---|
| Image / video generation | Kie AI (`skills/kie_media`) | Google AI Studio, WaveSpeed AI | pattern only; not yet wired |
| Web scraping | Firecrawl (`firecrawl_tools`) | Apify (purpose-built actors), Playwright Python | partial; Apify added for niche-research, no fallback router yet |
| LLM routing | OpenRouter via `orchestrator/router.py` | direct Anthropic, direct OpenAI | already implemented in router.py |
| Notion writes | Notion MCP / official SDK | local cache + retry queue | not implemented; deferred until we hit a real outage |

The point is not to wire all of these tomorrow. The point is to keep the
pattern consistent so that when one vendor breaks, the swap is mechanical.

## The pattern (3 parts)

### 1. A registry, not a switch

Each vendor capability gets a small registry: an ordered list of providers,
each with a `name`, a `call(args) -> result` function, and a `health()`
predicate. Order is preference. The registry lives next to the capability,
not in a global config dump.

Bad: `if KIE_OUT_OF_CREDITS: use_google()` scattered across three modules.

Good: `IMAGE_GEN_PROVIDERS = [kie, google_studio, wavespeed]`, with one
function that walks the list.

### 2. Health-aware, not error-blind

The walk function should not "try all providers blindly until one returns 200".
That hides real failures (a bad prompt that fails everywhere) and burns through
credits. Instead:

- Treat hard errors (auth, payment, rate-limit, vendor 5xx) as "this provider
  is down right now"; fall through to the next.
- Treat soft errors (input validation, content policy) as "the request itself
  is wrong"; do not fall through. Fail loudly.
- Cache the "down" verdict for a short window (default 60s) so we do not
  re-hit a known-bad provider for every request in the same batch.

### 3. Observability is mandatory

Every fallback call must log:
- Which providers were tried, in order.
- What error each one returned (one line, not a stack trace).
- Which provider succeeded, if any.
- Total elapsed time.

Without this, debugging becomes "we got an image, but I have no idea who
made it". That is worse than a single-provider hard failure.

## What this is NOT

- Not a load balancer. We are not trying to spread requests across vendors
  for capacity. We are trying to keep one capability working when one vendor
  flakes.
- Not a generic abstraction. Resist building `BaseProvider` with seven hooks
  and three lifecycle methods. Two functions per vendor is enough until proven
  otherwise.
- Not for cost optimization. Choosing a cheaper vendor when a request happens
  to fit it is a different feature; build it separately if you want it.

## Reference: R57 implementation we did not copy

R57 ships a `tools/providers/` directory with one Python module per vendor and
a small router. The pattern is fine, but R57's reasons to switch (default
provider for each model) are different from ours (vendor outage / credit
exhaustion). Read it if you build the kie_media fallback; do not copy it
wholesale.

Path on disk:
`workspace/skool-harvest/robonuggets/test-tool/downloads/extracted/r57-template-community/tools/providers/`

## Trigger to actually implement

Build the first fallback (image / video) when one of:
- Kie credits run out mid-week and we lose a day of content.
- A specific model on Kie hard-fails repeatedly while available on Google AI
  Studio or WaveSpeed.
- We add a third use case for image generation outside `kie_media`.

Until then, the registry stays a one-liner inside `kie_media.py` and this doc
is just a placeholder.
