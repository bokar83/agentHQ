#!/usr/bin/env node
// watch_canonical_head.js — Layer A of session-collision detection.
//
// Watches D:/Ai_Sandbox/agentsHQ/.git/HEAD (and per-worktree HEADs) for
// mutation. On change, posts a Telegram alert with old SHA, new SHA,
// timestamp, current `git worktree list`, and any reflog hint about which
// session caused the flip.
//
// Why this exists: multiple Claude Code / Antigravity / Codex sessions
// sharing one working tree have been silently flipping each other's HEAD
// for ~90 min on 2026-05-12, losing work in flight. Prevention layers
// (hooks, locks, Postgres claims) keep missing vectors (libgit2, IDE writes,
// `git switch` bypass of pre-checkout). Detection-via-fs.watch catches
// every vector because the data already lives in .git/HEAD and .git/logs.
//
// Run mode: standalone daemon. `node scripts/watch_canonical_head.js`.
// On Windows, install as a scheduled task at user logon. The script
// holds no state across restarts; safe to kill and relaunch.
//
// Telegram credentials read from .env (TELEGRAM_BOT_TOKEN +
// OWNER_TELEGRAM_CHAT_ID). If missing, watcher logs to stderr instead of
// posting — never crashes on missing config.
//
// Dedup: fs.watch on Windows occasionally double-fires for one logical
// change. We dedup by (path + new SHA) within a 2s window.

const fs = require('fs');
const path = require('path');
const { execFileSync } = require('child_process');
const https = require('https');

const CANONICAL_ROOT = process.env.AGENTSHQ_CANONICAL_ROOT
  || 'D:/Ai_Sandbox/agentsHQ';
const GIT_DIR = path.join(CANONICAL_ROOT, '.git');
const HEAD_FILE = path.join(GIT_DIR, 'HEAD');
const WORKTREES_DIR = path.join(GIT_DIR, 'worktrees');
const DEDUP_WINDOW_MS = 2000;

// Telegram config from .env in repo root if env var not set.
function loadEnv() {
  const envPath = path.join(CANONICAL_ROOT, '.env');
  const fromEnv = {
    token: process.env.TELEGRAM_BOT_TOKEN || process.env.ORCHESTRATOR_TELEGRAM_BOT_TOKEN,
    chat: process.env.OWNER_TELEGRAM_CHAT_ID || process.env.TELEGRAM_CHAT_ID,
  };
  if (fromEnv.token && fromEnv.chat) return fromEnv;
  try {
    const raw = fs.readFileSync(envPath, 'utf8');
    const cfg = {};
    for (const line of raw.split(/\r?\n/)) {
      const m = line.match(/^(\w+)=(.*)$/);
      if (m) cfg[m[1]] = m[2].replace(/^["']|["']$/g, '');
    }
    return {
      token: cfg.TELEGRAM_BOT_TOKEN || cfg.ORCHESTRATOR_TELEGRAM_BOT_TOKEN,
      chat: cfg.OWNER_TELEGRAM_CHAT_ID || cfg.TELEGRAM_CHAT_ID,
    };
  } catch (e) {
    return { token: null, chat: null };
  }
}

const env = loadEnv();

function readHead(file) {
  try {
    return fs.readFileSync(file, 'utf8').trim();
  } catch (e) {
    return null;
  }
}

function gitCmd(args) {
  try {
    return execFileSync('git', ['-C', CANONICAL_ROOT, ...args], {
      encoding: 'utf8',
      timeout: 5000,
    }).trim();
  } catch (e) {
    return '';
  }
}

function reflogTail() {
  const out = gitCmd(['reflog', '--date=iso', '-3']);
  return out || '(reflog unavailable)';
}

function worktreeList() {
  const out = gitCmd(['worktree', 'list']);
  return out || '(worktree list unavailable)';
}

// Telegram alert rule (2026-05-12): NEVER fire a pure-info alert.
// Every Telegram message MUST be actionable AND carry ✅/❌ inline
// buttons so Boubacar can decide in one tap. callback_data ≤64 bytes.
function postActionableAlert(text, oldSha, newSha) {
  if (!env.token || !env.chat) {
    process.stderr.write(`[watcher] no Telegram config — would post:\n${text}\n`);
    return;
  }
  // callback_data carries the SHA-to-restore. SHA is 40 chars + prefix
  // "rev:" = 44 chars, well under 64.
  const restoreCb = `canon_restore:${(oldSha || '').slice(0, 40)}`;
  const dismissCb = `canon_dismiss:${(newSha || '').slice(0, 40)}`;
  const payload = JSON.stringify({
    chat_id: env.chat,
    text,
    parse_mode: 'Markdown',
    disable_web_page_preview: true,
    reply_markup: {
      inline_keyboard: [[
        { text: '✅ Restore', callback_data: restoreCb },
        { text: '❌ Dismiss (intentional)', callback_data: dismissCb },
      ]],
    },
  });
  const req = https.request({
    hostname: 'api.telegram.org',
    path: `/bot${env.token}/sendMessage`,
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Content-Length': Buffer.byteLength(payload),
    },
  });
  req.on('error', err => {
    process.stderr.write(`[watcher] telegram error: ${err.message}\n`);
  });
  req.write(payload);
  req.end();
}

const lastSeen = new Map(); // path -> { sha, ts }
function recordChange(label, file) {
  const sha = readHead(file);
  if (!sha) return;
  const prev = lastSeen.get(file);
  const now = Date.now();
  // Suppress no-op writes: git rewrites HEAD on every pull / commit /
  // status / fetch even when content is unchanged (e.g. branch stays
  // `ref: refs/heads/main`). fs.watch fires on every touch. If content
  // is identical to last seen, this is NOT a flip — silent.
  // Branch-flip / detached-checkout / force-update changes content,
  // so those still trigger alerts. (Was: 2s dedup window only —
  // misfired on every legitimate git op after the window elapsed.)
  if (prev && prev.sha === sha) return;
  const oldSha = prev ? prev.sha : '(unknown)';
  lastSeen.set(file, { sha, ts: now });
  if (!prev) return; // first read = baseline, not a change

  // Only canonical HEAD flips are actionable. Worktree HEAD flips are
  // normal (every commit changes them); they are noise. Boubacar said
  // 2026-05-12: no Telegram alert unless action is required.
  if (label !== 'canonical') {
    process.stderr.write(`[watcher] worktree HEAD flip (silent): ${label} ${oldSha} -> ${sha}\n`);
    return;
  }

  process.stderr.write(`[watcher] CANONICAL HEAD flip: ${oldSha} -> ${sha}\n`);

  // Resolve the actual SHA for the restore button. HEAD file holds
  // either a sha (detached) or "ref: refs/heads/<branch>". For ref:
  // form, we resolve via reflog tail.
  let restoreSha = oldSha;
  if (restoreSha.startsWith('ref:')) {
    // The previous *commit* SHA is in reflog index 1.
    const reflogOne = gitCmd(['reflog', '-1', '--format=%H', `HEAD@{1}`]);
    if (reflogOne) restoreSha = reflogOne;
  }

  const msg = [
    '*CANONICAL HEAD FLIP — ACTION REQUIRED*',
    '',
    'Someone (or some session) just changed HEAD in the canonical',
    'agentsHQ working tree. This usually means another session is',
    'stepping on in-flight work.',
    '',
    `*Old:* \`${oldSha}\``,
    `*New:* \`${sha}\``,
    `*Time:* ${new Date(now).toISOString()}`,
    '',
    '*Reflog (last 3):*',
    '```',
    reflogTail(),
    '```',
    '',
    '✅ *Restore* = run `git reset --hard ' + restoreSha.slice(0, 12) + '` on canonical.',
    '❌ *Dismiss* = it was intentional; do nothing.',
  ].join('\n');

  postActionableAlert(msg, restoreSha, sha);
}

function watchFile(label, file) {
  if (!fs.existsSync(file)) {
    process.stderr.write(`[watcher] skip missing: ${file}\n`);
    return;
  }
  recordChange(label, file); // baseline
  fs.watch(file, { persistent: true }, () => recordChange(label, file));
  process.stderr.write(`[watcher] watching ${label}: ${file}\n`);
}

// Marker-consumer loop: orchestrator/handlers_approvals.py writes
// canon_restore/canon_dismiss markers to VPS at /app/data/canon_restore/.
// Watcher polls via SSH every 15s, executes the restore locally on the
// laptop's canonical tree, deletes the marker, posts a follow-up
// actionable confirmation (with ✅ done / ❌ undo buttons).
const VPS_HOST = process.env.AGENTSHQ_VPS_HOST || 'root@72.60.209.109';
const VPS_MARKER_DIR = '/root/agentsHQ/data/canon_restore';
const MARKER_POLL_MS = 15000;
const recentMarkers = new Set();

function postFollowupAlert(text, oldSha, newSha) {
  if (!env.token || !env.chat) return;
  // After a restore, the action is done. Follow-up message still gets a
  // single ❌ Undo button so Boubacar can rollback if the restore was
  // wrong (sole compliant pattern with the actionable-only rule).
  const undoCb = `canon_restore:${newSha.slice(0, 40)}`;
  const dismissCb = `canon_dismiss:done`;
  const payload = JSON.stringify({
    chat_id: env.chat,
    text,
    parse_mode: 'Markdown',
    disable_web_page_preview: true,
    reply_markup: {
      inline_keyboard: [[
        { text: '↩ Undo (re-restore to old HEAD)', callback_data: undoCb },
        { text: '✓ Acknowledge', callback_data: dismissCb },
      ]],
    },
  });
  const req = https.request({
    hostname: 'api.telegram.org',
    path: `/bot${env.token}/sendMessage`,
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Content-Length': Buffer.byteLength(payload),
    },
  });
  req.on('error', err => process.stderr.write(`[watcher] follow-up telegram err: ${err.message}\n`));
  req.write(payload);
  req.end();
}

function sshExec(cmd) {
  try {
    return execFileSync('ssh', ['-o', 'ConnectTimeout=5', '-o', 'BatchMode=yes', VPS_HOST, cmd], {
      encoding: 'utf8',
      timeout: 10000,
    });
  } catch (e) {
    return null;
  }
}

function pollMarkers() {
  // List markers, then fetch + delete each one we haven't already processed.
  const listing = sshExec(`ls -1 ${VPS_MARKER_DIR}/ 2>/dev/null || true`);
  if (!listing) return; // VPS unreachable or dir empty
  const names = listing.split(/\r?\n/).filter(n => n.endsWith('.json'));
  for (const name of names) {
    if (recentMarkers.has(name)) continue;
    recentMarkers.add(name);
    const raw = sshExec(`cat ${VPS_MARKER_DIR}/${name} && rm ${VPS_MARKER_DIR}/${name}`);
    if (!raw) continue;
    let marker;
    try { marker = JSON.parse(raw); } catch (e) {
      process.stderr.write(`[watcher] bad marker JSON ${name}: ${e.message}\n`);
      continue;
    }
    handleMarker(marker, name);
  }
  // Bound the in-memory dedup cache.
  if (recentMarkers.size > 500) {
    const arr = [...recentMarkers];
    recentMarkers.clear();
    for (const n of arr.slice(-100)) recentMarkers.add(n);
  }
}

function handleMarker(marker, name) {
  const { sha, decision } = marker;
  if (decision === 'dismiss') {
    process.stderr.write(`[watcher] marker dismiss ${sha.slice(0, 12)}\n`);
    return;
  }
  if (decision !== 'restore') {
    process.stderr.write(`[watcher] unknown decision in ${name}: ${decision}\n`);
    return;
  }
  // Resolve current HEAD on canonical BEFORE restoring (so Undo can roll
  // back to it). git reset --hard accepts a sha or ref.
  const currentSha = gitCmd(['rev-parse', 'HEAD']);
  process.stderr.write(`[watcher] restoring canonical from ${currentSha} -> ${sha}\n`);
  const out = gitCmd(['reset', '--hard', sha]);
  const newSha = gitCmd(['rev-parse', 'HEAD']);
  // Update the in-memory baseline so the upcoming fs.watch fire from
  // this very reset doesn't re-alert.
  lastSeen.set(HEAD_FILE, { sha: 'ref: refs/heads/' + (gitCmd(['rev-parse', '--abbrev-ref', 'HEAD']) || 'HEAD'), ts: Date.now() });
  postFollowupAlert(
    [
      '*RESTORE COMPLETE*',
      '',
      'Canonical HEAD reset to:',
      `\`${sha.slice(0, 12)}\``,
      '',
      'Result:',
      '```',
      (out || '(no output)').slice(0, 500),
      '```',
      '',
      `Now at: \`${newSha.slice(0, 12)}\``,
    ].join('\n'),
    sha,            // the sha we restored TO (acts as new HEAD for dedup)
    currentSha,     // sha we WERE on before reset (used for Undo)
  );
}

function main() {
  process.stderr.write(`[watcher] starting on ${CANONICAL_ROOT}\n`);
  watchFile('canonical', HEAD_FILE);

  // Discover and watch each worktree's HEAD too.
  try {
    const entries = fs.readdirSync(WORKTREES_DIR);
    for (const name of entries) {
      const wtHead = path.join(WORKTREES_DIR, name, 'HEAD');
      watchFile(`worktree:${name}`, wtHead);
    }
  } catch (e) {
    process.stderr.write(`[watcher] no worktrees dir: ${e.message}\n`);
  }

  // Re-scan every 60s for newly-added worktrees.
  setInterval(() => {
    try {
      const entries = fs.readdirSync(WORKTREES_DIR);
      for (const name of entries) {
        const wtHead = path.join(WORKTREES_DIR, name, 'HEAD');
        const label = `worktree:${name}`;
        if (!lastSeen.has(wtHead)) watchFile(label, wtHead);
      }
    } catch (e) { /* ignore */ }
  }, 60000);

  // Marker poll loop — consumes canon_restore / canon_dismiss markers
  // that the orchestrator writes when Boubacar taps a button.
  setInterval(pollMarkers, MARKER_POLL_MS);
  process.stderr.write(`[watcher] marker poll loop armed: ssh ${VPS_HOST} every ${MARKER_POLL_MS/1000}s\n`);
}

main();
