# FIXTURE: v2-6 hardcoded secret pattern
# Scan should flag: config.py:4 — password= hardcoded string — secret committed to history
# Scan should flag: config.py:5 — api_key= hardcoded string — secret committed to history

password = "Sup3rS3cretPass!"  # pragma: allowlist secret
api_key = "sk-abcdef1234567890abcdef1234567890"  # pragma: allowlist secret
token = "ghp_FAKEGITHUBTOKEN1234567890abcdef"  # pragma: allowlist secret
