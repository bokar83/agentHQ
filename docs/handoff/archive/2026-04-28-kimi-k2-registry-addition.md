# Session Handoff - Kimi K2 Registry Addition - 2026-04-28

## TL;DR

Reviewed an implementation plan to add Moonshot AI's Kimi models to agentsHQ. Ran Sankofa Council + Karpathy audit, both flagged the plan's core assumption (Moonshot requires routing bypass) as unverified. Live OpenRouter check revealed Kimi K2 is already on OpenRouter (6 models), collapsing the plan to a 7-line COUNCIL_MODEL_REGISTRY addition. No routing changes, no new env vars, no architectural fork.

## What was built / changed

- `orchestrator/agents.py`: Added `moonshotai/kimi-k2-0905` to COUNCIL_MODEL_REGISTRY (lines ~199-205). Tags: `deep_reasoning`, `long_context`, `fresh_perspective`. Cost tier: `low`. Pricing: $0.40/$2.00 /mtok. Context: 262K.
- Memory: Updated `feedback_openrouter_routing_philosophy.md`: registry now 19 models across 9 providers.
- Memory: Created `feedback_verify_openrouter_before_bypass.md`: Python snippet + rule for always checking OpenRouter live before planning any provider bypass.

## Decisions made

- **Use kimi-k2-0905 not kimi-k2**: k2-0905 has 262K context vs 128K and costs $0.40 vs $0.57 /mtok. Better value, larger context window.
- **Registry-only change**: No `get_llm` branching. OpenRouter carries the model natively; `_resolve_openrouter_model_string` handles it automatically via the `provider/slug` path.
- **No MOONSHOT_API_KEY needed**: OpenRouter routes to Moonshot; our single OPENROUTER_API_KEY covers it.
- **Karpathy verdict on original plan: HOLD** on Principles 1 and 4 (unverified assumption + weak verification plan). Post-check, the simplified plan passes all four.

## What is NOT done (explicit)

- Not committed or pushed: the agents.py change is local only.
- Kimi K2 has not been tested end-to-end (no actual API call made). The registry entry is syntactically correct but an inference test against a real Moonshot-routed call has not run.
- The newer kimi-k2.6 ($0.74 input) was noted but not added: no capability gap justifies the cost premium over k2-0905 today.

## Open questions

- Should `kimi-k2-0905` be wired to any specific role/complexity slot in `ROLE_CAPABILITY` or `ROLE_COST_CEILING`? Currently it competes on capability tags (deep_reasoning + long_context) with existing models in the `low` tier. It will be selected automatically when cost ceiling allows and the capability matches.
- Worth running a real inference test on the first council run that picks it?

## Next session must start here

1. Commit `orchestrator/agents.py` with message: `feat(council): add moonshotai/kimi-k2-0905 to COUNCIL_MODEL_REGISTRY`
2. Optionally: run an end-to-end test: `python -c "from orchestrator.agents import get_llm; llm = get_llm('moonshotai/kimi-k2-0905', 0.3); print(llm.call([{'role':'user','content':'ping'}]))"` from inside the container or VPS.
3. Check roadmap `docs/roadmap/atlas.md` for M11d (model review agent): Kimi K2 is a good first candidate to surface in a weekly model review.

## Files changed this session

- `d:\Ai_Sandbox\agentsHQ\orchestrator\agents.py`: COUNCIL_MODEL_REGISTRY addition only
- `C:\Users\HUAWEI\.claude\projects\d-Ai-Sandbox-agentsHQ\memory\feedback_openrouter_routing_philosophy.md`: updated provider count
- `C:\Users\HUAWEI\.claude\projects\d-Ai-Sandbox-agentsHQ\memory\feedback_verify_openrouter_before_bypass.md`: new memory
- `d:\Ai_Sandbox\agentsHQ\docs\handoff\2026-04-28-kimi-k2-registry-addition.md`: this file
