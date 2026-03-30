# Check-In Trigger Reference

Full logic for when and how check-ins fire in boubacar-skill-creator.

## Rules

1. Max ONE check-in per step — if multiple triggers fire simultaneously, use the priority order below
2. Check-ins are one question only — wait for response before continuing
3. Never interrupt mid-draft — check-ins fire between steps, not inside them
4. All check-in responses may trigger a learning candidate — note them for the reflector pass

## Trigger Table (Priority Order)

| Priority | Trigger Condition | Check-In Message | When It Fires |
|----------|------------------|-----------------|---------------|
| 1 | Domain = voice-inject AND tone not stated by user | "This skill touches your [domain] domain. Should I write it in your leGriot voice, or keep it technical?" | Step 3 (domain classification) |
| 2 | Stored instinct contradicted by current approach | "You usually [instinct observation]. This skill does [different thing] — intentional?" | Step 4 (during draft) |
| 3 | First draft written | "First draft done. Does this sound like you, or does it feel generic?" | End of Step 4 |
| 4 | session-tracker.json shows skills_since_reflection >= 3 | "Quick check-in — I haven't done a reflection pass in a while. Let me surface what I've learned about how you work. Still accurate?" | Step 1 (pre-session brief) |
| 5 | Before packaging | "Before I package: anything you'd want future-you to know when using this skill?" | Step 8 (before package command) |

## What NOT to Do

- Do not fire check-in #3 if check-in #1 already fired in the same step
- Do not fire check-in #4 if the user just completed a reflection pass this session
- Do not combine check-ins into one message with multiple questions
- Do not use check-ins as a way to stall — if the answer is obvious from context, skip the check-in

## After a Check-In Response

Always process the response before continuing. If the response:
- Confirms current direction → continue
- Redirects → adjust draft accordingly, note as candidate learning for reflector
- Reveals a new preference not in instincts.json → note explicitly for reflector pass
