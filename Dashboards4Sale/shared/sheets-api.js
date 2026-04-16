import { spawnSync } from 'child_process';
import { createRequire } from 'module';
import { resolve, join } from 'path';
import { existsSync } from 'fs';

// On Windows, gws is a Node.js script wrapped in a .cmd shim.
// Running gws.cmd passes args through cmd.exe which mangles JSON quotes.
// Instead we invoke the underlying Node.js script directly so argument
// passing goes through the V8/Node IPC layer with no shell quoting issues.
//
// On non-Windows, invoke the plain 'gws' binary directly.
function resolveGwsBin() {
  if (process.platform !== 'win32') return { bin: 'gws', args: [] };

  // Walk common npm global bin locations to find run-gws.js
  const candidates = [
    join(process.env.APPDATA || '', 'npm', 'node_modules', '@googleworkspace', 'cli', 'run-gws.js'),
    join(process.env.LOCALAPPDATA || '', 'npm', 'node_modules', '@googleworkspace', 'cli', 'run-gws.js'),
  ];
  for (const p of candidates) {
    if (existsSync(p)) return { bin: process.execPath, args: [p] };
  }
  // Fallback: try gws.cmd through spawnSync with shell:true (may fail with nested quotes)
  return { bin: 'gws.cmd', args: [] };
}

const { bin: GWS_BIN, args: GWS_ARGS } = resolveGwsBin();

// Pre-flight: fail fast with a clear message if gws is not available.
const preflight = spawnSync(GWS_BIN, [...GWS_ARGS, '--version'],
  { encoding: 'utf8', stdio: 'pipe' });
if (preflight.status !== 0 || preflight.error) {
  throw new Error('gws CLI not found. Ensure gws is installed: npm i -g @googleworkspace/cli');
}

// Calls the gws CLI using spawnSync (injection-safe, no shell required).
// args: array of strings, e.g. ['sheets', 'spreadsheets', 'create']
// params: object passed as --params JSON
// body: object passed as --json JSON (optional)
function gws(args, params = {}, body = null) {
  const argv = [...GWS_ARGS, ...args, '--params', JSON.stringify(params)];
  if (body) argv.push('--json', JSON.stringify(body));
  const result = spawnSync(GWS_BIN, argv,
    { encoding: 'utf8', stdio: ['ignore', 'pipe', 'pipe'] });
  if (result.status !== 0 || result.error) {
    const detail = result.stderr?.trim() || result.error?.message || 'unknown error';
    throw new Error(`gws ${args.join(' ')} failed: ${detail}`);
  }
  return JSON.parse(result.stdout);
}

export function createSpreadsheet(title) {
  return gws(['sheets', 'spreadsheets', 'create'], {}, { properties: { title } });
}

export function batchUpdate(spreadsheetId, requests) {
  return gws(
    ['sheets', 'spreadsheets', 'batchUpdate'],
    { spreadsheetId },
    { requests }
  );
}

export function getSpreadsheet(spreadsheetId) {
  return gws(['sheets', 'spreadsheets', 'get'], { spreadsheetId });
}

export function shareViewOnly(fileId) {
  return gws(
    ['drive', 'permissions', 'create'],
    { fileId, sendNotificationEmail: false },
    { role: 'reader', type: 'anyone' }
  );
}
