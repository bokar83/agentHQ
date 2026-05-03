# Studio - ElevenLabs Voice IDs

**Locked:** 2026-05-03, Studio M2 session
**Source:** Boubacar Barry (owner)

## Voice Registry

| Persona | Channel | Voice ID | Notes |
|---------|---------|----------|-------|
| Griot Kofi (male) | Under the Baobab | `U7wWSnxIJwCjioxt86mk` | Warm baritone, unhurried, storytelling register |
| Female narrator (alt) | Under the Baobab | `D9xwB6HNBJ9h4YvQFWuE` | Alt voice for female character POV episodes |
| Boubacar Barry | AI Catalyst | `KuCymRJ2M5Gs5LQIAbwJ` | His actual voice - openly him, this IS the channel |
| Hunter | First Generation Money + generic VO | `X4Lh5Ftnso6JSt25plzX` | Gender-neutral, warm, calm. Name nod to Hunter lead-gen tool. |
| Elhadja | Elder/wisdom voice | `Kpr3bkxYd7gPcHKxBohV` | Older gentleman register - use for elder characters, wisdom narration, elder griot moments. |

## Usage in M3 Production Crew

```python
ELEVENLABS_VOICES = {
    "griot_kofi":        "U7wWSnxIJwCjioxt86mk",  # Under the Baobab male
    "baobab_female":     "D9xwB6HNBJ9h4YvQFWuE",  # Under the Baobab female alt
    "boubacar":          "KuCymRJ2M5Gs5LQIAbwJ",  # AI Catalyst
    "hunter":            "X4Lh5Ftnso6JSt25plzX",  # First Generation Money + generic
    "elhadja":           "Kpr3bkxYd7gPcHKxBohV",  # Elder/wisdom voice - older gentleman
}

CHANNEL_DEFAULT_VOICE = {
    "under-the-baobab":         ELEVENLABS_VOICES["griot_kofi"],
    "ai-catalyst":              ELEVENLABS_VOICES["boubacar"],
    "first-generation-money":   ELEVENLABS_VOICES["hunter"],
}
```

## Fallback

If ElevenLabs unavailable: Kai TTS via `kie_media` skill.
- Under the Baobab: lowest pace setting, warmest available male voice
- AI Catalyst: most neutral available voice, pace -10%
- First Generation Money: neutral calm voice, pace -5%
