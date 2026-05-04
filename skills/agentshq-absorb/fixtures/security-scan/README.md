# Security Scan Fixtures

Test cases for the Security Scan Gate in `skills/agentshq-absorb/SKILL.md`.

## Structure

```text
security-scan/
  clean/                          → should produce STATIC-CLEAN
    package.json                  → legit deps, no lifecycle shell-outs
    requirements.txt              → legit deps, no typosquats
    main.py                       → reads env var safely, no exfil

  malicious/
    v1-1-postinstall-shellout/
      package.json                → postinstall: curl | bash → BLOCKED
    v1-2-base64-exec/
      index.js                    → documented pattern only (hook blocks live eval)
      main.py                     → base64.b64decode + subprocess.run → BLOCKED
    v2-3-typosquat/
      requirements.txt            → requets, numppy, flaskk → SUSPICIOUS
      package.json                → expresss, lodahs, axois → SUSPICIOUS
    v2-4-exfil-endpoint/
      exfil.py                    → requests.post to hardcoded IP → SUSPICIOUS
    v2-5-env-harvest/
      harvest.py                  → os.environ dict → POST to external URL → SUSPICIOUS
    v2-6-hardcoded-secret/
      config.py                   → password/api_key/token literals → SUSPICIOUS
    v3-7-astroturfed/
      README.md                   → GitHub API procedure (no static file; live metadata required) → SUSPICIOUS
```

## How to use

When scanning a repo, mentally run each malicious fixture against the pattern table. Every malicious file must trigger its labeled pattern. The clean files must produce zero flags.

If a pattern fires on the clean files → false positive : tighten the pattern.
If a malicious file produces no flags → missed detection : widen the pattern.
