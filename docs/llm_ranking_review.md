# LLM Ranking Review (bi-weekly checklist)

## Why this exists

`COUNCIL_MODEL_REGISTRY` in `orchestrator/agents.py` carries the capability tags (`deep_reasoning`, `creative_divergence`, `instruction_following`, etc.) and the per-Mtok prices that drive `select_by_capability`. Those tags and prices drift fast: a frontier model ships, a price drops, an underdog gains a capability, a model gets deprecated. Without a regular review, the registry rots and the council/agents keep picking yesterday's winner at yesterday's price.

## Cadence

Every other Monday. Block 30 minutes. Owner: Boubacar.

Next review due: **2026-04-27** (Mon). Subsequent: **2026-05-11**, **2026-05-25**, etc.

Log each review at the bottom of this file with the date and the diff applied.

## The five questions

For each, the source is OpenRouter's models page (`https://openrouter.ai/models`), the lmarena leaderboards, and the Anthropic / OpenAI / Google / xAI / DeepSeek release notes feeds.

1. **Cheapest model at each capability tier today?**
   Walk the registry. For each `cost_tier` (`very_low`, `low`, `low-medium`, `medium`, `medium-high`, `high`), is the cheapest entry still the cheapest on OpenRouter? If a cheaper model showed up at the same capability bar, swap or add it.

2. **New frontier model in the last 14 days?**
   Examples to watch: Claude 4.7 / 4.8, GPT-5.2 / 5.3, Gemini 3.2 / 3.3, Grok 5, DeepSeek r2, Qwen 3.5, Mistral Large 3. If yes, evaluate which capabilities it should claim and add it.

3. **Which existing model gained a capability tag?**
   Read recent benchmarks (lmarena, HumanEval, GPQA, MATH-500, AIME, SWE-bench). If Qwen3 just topped a category, give it the matching tag.

4. **Which model should LOSE a tag?**
   Capability claims are a promise. If a model has slid down a benchmark or a known regression has surfaced, strip the tag. Example: an Anthropic model losing `instruction_following` after a release that broke structured-output prompts.

5. **Any price cuts?**
   OpenRouter announces these in their changelog. Update `input_per_mtok` / `output_per_mtok`. A 2x price cut on a tagged-but-unused model can flip routing decisions immediately.

## How to apply changes

1. Edit `orchestrator/agents.py:85-192` (`COUNCIL_MODEL_REGISTRY`).
2. Run a sanity smoke test on the council:
   ```bash
   ssh root@agentshq.boubacarbarry.com "docker exec orc-crewai python /tmp/smoke_council.py"
   ```
   Confirm a 3-round run completes and `Voice models` log line shows the new selections.
3. Query `llm_calls` after a few real council runs to confirm cost-per-run hasn't regressed:
   ```sql
   SELECT council_run_id, COUNT(*) AS calls, ROUND(SUM(cost_usd)::numeric, 4) AS run_cost_usd
   FROM llm_calls WHERE council_run_id IS NOT NULL AND ts > NOW() - INTERVAL '7 days'
   GROUP BY council_run_id ORDER BY ts DESC LIMIT 20;
   ```
4. Commit with message `chore(registry): bi-weekly ranking review YYYY-MM-DD`.

## What this ritual is NOT

- Not a performance/quality review of agent output. That requires a shadow harness (Phase 3.5 prerequisite, separate work).
- Not a place to add new agents or change `ROLE_MODEL` / `ROLE_TEMPERATURE` mappings. Those are operational decisions, not registry hygiene.
- Not a place to remove provider-locked entries (chairman, consultant, orchestrator). Those decisions sit elsewhere.

## Review log

| Date | Reviewer | Models added | Models removed | Tags added | Tags removed | Price changes | Notes |
|---|---|---|---|---|---|---|---|
| 2026-04-21 | Claude (initial setup) | n/a | n/a | n/a | n/a | n/a | Doc created. First scheduled review 2026-04-27. |
| 2026-04-21 | Boubacar + Claude (early) | anthropic/claude-opus-4.7, qwen/qwen3.5-flash-02-23 | none | none | none | none | Pulled forward from Apr 27. Opus 4.7 same price as 4.6 but newer training. Qwen3.5-flash adds 1M context at very_low ($0.065/$0.26). Kept opus-4.6 as fallback. No swaps to existing routing. Also: routed x-ai reviews to grok-4-fast (15x/30x cheaper, smoke verified). |
