// ═══════════════════════════════════════════════════════════════════════
//  Smart 50/30/20 Monthly Budget Planner — Apps Script
//  INSTALL: Extensions > Apps Script > paste this code > Save > Run onOpen
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
    'This will permanently delete the 35 demo transactions and reset the Debt Tracker, Savings Goals, and income entries in Setup.\n\nYour formatting, formulas, and column headers are preserved.\n\nAre you sure?',
    ui.ButtonSet.YES_NO
  );
  if (result !== ui.Button.YES) return;

  var ss = SpreadsheetApp.getActiveSpreadsheet();

  var txn = ss.getSheetByName('Transactions');
  if (txn) txn.getRange('A2:I1000').clearContent();

  var setup = ss.getSheetByName('Setup');
  if (setup) {
    setup.getRange('C5:C7').clearContent();
    setup.getRange('C3').setValue('');
  }

  var debt = ss.getSheetByName('Debt Tracker');
  if (debt) {
    debt.getRange('A5:F12').clearContent();
    debt.getRange('J5:J12').clearContent();
  }

  var sav = ss.getSheetByName('Savings Goals');
  if (sav) {
    sav.getRange('A4:D10').clearContent();
    sav.getRange('H4:H10').clearContent();
  }

  ui.alert('Done!',
    "Sample data cleared. Ready for your real budget!\n\n" +
    "1. Open Setup tab and enter your income\n" +
    "2. Set your Active Month in cell C3\n" +
    "3. Start logging your transactions!\n\n" +
    "Tip: The 50/30/20 budgets in Setup update automatically.",
    ui.ButtonSet.OK);
}

// ── TOGGLE DARK / LIGHT THEME ────────────────────────────────────────
function toggleTheme() {
  var ss   = SpreadsheetApp.getActiveSpreadsheet();
  var props = PropertiesService.getDocumentProperties();
  var isDark = props.getProperty('theme') !== 'light';

  var DARK  = { bg: '#1C2833', text: '#FFFFFF', header: '#141C25' };
  var LIGHT = { bg: '#FAFAFA', text: '#1C2833', header: '#2C3E50' };
  var theme = isDark ? LIGHT : DARK;

  var sheetNames = ['Dashboard','Transactions','Debt Tracker','Savings Goals','Annual Overview','Setup'];
  sheetNames.forEach(function(name) {
    var sheet = ss.getSheetByName(name);
    if (!sheet) return;
    sheet.getRange(1, 1, Math.min(sheet.getMaxRows(), 300), sheet.getMaxColumns())
         .setBackground(theme.bg)
         .setFontColor(theme.text);
  });

  props.setProperty('theme', isDark ? 'light' : 'dark');
  ss.toast('Switched to ' + (isDark ? 'Light' : 'Dark') + ' mode.', 'Theme Updated', 3);
}

// ── ABOUT ────────────────────────────────────────────────────────────
function showAbout() {
  SpreadsheetApp.getUi().alert(
    'Smart 50/30/20 Monthly Budget Planner',
    'Version 2.0  —  Premium Dark Edition\n\n' +
    'Built on the 50/30/20 rule:\n' +
    '  • 50% → Needs (housing, food, bills)\n' +
    '  • 30% → Wants (dining, fun, subscriptions)\n' +
    '  • 20% → Savings & debt payoff\n\n' +
    'All 6 tabs auto-update from your Transactions log.\n\n' +
    'Tip: Change Setup > C3 each month to see that month\'s dashboard.',
    SpreadsheetApp.getUi().ButtonSet.OK
  );
}
