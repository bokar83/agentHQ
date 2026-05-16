#!/usr/bin/env node
// check_cwd_canonical.js — Layer B of session-collision prevention.
//
// Claude Code PreToolUse hook. Reads JSON on stdin per the hook spec.
// Blocks any write-tool whose effective target is the canonical agentsHQ
// working tree (D:/Ai_Sandbox/agentsHQ) without going through a worktree.
//
// Repo canonical copy: scripts/check_cwd_canonical.js. This file is
// installed-from-repo; treat the repo version as source of truth.
//
// Decision tree:
//  1. Read tool_name + tool_input from stdin JSON.
//  2. File tools (Edit/Write/MultiEdit/NotebookEdit):
//       - file_path outside canonical OR under a worktree dir → allow.
//       - file_path inside canonical and not under a worktree → block.
//  3. Bash:
//       - Inline `CLAUDE_ALLOW_CANONICAL_WRITE=1 ...` prefix → allow.
//       - Leading `cd <path>` or `git -C <path>` to non-canonical → allow.
//       - Leading `cd <canonical>` → block.
//       - Bare git mutating command (checkout/switch/reset/rebase/merge/
//         pull/cherry-pick/stash) → fall through to cwd check.
//       - Anything else → allow (file writes via redirection unparseable;
//         primary collision pattern is HEAD-flipping, not stray writes).
//  4. Cwd fallback (file tool without path arg, or bare-git Bash):
//       - cwd is canonical root → block.
//       - cwd is a worktree → allow.
//
// Bypass: CLAUDE_ALLOW_CANONICAL_WRITE=1 in process env OR as Bash
// command prefix (env doesn't propagate across CC tool calls).
//
// Fail-open on any detection error.

const { execFileSync } = require('child_process');

const CANONICAL_ROOT = (process.env.AGENTSHQ_CANONICAL_ROOT
  || 'D:/Ai_Sandbox/agentsHQ').replace(/\\/g, '/').replace(/\/+$/, '');

function readStdin() {
  return new Promise(resolve => {
    let buf = '';
    process.stdin.setEncoding('utf8');
    process.stdin.on('data', chunk => { buf += chunk; });
    process.stdin.on('end', () => resolve(buf));
    setTimeout(() => resolve(buf), 1500);
  });
}

function gitDirInfo(cwd) {
  try {
    const dir = execFileSync('git', ['-C', cwd, 'rev-parse', '--git-dir'], { encoding: 'utf8', timeout: 2000 }).trim();
    const common = execFileSync('git', ['-C', cwd, 'rev-parse', '--git-common-dir'], { encoding: 'utf8', timeout: 2000 }).trim();
    return { dir, common };
  } catch (e) { return null; }
}

function norm(p) { return (p || '').replace(/\\/g, '/').replace(/\/+$/, ''); }
function isInsideCanonical(p) {
  const n = norm(p).toLowerCase();
  const r = CANONICAL_ROOT.toLowerCase();
  return n === r || n.startsWith(r + '/');
}
function isCanonicalAndNotWorktree(p) {
  const n = norm(p).toLowerCase();
  const r = CANONICAL_ROOT.toLowerCase();
  if (!(n === r || n.startsWith(r + '/'))) return false;
  if (n.startsWith(r + '/.claude/worktrees/')) return false;
  return true;
}

function allow() { process.stdout.write(''); process.exit(0); }
function block(reason) { process.stdout.write(JSON.stringify({ decision: 'block', reason })); process.exit(0); }

function buildReason(target, kind) {
  const sessionId = (process.env.CLAUDE_SESSION_ID || process.env.ANTIGRAVITY_SESSION_ID || `pid-${process.pid}`).slice(0, 12);
  // 2026-05-16: worktrees moved from D:/tmp/wt-X to D:/Ai_Sandbox/agentsHQ-worktrees/wt-X.
  // D:/tmp/ broke `claude --resume` after reboot because CC session jsonl files
  // embed cwd. Sibling-of-canonical path survives reboot and keeps work under
  // agentsHQ tree. Old D:/tmp/wt-X paths still resolve via NTFS junctions from
  // the 2026-05-16 migration; new worktrees go here.
  const wtPath = `D:/Ai_Sandbox/agentsHQ-worktrees/wt-${sessionId}`;
  return [
    `BLOCKED: ${kind} would mutate the canonical agentsHQ working tree.`,
    '',
    `Canonical root: ${CANONICAL_ROOT}`,
    `Offending arg:  ${target}`,
    '',
    "Concurrent sessions sharing this tree have flipped each other's",
    'branches 5+ times today, losing work. Use a worktree:',
    '',
    '```',
    `cd "${CANONICAL_ROOT}"`,
    'git fetch origin main',
    `git worktree add "${wtPath}" -b fix/<your-branch> origin/main`,
    `cd "${wtPath}"`,
    '```',
    '',
    'Then retry from the new worktree. Inline per-call bypass:',
    'prefix Bash with CLAUDE_ALLOW_CANONICAL_WRITE=1 (env does not',
    'propagate across Claude Code tool calls).',
  ].join('\n');
}

async function main() {
  let payload = {};
  try {
    const raw = await readStdin();
    if (raw.trim()) payload = JSON.parse(raw);
  } catch (e) { return allow(); }

  const tool = payload.tool_name || '';
  const writeTools = new Set(['Edit', 'Write', 'MultiEdit', 'NotebookEdit', 'Bash']);
  if (!writeTools.has(tool)) return allow();

  const ti = payload.tool_input || {};
  if (process.env.CLAUDE_ALLOW_CANONICAL_WRITE === '1') return allow();

  // === File-tool branch ===
  if (tool !== 'Bash') {
    const target = norm(ti.file_path || ti.notebook_path || '');
    if (target) {
      if (isCanonicalAndNotWorktree(target)) {
        return block(buildReason(target, `${tool} target`));
      }
      return allow();
    }
    // No target arg → fall through to cwd check.
  }

  // === Bash branch ===
  if (tool === 'Bash') {
    const cmd = (ti.command || '').trim();

    if (/^CLAUDE_ALLOW_CANONICAL_WRITE=1\b/.test(cmd)) return allow();

    const cdMatch = cmd.match(/^cd\s+(?:"([^"]+)"|'([^']+)'|(\S+))/);
    if (cdMatch) {
      const cdTarget = norm(cdMatch[1] || cdMatch[2] || cdMatch[3] || '');
      if (isCanonicalAndNotWorktree(cdTarget)) {
        return block(buildReason(cdTarget, 'cd into canonical'));
      }
      return allow();
    }

    const gitCMatch = cmd.match(/^git\s+-C\s+(?:"([^"]+)"|'([^']+)'|(\S+))/);
    if (gitCMatch) {
      const target = norm(gitCMatch[1] || gitCMatch[2] || gitCMatch[3] || '');
      if (isCanonicalAndNotWorktree(target)) {
        return block(buildReason(target, 'git -C canonical'));
      }
      return allow();
    }

    const dangerousBareGit = /^(git\s+(checkout|switch|reset|rebase|merge|pull|cherry-pick|stash\s+pop|stash\s+apply)\b)/;
    if (!dangerousBareGit.test(cmd)) return allow();
    // dangerous bare-git → fall through to cwd check
  }

  // === Cwd fallback ===
  const cwd = norm(process.cwd());
  if (!isInsideCanonical(cwd)) return allow();
  const info = gitDirInfo(cwd);
  if (!info) return allow();
  const isCanonicalCwd = norm(info.dir) === norm(info.common);
  if (!isCanonicalCwd) return allow();
  return block(buildReason(cwd, 'shell-cwd canonical + dangerous git op'));
}

main().catch(() => allow());
