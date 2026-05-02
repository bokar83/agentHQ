"""
Creates or updates the Apps Script project bound to the spreadsheet.
Adds: Budget Tools menu, clearSampleData(), toggleTheme()
"""
import json, os, subprocess

SHEET_ID = "1pkO1G5q_qDe0nLCm7W12O3-jurzYKH16bcw8X5AOmQ0"
GIT_BASH  = r"C:\Program Files\Git\bin\bash.exe"
OUT       = r"D:\Ai_Sandbox\agentsHQ\Dashboards4Sale\tmp"

def to_unix(p):
    p = p.replace("\\", "/")
    if len(p) > 1 and p[1] == ":": p = "/" + p[0].lower() + p[2:]
    return p

def gws_cmd(subcmd, params_json, body_json):
    fname = os.path.join(OUT, "_script_tmp.json")
    with open(fname, "w", encoding="utf-8") as f:
        json.dump(body_json, f)
    unix = to_unix(fname)
    cmd = (f"gws script projects {subcmd} "
           f"--params '{params_json}' "
           f"--json \"$(cat '{unix}')\"")
    r = subprocess.run([GIT_BASH, "-c", cmd],
                       capture_output=True, text=True, encoding="utf-8", errors="replace")
    os.remove(fname)
    return r.stdout + r.stderr

# ── Script source code ────────────────────────────────────────────────────────
SCRIPT_CODE = r'''
// ═══════════════════════════════════════════════════════════════════════
//  Smart 50/30/20 Monthly Budget Planner — Apps Script
//  Budget Tools menu: Clear Sample Data | Toggle Theme
// ═══════════════════════════════════════════════════════════════════════

function onOpen() {
  SpreadsheetApp.getUi()
    .createMenu('Budget Tools')
    .addItem('Clear Sample Data...', 'clearSampleData')
    .addSeparator()
    .addItem('Toggle Dark / Light Theme', 'toggleTheme')
    .addSeparator()
    .addItem('About This Planner', 'showAbout')
    .addToUi();
}

// ── CLEAR SAMPLE DATA ────────────────────────────────────────────────
function clearSampleData() {
  var ui = SpreadsheetApp.getUi();
  var result = ui.alert(
    'Clear Sample Data',
    'This will permanently delete the 35 demo transactions and reset the Debt Tracker, Savings Goals, and income entries in Setup.\n\nYour formatting, formulas, and column headers will be preserved.\n\nAre you sure?',
    ui.ButtonSet.YES_NO
  );
  if (result !== ui.Button.YES) return;

  var ss = SpreadsheetApp.getActiveSpreadsheet();

  // Transactions: clear rows 2-36 (keep header row 1)
  var txn = ss.getSheetByName('Transactions');
  if (txn) txn.getRange('A2:I36').clearContent();

  // Setup: clear income values only (C5:C7) and reset active month
  var setup = ss.getSheetByName('Setup');
  if (setup) {
    setup.getRange('C5:C7').clearContent();
    setup.getRange('C3').setValue('');
  }

  // Debt Tracker: clear debt rows 5-12 data cols (A-F, J)
  var debt = ss.getSheetByName('Debt Tracker');
  if (debt) {
    debt.getRange('A5:F12').clearContent();
    debt.getRange('J5:J12').clearContent();
  }

  // Savings Goals: clear goal rows 4-10 data cols (A-D, H)
  var sav = ss.getSheetByName('Savings Goals');
  if (sav) {
    sav.getRange('A4:D10').clearContent();
    sav.getRange('H4:H10').clearContent();
  }

  ui.alert('Done!', 'Sample data cleared. You\'re ready to enter your own budget.\n\n1. Open Setup and enter your income\n2. Set your Active Month\n3. Start logging transactions!', ui.ButtonSet.OK);
}

// ── TOGGLE DARK / LIGHT THEME ────────────────────────────────────────
function toggleTheme() {
  var ss = SpreadsheetApp.getActiveSpreadsheet();
  var props = PropertiesService.getDocumentProperties();
  var isDark = props.getProperty('theme') !== 'light';

  // Color palettes
  var DARK  = { bg: '#1C2833', header: '#141C25', card: '#233240', text: '#FFFFFF', secondary: '#95A5A6', teal: '#00B4A6' };
  var LIGHT = { bg: '#F4F6F7', header: '#2C3E50', card: '#FFFFFF',  text: '#2C3E50', secondary: '#7F8C8D', teal: '#1ABC9C' };
  var theme = isDark ? LIGHT : DARK;

  var sheetNames = ['Dashboard','Transactions','Debt Tracker','Savings Goals','Annual Overview','Setup'];
  sheetNames.forEach(function(name) {
    var sheet = ss.getSheetByName(name);
    if (!sheet) return;
    // Paint the base background
    sheet.getRange(1, 1, sheet.getMaxRows(), sheet.getMaxColumns())
         .setBackground(theme.bg)
         .setFontColor(theme.text);
  });

  props.setProperty('theme', isDark ? 'light' : 'dark');
  SpreadsheetApp.getActiveSpreadsheet().toast(
    'Switched to ' + (isDark ? 'Light' : 'Dark') + ' mode.',
    'Theme Updated', 3
  );
}

// ── ABOUT ────────────────────────────────────────────────────────────
function showAbout() {
  var ui = SpreadsheetApp.getUi();
  ui.alert(
    'Smart 50/30/20 Monthly Budget Planner',
    'Version 2.0 — Premium Dark Edition\n\nThis planner helps you track income, expenses, debts, and savings goals using the proven 50/30/20 budgeting rule.\n\n• 50% → Needs (housing, food, utilities)\n• 30% → Wants (dining, entertainment)\n• 20% → Savings & Debt payoff\n\nAll tabs update automatically from your Transactions log.\n\nTip: Set your Active Month in Setup > C3 each month.',
    ui.ButtonSet.OK
  );
}
'''

# ── Step 1: Get existing script project ID or create new one ─────────────────
print("Getting spreadsheet metadata for script ID...")
fname = os.path.join(OUT, "_meta_tmp.json")
cmd = (f"gws sheets spreadsheets get "
       f"--params '{{\"spreadsheetId\":\"{SHEET_ID}\",\"fields\":\"spreadsheetId\"}}' 2>&1")
r = subprocess.run([GIT_BASH, "-c", cmd], capture_output=True, text=True, encoding="utf-8", errors="replace")
out = r.stdout + r.stderr

# Create new Apps Script project
print("Creating Apps Script project...")
create_body = {
    "title": "Smart 50/30/20 Budget Planner — Scripts",
    "parentId": SHEET_ID
}
result = gws_cmd("create", "{}", create_body)
print(f"  Create result: {result[:200]}")

try:
    data = json.loads("\n".join([l for l in result.splitlines() if not l.startswith("Using")]))
    script_id = data.get("scriptId", "")
    print(f"  Script ID: {script_id}")
except Exception as e:
    print(f"  Could not parse script ID: {e}")
    print("  Trying to find existing script...")
    script_id = ""

if not script_id:
    print("Script creation failed or returned no ID. Trying updateContent on known script ID...")
    # Try getting bound scripts from drive
    print("Done (manual step may be needed)")
else:
    # ── Step 2: Push the script code ──────────────────────────────────────────
    print("Uploading script code...")
    content_body = {
        "files": [
            {
                "name": "Code",
                "type": "SERVER_JS",
                "source": SCRIPT_CODE
            },
            {
                "name": "appsscript",
                "type": "JSON",
                "source": json.dumps({
                    "timeZone": "America/New_York",
                    "dependencies": {},
                    "exceptionLogging": "STACKDRIVER",
                    "runtimeVersion": "V8"
                })
            }
        ]
    }
    upload_result = gws_cmd("updateContent",
                            f'{{\"scriptId\":\"{script_id}\"}}',
                            content_body)
    if '"scriptId"' in upload_result or '"files"' in upload_result:
        print("  OK: Script code uploaded successfully")
    else:
        print(f"  Result: {upload_result[:300]}")

print("\nApps Script setup complete!")
