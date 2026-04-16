// budget-template-ar/build.js
import { createSpreadsheet, batchUpdate, getSpreadsheet, shareViewOnly }
  from '../shared/sheets-api.js';
import { COLORS } from '../shared/colors.js';
import { bgColor, textFormat, mergeCells, cardBorder,
         colWidth, freezeRows, dropdown, cfSingleColor }
  from '../shared/formatting.js';
import { TITLE, CATEGORIES, TYPES, SAMPLE_TRANSACTIONS, HEADERS,
         KPI_LABELS, BANNER_LABELS, SAVINGS_HEADERS, SAMPLE_GOALS,
         INCOME_TYPE, EXPENSE_TYPE, CURRENCY_FORMAT, PCT_FORMAT,
         DASHBOARD_LABELS }
  from './data.js';

const sheet = createSpreadsheet(TITLE);
const spreadsheetId = sheet.spreadsheetId;
console.log('Created:', spreadsheetId);
console.log('URL: https://docs.google.com/spreadsheets/d/' + spreadsheetId);

// Set Arabic locale (ar). Google Sheets API does not support ar_MA; ar is the accepted code.
batchUpdate(spreadsheetId, [{
  updateSpreadsheetProperties: {
    properties: { locale: 'ar' },
    fields: 'locale'
  }
}]);

// Get default sheet ID and rename to budget tab
const info = getSpreadsheet(spreadsheetId);
const budgetSheetId = info.sheets[0].properties.sheetId;

batchUpdate(spreadsheetId, [
  {
    updateSheetProperties: {
      properties: {
        sheetId: budgetSheetId,
        title: BANNER_LABELS.budget,
        tabColorStyle: { rgbColor: COLORS.terracotta }
      },
      fields: 'title,tabColorStyle'
    }
  },
  { addSheet: { properties: { title: BANNER_LABELS.savings,
      tabColorStyle: { rgbColor: COLORS.terracotta } } } },
  { addSheet: { properties: { title: BANNER_LABELS.dashboard,
      tabColorStyle: { rgbColor: COLORS.terracotta } } } },
]);

const updated = getSpreadsheet(spreadsheetId);
const savingsSheetId   = updated.sheets[1].properties.sheetId;
const dashboardSheetId = updated.sheets[2].properties.sheetId;

// Set right-to-left layout for all 3 tabs
batchUpdate(spreadsheetId, [
  { updateSheetProperties: {
      properties: { sheetId: budgetSheetId, rightToLeft: true },
      fields: 'rightToLeft' } },
  { updateSheetProperties: {
      properties: { sheetId: savingsSheetId, rightToLeft: true },
      fields: 'rightToLeft' } },
  { updateSheetProperties: {
      properties: { sheetId: dashboardSheetId, rightToLeft: true },
      fields: 'rightToLeft' } },
]);

// Parse 'DD/MM/YYYY' date string into a Sheets serial-number formula =DATE(y,m,d)
// so the Date column sorts and filters correctly.
function dateFormula(ddmmyyyy) {
  const [d, m, y] = ddmmyyyy.split('/');
  return `=DATE(${y},${Number(m)},${Number(d)})`;
}

function buildBudgetTab(spreadsheetId, sheetId) {
  // Row 1: banner, merged A1:F1 (6 cols to cover the full KPI row), terracotta bg, white bold 12pt
  batchUpdate(spreadsheetId, [
    mergeCells(sheetId, 0, 1, 0, 6),
    bgColor(sheetId, 0, 1, 0, 6, COLORS.terracotta),
    textFormat(sheetId, 0, 1, 0, 6, { bold: true, fontSize: 12, color: COLORS.white }),
    {
      updateCells: {
        range: { sheetId, startRowIndex: 0, endRowIndex: 1,
                 startColumnIndex: 0, endColumnIndex: 1 },
        rows: [{ values: [{ userEnteredValue: { stringValue: BANNER_LABELS.budget } }] }],
        fields: 'userEnteredValue'
      }
    }
  ]);

  // Row 2: KPI cells: A2 label, B2 Income value, C2 label, D2 Spent value,
  //                     E2 label, F2 Remaining value
  batchUpdate(spreadsheetId, [{
    updateCells: {
      range: { sheetId, startRowIndex: 1, endRowIndex: 2,
               startColumnIndex: 0, endColumnIndex: 6 },
      rows: [{
        values: [
          { userEnteredValue: { stringValue: KPI_LABELS.income },
            userEnteredFormat: { textFormat: { fontSize: 8, foregroundColor: COLORS.muted } } },
          { userEnteredValue: { formulaValue: `=SUMIF(D5:D54,"${INCOME_TYPE}",E5:E54)` },
            userEnteredFormat: {
              numberFormat: { type: 'CURRENCY', pattern: CURRENCY_FORMAT },
              textFormat: { bold: true, fontSize: 14, foregroundColor: COLORS.terracotta }
            }
          },
          { userEnteredValue: { stringValue: KPI_LABELS.spent },
            userEnteredFormat: { textFormat: { fontSize: 8, foregroundColor: COLORS.muted } } },
          { userEnteredValue: { formulaValue: `=SUMIF(D5:D54,"${EXPENSE_TYPE}",E5:E54)` },
            userEnteredFormat: {
              numberFormat: { type: 'CURRENCY', pattern: CURRENCY_FORMAT },
              textFormat: { bold: true, fontSize: 14, foregroundColor: COLORS.coral }
            }
          },
          { userEnteredValue: { stringValue: KPI_LABELS.remaining },
            userEnteredFormat: { textFormat: { fontSize: 8, foregroundColor: COLORS.muted } } },
          { userEnteredValue: { formulaValue: '=B2-D2' },
            userEnteredFormat: {
              numberFormat: { type: 'CURRENCY', pattern: CURRENCY_FORMAT },
              textFormat: { bold: true, fontSize: 14, foregroundColor: COLORS.sage }
            }
          },
        ]
      }],
      fields: 'userEnteredValue,userEnteredFormat.numberFormat,userEnteredFormat.textFormat'
    }
  }]);

  // Row 4: column headers; cream bg (A:F), terracotta bold text (A:E only; F has no header)
  batchUpdate(spreadsheetId, [
    bgColor(sheetId, 3, 4, 0, 6, COLORS.cream),
    {
      updateCells: {
        range: { sheetId, startRowIndex: 3, endRowIndex: 4,
                 startColumnIndex: 0, endColumnIndex: 5 },
        rows: [{
          values: HEADERS.map(h => ({
            userEnteredValue: { stringValue: h },
            userEnteredFormat: { textFormat: { bold: true, fontSize: 10,
              foregroundColor: COLORS.terracotta } }
          }))
        }],
        fields: 'userEnteredValue,userEnteredFormat.textFormat'
      }
    },
    freezeRows(sheetId, 4),
  ]);

  // Column widths: A=100, B=200, C=160, D=100, E=110, F=110 (Remaining value)
  batchUpdate(spreadsheetId, [
    colWidth(sheetId, 0, 100), colWidth(sheetId, 1, 200),
    colWidth(sheetId, 2, 160), colWidth(sheetId, 3, 100),
    colWidth(sheetId, 4, 110), colWidth(sheetId, 5, 110),
  ]);

  // Sample data rows 5-19 (indices 4-18)
  // Dates are written as =DATE(y,m,d) formulas so Sheets treats them as date serials
  // (sortable, filterable) rather than plain text strings.
  const dataRows = SAMPLE_TRANSACTIONS.map(([date, desc, cat, type, amt]) => ({
    values: [
      { userEnteredValue: { formulaValue: dateFormula(date) },
        userEnteredFormat: { numberFormat: { type: 'DATE', pattern: 'dd/mm/yyyy' } } },
      { userEnteredValue: { stringValue: desc } },
      { userEnteredValue: { stringValue: cat } },
      { userEnteredValue: { stringValue: type } },
      { userEnteredValue: { numberValue: amt },
        userEnteredFormat: { numberFormat: { type: 'CURRENCY', pattern: CURRENCY_FORMAT } } },
    ]
  }));
  batchUpdate(spreadsheetId, [{
    updateCells: {
      range: { sheetId, startRowIndex: 4, endRowIndex: 4 + dataRows.length,
               startColumnIndex: 0, endColumnIndex: 5 },
      rows: dataRows,
      fields: 'userEnteredValue,userEnteredFormat.numberFormat'
    }
  }]);

  // Dropdowns: C5:C54 = categories, D5:D54 = types
  batchUpdate(spreadsheetId, [
    dropdown(sheetId, 4, 54, 2, 3, CATEGORIES),
    dropdown(sheetId, 4, 54, 3, 4, TYPES),
  ]);

  // Input styling: pale cream for A-D, pale yellow for Amount (E), cream for F (unused, keep clean)
  batchUpdate(spreadsheetId, [
    bgColor(sheetId, 4, 54, 0, 4, COLORS.cream),
    bgColor(sheetId, 4, 54, 4, 5, COLORS.inputYellow),
    bgColor(sheetId, 4, 54, 5, 6, COLORS.cream),
  ]);

  // Conditional formatting on E2:F2 (REMAINING label + value): sage bg if positive, coral if negative
  batchUpdate(spreadsheetId, [
    cfSingleColor(sheetId, 1, 2, 4, 6, '=$F$2>=0', COLORS.positiveBg),
    cfSingleColor(sheetId, 1, 2, 4, 6, '=$F$2<0',  COLORS.negativeBg),
  ]);

  console.log('BUDGET tab done.');
}

function buildSavingsTab(spreadsheetId, sheetId) {
  // Row 1: banner
  batchUpdate(spreadsheetId, [
    mergeCells(sheetId, 0, 1, 0, 8),
    bgColor(sheetId, 0, 1, 0, 8, COLORS.terracotta),
    textFormat(sheetId, 0, 1, 0, 8, { bold: true, fontSize: 12, color: COLORS.white }),
    {
      updateCells: {
        range: { sheetId, startRowIndex: 0, endRowIndex: 1,
                 startColumnIndex: 0, endColumnIndex: 1 },
        rows: [{ values: [{ userEnteredValue: { stringValue: BANNER_LABELS.savings } }] }],
        fields: 'userEnteredValue'
      }
    }
  ]);

  // Row 2: summary: A2 label, B2 total saved, C2 label, D2 total target, E2 label, F2 overall %
  batchUpdate(spreadsheetId, [{
    updateCells: {
      range: { sheetId, startRowIndex: 1, endRowIndex: 2,
               startColumnIndex: 0, endColumnIndex: 6 },
      rows: [{
        values: [
          { userEnteredValue: { stringValue: 'إجمالي الادخار' },
            userEnteredFormat: { textFormat: { fontSize: 8, foregroundColor: COLORS.muted } } },
          { userEnteredValue: { formulaValue: '=SUM(C5:C9)' },
            userEnteredFormat: {
              numberFormat: { type: 'CURRENCY', pattern: CURRENCY_FORMAT },
              textFormat: { bold: true, fontSize: 12, foregroundColor: COLORS.sage }
            }
          },
          { userEnteredValue: { stringValue: 'إجمالي الهدف' },
            userEnteredFormat: { textFormat: { fontSize: 8, foregroundColor: COLORS.muted } } },
          { userEnteredValue: { formulaValue: '=SUM(B5:B9)' },
            userEnteredFormat: {
              numberFormat: { type: 'CURRENCY', pattern: CURRENCY_FORMAT },
              textFormat: { bold: true, fontSize: 12, foregroundColor: COLORS.terracotta }
            }
          },
          { userEnteredValue: { stringValue: 'المجموع %' },
            userEnteredFormat: { textFormat: { fontSize: 8, foregroundColor: COLORS.muted } } },
          { userEnteredValue: { formulaValue: '=IFERROR(B2/D2,0)' },
            userEnteredFormat: {
              numberFormat: { type: 'PERCENT', pattern: PCT_FORMAT },
              textFormat: { bold: true, fontSize: 12, foregroundColor: COLORS.terracotta }
            }
          },
        ]
      }],
      fields: 'userEnteredValue,userEnteredFormat.numberFormat,userEnteredFormat.textFormat'
    }
  }]);

  // Row 4: headers, cream bg, terracotta bold
  batchUpdate(spreadsheetId, [
    bgColor(sheetId, 3, 4, 0, 8, COLORS.cream),
    {
      updateCells: {
        range: { sheetId, startRowIndex: 3, endRowIndex: 4,
                 startColumnIndex: 0, endColumnIndex: 8 },
        rows: [{
          values: SAVINGS_HEADERS.map(h => ({
            userEnteredValue: { stringValue: h },
            userEnteredFormat: { textFormat: { bold: true, fontSize: 10,
              foregroundColor: COLORS.terracotta } }
          }))
        }],
        fields: 'userEnteredValue,userEnteredFormat.textFormat'
      }
    },
    freezeRows(sheetId, 4),
  ]);

  // Rows 5-7: sample goals with formulas (indices 4-6)
  const goalRows = SAMPLE_GOALS.map(([name, target, saved, dateStr], i) => {
    const r = i + 5; // 1-based row number for formula references
    return {
      values: [
        { userEnteredValue: { stringValue: name } },
        { userEnteredValue: { numberValue: target },
          userEnteredFormat: { numberFormat: { type: 'CURRENCY', pattern: CURRENCY_FORMAT } } },
        { userEnteredValue: { numberValue: saved },
          userEnteredFormat: { numberFormat: { type: 'CURRENCY', pattern: CURRENCY_FORMAT } } },
        { userEnteredValue: { stringValue: dateStr } },
        { userEnteredValue: { formulaValue: `=IFERROR(C${r}/B${r},0)` },
          userEnteredFormat: { numberFormat: { type: 'PERCENT', pattern: PCT_FORMAT } } },
        { userEnteredValue: { formulaValue:
            `=IFERROR((B${r}-C${r})/MAX(1,DATEDIF(TODAY(),IFERROR(DATEVALUE(D${r}),D${r}),"M")),0)` },
          userEnteredFormat: { numberFormat: { type: 'CURRENCY', pattern: CURRENCY_FORMAT } } },
        { userEnteredValue: { formulaValue:
            `=REPT("█",MIN(10,ROUND(E${r}*10,0)))&REPT("░",MAX(0,10-MIN(10,ROUND(E${r}*10,0))))` },
          userEnteredFormat: { textFormat: {
            fontFamily: 'Courier New', fontSize: 10, foregroundColor: COLORS.sage } } },
        { userEnteredValue: { formulaValue:
            `=IF(E${r}>=1,"✓ ممول!",IF(F${r}<=0,"✓ في المسار","> "&TEXT(F${r},"#,##0 \\"د.م\\"")&"/شهر"))` },
          userEnteredFormat: { textFormat: { fontSize: 10, foregroundColor: COLORS.sage } } },
      ]
    };
  });

  batchUpdate(spreadsheetId, [{
    updateCells: {
      range: { sheetId, startRowIndex: 4, endRowIndex: 4 + goalRows.length,
               startColumnIndex: 0, endColumnIndex: 8 },
      rows: goalRows,
      fields: 'userEnteredValue,userEnteredFormat.numberFormat,userEnteredFormat.textFormat'
    }
  }]);

  // Conditional formatting: relative row reference (E5, not $E5) so each row evaluates itself
  // Note: ar_MA locale may reject decimal point in CF formulas; use E5*2>=1 instead of E5>=0.5
  batchUpdate(spreadsheetId, [
    cfSingleColor(sheetId, 4, 9, 0, 8, '=E5>=1',    COLORS.paleSage),
  ]);
  batchUpdate(spreadsheetId, [
    cfSingleColor(sheetId, 4, 9, 0, 8, '=E5*2>=1', COLORS.cream),
  ]);

  // Column widths
  batchUpdate(spreadsheetId, [
    colWidth(sheetId, 0, 160), colWidth(sheetId, 1, 110),
    colWidth(sheetId, 2, 110), colWidth(sheetId, 3, 100),
    colWidth(sheetId, 4, 90),  colWidth(sheetId, 5, 130),
    colWidth(sheetId, 6, 130), colWidth(sheetId, 7, 150),
  ]);

  console.log('SAVINGS tab done.');
}

function buildDashboardTab(spreadsheetId, sheetId) {
  // Cross-sheet reference helpers: Arabic sheet names require single-quoting in Sheets formula syntax
  const budgetRef  = `'${BANNER_LABELS.budget}'`;   // "'الميزانية'"
  const savingsRef = `'${BANNER_LABELS.savings}'`;  // "'الادخار'"

  // Sheet background: cream
  batchUpdate(spreadsheetId, [ bgColor(sheetId, 0, 30, 0, 15, COLORS.cream) ]);

  // Row 1: banner with auto month/year
  batchUpdate(spreadsheetId, [
    mergeCells(sheetId, 0, 1, 0, 10),
    bgColor(sheetId, 0, 1, 0, 10, COLORS.terracotta),
    textFormat(sheetId, 0, 1, 0, 10, { bold: true, fontSize: 12, color: COLORS.white }),
    {
      updateCells: {
        range: { sheetId, startRowIndex: 0, endRowIndex: 1,
                 startColumnIndex: 0, endColumnIndex: 1 },
        rows: [{ values: [{
          userEnteredValue: { formulaValue:
            `="${BANNER_LABELS.dashboard} · "&TEXT(TODAY(),"MMMM YYYY")` }
        }] }],
        fields: 'userEnteredValue'
      }
    }
  ]);

  // LEFT COLUMN, Card 1: Income (rows 2-4, cols A-D / indices 1-4, 0-4)
  batchUpdate(spreadsheetId, [
    cardBorder(sheetId, 1, 4, 0, 4),
    bgColor(sheetId, 1, 4, 0, 4, COLORS.white),
    {
      updateCells: {
        range: { sheetId, startRowIndex: 1, endRowIndex: 4,
                 startColumnIndex: 0, endColumnIndex: 1 },
        rows: [
          { values: [{ userEnteredValue: { stringValue: KPI_LABELS.income },
            userEnteredFormat: { textFormat: { fontSize: 8, foregroundColor: COLORS.muted } } }] },
          { values: [{ userEnteredValue: { formulaValue: `=${budgetRef}!B2` },
            userEnteredFormat: {
              numberFormat: { type: 'CURRENCY', pattern: CURRENCY_FORMAT },
              textFormat: { bold: true, fontSize: 14, foregroundColor: COLORS.terracotta }
            }
          }] },
          { values: [{ userEnteredValue: { stringValue: KPI_LABELS.thisMonth },
            userEnteredFormat: { textFormat: { fontSize: 8, foregroundColor: COLORS.muted } } }] },
        ],
        fields: 'userEnteredValue,userEnteredFormat.numberFormat,userEnteredFormat.textFormat'
      }
    }
  ]);

  // LEFT COLUMN, Card 2: Spent (rows 5-7)
  batchUpdate(spreadsheetId, [
    cardBorder(sheetId, 4, 7, 0, 4),
    bgColor(sheetId, 4, 7, 0, 4, COLORS.white),
    {
      updateCells: {
        range: { sheetId, startRowIndex: 4, endRowIndex: 7,
                 startColumnIndex: 0, endColumnIndex: 1 },
        rows: [
          { values: [{ userEnteredValue: { stringValue: KPI_LABELS.spent },
            userEnteredFormat: { textFormat: { fontSize: 8, foregroundColor: COLORS.muted } } }] },
          { values: [{ userEnteredValue: { formulaValue: `=${budgetRef}!D2` },
            userEnteredFormat: {
              numberFormat: { type: 'CURRENCY', pattern: CURRENCY_FORMAT },
              textFormat: { bold: true, fontSize: 14, foregroundColor: COLORS.coral }
            }
          }] },
          { values: [{ userEnteredValue: {
              formulaValue: `=TEXT(IFERROR(${budgetRef}!D2/${budgetRef}!B2*100,0),"0")&"% من الدخل"` },
            userEnteredFormat: { textFormat: { fontSize: 8, foregroundColor: COLORS.muted } } }] },
        ],
        fields: 'userEnteredValue,userEnteredFormat.numberFormat,userEnteredFormat.textFormat'
      }
    }
  ]);

  // LEFT COLUMN, Card 3: Remaining (rows 8-10)
  batchUpdate(spreadsheetId, [
    cardBorder(sheetId, 7, 10, 0, 4),
    bgColor(sheetId, 7, 10, 0, 4, COLORS.white),
    {
      updateCells: {
        range: { sheetId, startRowIndex: 7, endRowIndex: 10,
                 startColumnIndex: 0, endColumnIndex: 1 },
        rows: [
          { values: [{ userEnteredValue: { stringValue: KPI_LABELS.remaining },
            userEnteredFormat: { textFormat: { fontSize: 8, foregroundColor: COLORS.muted } } }] },
          { values: [{ userEnteredValue: { formulaValue: `=${budgetRef}!F2` },
            userEnteredFormat: {
              numberFormat: { type: 'CURRENCY', pattern: CURRENCY_FORMAT },
              textFormat: { bold: true, fontSize: 14, foregroundColor: COLORS.sage }
            }
          }] },
          { values: [{ userEnteredValue: {
              formulaValue:
                `=IF(${budgetRef}!F2>=0,"${KPI_LABELS.underBudget}","${KPI_LABELS.overBudget}")` },
            userEnteredFormat: { textFormat: { fontSize: 8, foregroundColor: COLORS.sage } } }] },
        ],
        fields: 'userEnteredValue,userEnteredFormat.numberFormat,userEnteredFormat.textFormat'
      }
    }
  ]);

  // Conditional format Card 3 value (row 9, index 8): sage/coral bg
  // Use local cell reference ($A$9 holds =${budgetRef}!F2); cross-sheet refs not allowed in CF formulas
  batchUpdate(spreadsheetId, [
    cfSingleColor(sheetId, 8, 9, 0, 4, '=$A$9>=0', COLORS.positiveBg),
    cfSingleColor(sheetId, 8, 9, 0, 4, '=$A$9<0',  COLORS.negativeBg),
  ]);

  // RIGHT COLUMN, Spending split card (rows 2-6, cols F-J / indices 1-6, 5-10)
  batchUpdate(spreadsheetId, [
    cardBorder(sheetId, 1, 6, 5, 10),
    bgColor(sheetId, 1, 6, 5, 10, COLORS.white),
    {
      updateCells: {
        range: { sheetId, startRowIndex: 1, endRowIndex: 6,
                 startColumnIndex: 5, endColumnIndex: 6 },
        rows: [
          { values: [{ userEnteredValue: { stringValue: DASHBOARD_LABELS.spendingSplit },
            userEnteredFormat: { textFormat: { bold: true, fontSize: 9,
              foregroundColor: COLORS.terracotta } } }] },
          { values: [{ userEnteredValue: { stringValue: DASHBOARD_LABELS.spending },
            userEnteredFormat: { textFormat: { fontSize: 9, foregroundColor: COLORS.charcoal } } }] },
          { values: [{ userEnteredValue: { formulaValue:
              `=REPT("█",ROUND(IFERROR(${budgetRef}!D2/${budgetRef}!B2,0)*10,0))` +
              `&REPT("░",10-ROUND(IFERROR(${budgetRef}!D2/${budgetRef}!B2,0)*10,0))` },
            userEnteredFormat: { textFormat: { fontFamily: 'Courier New', fontSize: 10,
              foregroundColor: COLORS.coral } } }] },
          { values: [{ userEnteredValue: { stringValue: DASHBOARD_LABELS.savingsLabel },
            userEnteredFormat: { textFormat: { fontSize: 9, foregroundColor: COLORS.charcoal } } }] },
          { values: [{ userEnteredValue: { formulaValue:
              `=REPT("█",ROUND((1-IFERROR(${budgetRef}!D2/${budgetRef}!B2,0))*10,0))` +
              `&REPT("░",10-ROUND((1-IFERROR(${budgetRef}!D2/${budgetRef}!B2,0))*10,0))` },
            userEnteredFormat: { textFormat: { fontFamily: 'Courier New', fontSize: 10,
              foregroundColor: COLORS.sage } } }] },
        ],
        fields: 'userEnteredValue,userEnteredFormat.textFormat'
      }
    }
  ]);

  // RIGHT COLUMN, Top savings goal card (rows 7-10, cols F-J / indices 6-10, 5-10)
  batchUpdate(spreadsheetId, [
    cardBorder(sheetId, 6, 10, 5, 10),
    bgColor(sheetId, 6, 10, 5, 10, COLORS.white),
    {
      updateCells: {
        range: { sheetId, startRowIndex: 6, endRowIndex: 10,
                 startColumnIndex: 5, endColumnIndex: 6 },
        rows: [
          { values: [{ userEnteredValue: { stringValue: DASHBOARD_LABELS.topSavingsGoal },
            userEnteredFormat: { textFormat: { bold: true, fontSize: 9,
              foregroundColor: COLORS.terracotta } } }] },
          { values: [{ userEnteredValue: { formulaValue: `=${savingsRef}!A5` },
            userEnteredFormat: { textFormat: { bold: true, fontSize: 10,
              foregroundColor: COLORS.charcoal } } }] },
          { values: [{ userEnteredValue: { formulaValue: `=${savingsRef}!G5` },
            userEnteredFormat: { textFormat: { fontFamily: 'Courier New', fontSize: 10,
              foregroundColor: COLORS.sage } } }] },
          { values: [{ userEnteredValue: {
              formulaValue: `=${savingsRef}!C5&" / "&${savingsRef}!B5&" د.م · "&TEXT(${savingsRef}!E5,"0%")` },
            userEnteredFormat: { textFormat: { fontSize: 8,
              foregroundColor: COLORS.muted } } }] },
        ],
        fields: 'userEnteredValue,userEnteredFormat.textFormat'
      }
    }
  ]);

  // Column widths for dashboard
  batchUpdate(spreadsheetId, [
    colWidth(sheetId, 0, 160), colWidth(sheetId, 1, 80),
    colWidth(sheetId, 2, 80),  colWidth(sheetId, 3, 80),
    colWidth(sheetId, 4, 20),  // spacer col E
    colWidth(sheetId, 5, 160), colWidth(sheetId, 6, 80),
    colWidth(sheetId, 7, 80),  colWidth(sheetId, 8, 80),
    colWidth(sheetId, 9, 80),
  ]);

  console.log('DASHBOARD tab done.');
}

buildBudgetTab(spreadsheetId, budgetSheetId);
buildSavingsTab(spreadsheetId, savingsSheetId);
buildDashboardTab(spreadsheetId, dashboardSheetId);

shareViewOnly(spreadsheetId);
console.log('Done. Share URL above with Etsy buyer.');
