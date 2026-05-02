# shadcn-compatible Agent / Chat / Tool-Call UIs

Agent UIs (Atlas chat, Studio operator panels, future MCP-app surfaces, any LLM-tool UI) start from an existing shadcn-compatible primitive set rather than composing from scratch.

## Primary source: 21st.dev Agent Elements

[agent-elements.21st.dev](https://agent-elements.21st.dev)

- React 19 + Tailwind v4 + Vercel AI SDK
- shadcn-aesthetic by default (composes cleanly with the rest of `ui-styling`)
- Copy-paste model (no install, no runtime dependency)

## Primitives covered

- Chat shell (message list, scroll, sticky composer)
- Tool-call cards: Bash, Edit, Search, Todo, Plan
- Clarifying questions block
- Input bar with attachments + paste handling
- Streaming markdown renderer

## When to use

When `frontend-design` is invoked on agent / chat / tool-call UI work, defer here before composing primitives by hand. This is the canonical-home rule applied: shadcn-substrate decisions live in `ui-styling`, and agent-elements is shadcn-substrate.

The Volta standard from `frontend-design` still applies on top: customize, never ship the default look.

## Related

- Atlas chat attachments: see `memory/reference_atlas_chat_attachments.md` for the existing paperclip + paste + Sonnet 4.6 wiring.
- For non-agent UIs (marketing, dashboards, auth), use the standard shadcn blocks from `references/shadcn-blocks.md` instead.

Borrowed from awesome-shadcn-ui curation (2026-05-02 absorb).
