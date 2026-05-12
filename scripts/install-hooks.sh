#!/usr/bin/env bash
# Install agentsHQ git hooks into .git/hooks/. Idempotent. Run once per clone,
# or every time scripts/git-hooks/ changes (nsync calls this).
#
# Why hooks aren't symlinked: Windows + Git Bash treat hook symlinks
# inconsistently. Copy is reliable across all platforms.

set -euo pipefail
REPO_ROOT="$(git rev-parse --show-toplevel)"
SRC="${REPO_ROOT}/scripts/git-hooks"
DST="${REPO_ROOT}/.git/hooks"

[ -d "$SRC" ] || { echo "install-hooks: no $SRC, aborting"; exit 1; }
[ -d "$DST" ] || { echo "install-hooks: no $DST, aborting"; exit 1; }

for hook in pre-checkout commit-msg; do
  if [ -f "${SRC}/${hook}" ]; then
    cp "${SRC}/${hook}" "${DST}/${hook}"
    chmod +x "${DST}/${hook}"
    echo "install-hooks: installed ${hook}"
  fi
done
echo "install-hooks: done"
