# GWS Personal Creds — One-Week Follow-Up Check

## Status

This is an automated reminder fired by a scheduled remote agent on 2026-05-06, one week after an `invalid_client` credential issue was originally logged for `secrets/gws-oauth-credentials.json`.

> **Note:** The source handoff doc (`docs/handoff/2026-04-29-personal-gws-creds-broken.md`) was not found in the repository at the time this follow-up was generated. It may have been archived, never committed, or the issue was tracked informally. The reminder is preserved here regardless so the credential status gets a conscious check-in.

---

## Original issue

As of 2026-04-29, the personal Google Workspace OAuth credentials stored at
`secrets/gws-oauth-credentials.json` were returning an `invalid_client` error when the token
refresh flow was triggered. This typically indicates the OAuth client ID / secret in that file
no longer matches a valid client registered in Google Cloud Console — either the credentials
were rotated, the project was deleted, or the OAuth consent screen was placed back into
"testing" mode with an expired token that cannot be silently refreshed.
See original handoff: `docs/handoff/2026-04-29-personal-gws-creds-broken.md` *(not found at follow-up time — check archive)*.

---

## What this agent did

This agent ran remotely without access to the local `secrets/` directory and therefore cannot
inspect or test the credentials file directly.

**Git activity observed** (`git log --oneline --since=2026-04-29 -- secrets/ docs/roadmap/future-enhancements.md docs/handoff/`):

No commits were found that touched `secrets/`, `docs/roadmap/future-enhancements.md` for a GWS
section, or a GWS-credentials handoff doc. The only recent commits touching `docs/handoff/` are
unrelated session handoffs and the 2026-05-05 archive chore. This means the credential issue has
not been resolved (or at least not documented) in the past week.

---

## Verify command for Boubacar to run locally

Run this from the repo root to test the personal account token:

```bash
python -c "from orchestrator.tools import _gws_request; print(_gws_request('get', 'https://gmail.googleapis.com/gmail/v1/users/me/profile'))"
```

To also test the CW account, pass the `account` kwarg:

```bash
python -c "from orchestrator.tools import _gws_request; print(_gws_request('get', 'https://gmail.googleapis.com/gmail/v1/users/me/profile', account='boubacar@catalystworks.consulting'))"
```

A successful response returns a JSON profile object. An `invalid_client` or `Token has been
expired or revoked` error confirms the issue is still live.

---

## If still broken

Check `docs/roadmap/future-enhancements.md` under the section **"Personal Gmail OAuth Credentials
Refresh"** for documented fix steps.

> **Note:** That section was not present in `future-enhancements.md` at follow-up time. If it was
> never written, the standard fix path is:
> 1. Go to Google Cloud Console → APIs & Services → Credentials.
> 2. Confirm the OAuth 2.0 client ID matching `secrets/gws-oauth-credentials.json` still exists and is not disabled.
> 3. If the consent screen is in "testing" mode and the test-user token has expired (> 7 days), re-run the OAuth flow locally: `python scripts/refresh_gws_token.py` (or equivalent).
> 4. If the client was deleted, create a new OAuth client, download the credentials JSON, and replace `secrets/gws-oauth-credentials.json`. Then re-run the auth flow.
> 5. Commit the updated token file (not the credentials JSON — that should stay in `.gitignore`).

---

## Close-out

Once the credentials are confirmed working locally:

1. Delete this followup doc (`docs/handoff/2026-05-06-gws-creds-followup.md`).
2. If a "Personal Gmail OAuth Credentials Refresh" entry exists in `docs/roadmap/future-enhancements.md`, remove it.
3. Commit the cleanup with a short message like `chore: gws creds verified and reminders cleared`.
