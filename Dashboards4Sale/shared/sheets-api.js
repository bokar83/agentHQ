import { execFileSync } from 'child_process';

// Pre-flight: fail fast with a clear message if gws is not on PATH.
try {
  execFileSync('gws', ['--version'], { encoding: 'utf8', stdio: 'pipe' });
} catch {
  throw new Error('gws CLI not found on PATH. Ensure gws is installed and accessible in your shell.');
}

// Calls the gws CLI using execFileSync (no shell — injection-safe).
// args: array of strings, e.g. ['sheets', 'spreadsheets', 'create']
// params: object passed as --params JSON
// body: object passed as --json JSON (optional)
function gws(args, params = {}, body = null) {
  const argv = [...args, '--params', JSON.stringify(params)];
  if (body) argv.push('--json', JSON.stringify(body));
  try {
    const result = execFileSync('gws', argv, { encoding: 'utf8', stdio: ['ignore', 'pipe', 'pipe'] });
    return JSON.parse(result);
  } catch (err) {
    const detail = err.stderr?.trim() || err.message;
    throw new Error(`gws ${args.join(' ')} failed: ${detail}`);
  }
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
