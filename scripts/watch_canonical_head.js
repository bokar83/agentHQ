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
  if (process.env.TELEGRAM_BOT_TOKEN && process.env.OWNER_TELEGRAM_CHAT_ID) {
    return {
      token: process.env.TELEGRAM_BOT_TOKEN,
      chat: process.env.OWNER_TELEGRAM_CHAT_ID,
    };
  }
  try {
    const raw = fs.readFileSync(envPath, 'utf8');
    const cfg = {};
    for (const line of raw.split(/\r?\n/)) {
      const m = line.match(/^(\w+)=(.*)$/);
      if (m) cfg[m[1]] = m[2].replace(/^["']|["']$/g, '');
    }
    return {
      token: cfg.TELEGRAM_BOT_TOKEN || cfg.ORCHESTRATOR_TELEGRAM_BOT_TOKEN,
      chat: cfg.OWNER_TELEGRAM_CHAT_ID,
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

function postTelegram(text) {
  if (!env.token || !env.chat) {
    process.stderr.write(`[watcher] no Telegram config — would post:\n${text}\n`);
    return;
  }
  const payload = JSON.stringify({
    chat_id: env.chat,
    text,
    parse_mode: 'Markdown',
    disable_web_page_preview: true,
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
  if (prev && prev.sha === sha && (now - prev.ts) < DEDUP_WINDOW_MS) return;
  const oldSha = prev ? prev.sha : '(unknown)';
  lastSeen.set(file, { sha, ts: now });
  if (!prev) return; // first read = baseline, not a change

  const msg = [
    '*HEAD FLIP DETECTED*',
    `*Tree:* ${label}`,
    `*File:* \`${file}\``,
    `*Old:* \`${oldSha}\``,
    `*New:* \`${sha}\``,
    `*Time:* ${new Date(now).toISOString()}`,
    '',
    '*Recent reflog:*',
    '```',
    reflogTail(),
    '```',
    '',
    '*Worktrees:*',
    '```',
    worktreeList(),
    '```',
    '',
    '_Recover (paste in canonical):_',
    '```',
    `cd "${CANONICAL_ROOT}"`,
    'git reflog -5  # pick the SHA before the flip',
    'git reset --hard <sha>',
    '```',
  ].join('\n');

  postTelegram(msg);
  process.stderr.write(`[watcher] HEAD flip on ${label} ${oldSha} -> ${sha}\n`);
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
}

main();
