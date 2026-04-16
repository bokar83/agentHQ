import { execFileSync } from 'child_process';

// Calls the gws CLI using execFileSync (no shell — injection-safe).
// args: array of strings, e.g. ['sheets', 'spreadsheets', 'create']
// params: object passed as --params JSON
// body: object passed as --json JSON (optional)
function gws(args, params = {}, body = null) {
  const argv = [...args, '--params', JSON.stringify(params)];
  if (body) argv.push('--json', JSON.stringify(body));
  const result = execFileSync('gws', argv, { encoding: 'utf8' });
  return JSON.parse(result);
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
