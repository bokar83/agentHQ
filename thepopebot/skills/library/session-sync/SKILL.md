---
name: session-sync
description: Syncs the current browser conversation summary to the agentsHQ orchestrator so Telegram can pick up with full context. Call at the end of any substantive browser session.
---

# session-sync

Sends the current browser conversation summary to the agentsHQ orchestrator's `/sync-session`
endpoint. This seeds PostgreSQL conversation memory under the user's session key so that
Telegram and browser share the same context.

## When to call

Call this skill at the end of a browser session when:
- The user completed a meaningful task or conversation
- The user says "I'll continue this on Telegram" or "save this session"
- A long research/analysis session just wrapped up
- Any time the user wants cross-interface continuity

## Usage

```bash
skills/library/session-sync/sync.sh "<session_key>" "<summary>" [notify]
```

### Arguments

- `session_key` — The user's Telegram chat_id or project-scoped key (e.g. `7792432594` or `7792432594:catalystworks-site`)
- `summary` — What happened in this browser session (1-3 paragraphs, key decisions and outputs)
- `notify` — Optional: pass `notify` to send a Telegram ping when done

### Examples

```bash
# Basic sync
skills/library/session-sync/sync.sh "7792432594" "We designed the CW website hero section. Final copy: [copy here]. Colors: #1a1a2e bg, #e94560 accent."

# Sync + notify Telegram
skills/library/session-sync/sync.sh "7792432594" "Research complete: top 5 AI tools for solopreneurs are..." notify
```

## Output

Returns JSON confirming the write and number of characters saved.
