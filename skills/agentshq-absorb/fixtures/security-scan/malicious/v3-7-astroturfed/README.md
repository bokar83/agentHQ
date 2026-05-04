# Fixture: v3-7 Astroturfed Repo

This pattern cannot be a static file. It requires live GitHub API metadata.

## What to check (via GitHub MCP get_repository or API)

```
GET https://api.github.com/repos/<owner>/<repo>

Fields:
  created_at:        "2026-04-20T10:00:00Z"   ← repo age
  stargazers_count:  312                        ← star count
  forks_count:       28                         ← fork count
```

## Trigger conditions

SUSPICIOUS (high confidence): age ≤ 30 days AND stars ≥ 50
SUSPICIOUS (lower confidence): age ≤ 30 days AND forks ≥ 20

## Example flag output

```
SECURITY SCAN : some-owner-new-repo
=====================================
Status: SUSPICIOUS
Flags:
  - GitHub metadata, v3-7 astroturfed trust signal: created_at: 2026-04-20 (14 days old), stars: 312, forks: 28
Recommendation: PROCEED-WITH-CAUTION
Override: [ ] Boubacar annotated: "<reason>" on <date>
```

## Known legitimate exception

Viral tools (e.g. a famous person's repo going public) can hit 50 stars in < 30 days legitimately.
The v3-7 flag is SUSPICIOUS (not BLOCKED) precisely because of this. Boubacar makes the final call.
