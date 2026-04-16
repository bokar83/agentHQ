// budget-template-en/build.js
import { createSpreadsheet, batchUpdate, getSpreadsheet, shareViewOnly }
  from '../shared/sheets-api.js';
import { COLORS } from '../shared/colors.js';
import { bgColor, textFormat, mergeCells, cardBorder,
         colWidth, freezeRows, dropdown, cfSingleColor }
  from '../shared/formatting.js';
import { TITLE, CATEGORIES, TYPES, SAMPLE_TRANSACTIONS, HEADERS,
         KPI_LABELS, BANNER_LABELS, SAVINGS_HEADERS, SAMPLE_GOALS,
         INCOME_TYPE, EXPENSE_TYPE, CURRENCY_FORMAT, PCT_FORMAT }
  from './data.js';

const sheet = createSpreadsheet(TITLE);
const spreadsheetId = sheet.spreadsheetId;
console.log('Created:', spreadsheetId);
console.log('URL: https://docs.google.com/spreadsheets/d/' + spreadsheetId);

// Get default sheet ID and rename to BUDGET
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

function buildBudgetTab(spreadsheetId, sheetId) {
  // Row 1: banner — merged A1:E1, terracotta bg, white bold 12pt
  batchUpdate(spreadsheetId, [
    mergeCells(sheetId, 0, 1, 0, 5),
    bgColor(sheetId, 0, 1, 0, 5, COLORS.terracotta),
    textFormat(sheetId, 0, 1, 0, 5, { bold: true, fontSize: 12, color: COLORS.white }),
    {
      updateCells: {
        range: { sheetId, startRowIndex: 0, endRowIndex: 1,
                 startColumnIndex: 0, endColumnIndex: 1 },
        rows: [{ values: [{ userEnteredValue: { stringValue: BANNER_LABELS.budget } }] }],
        fields: 'userEnteredValue'
      }
    }
  ]);

  // Row 2: KPI cells — A2 label, B2 Income value, C2 label, D2 Spent value,
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

  // Row 4: column headers — cream bg, terracotta bold text
  batchUpdate(spreadsheetId, [
    bgColor(sheetId, 3, 4, 0, 5, COLORS.cream),
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

  // Column widths: A=100, B=200, C=160, D=100, E=110
  batchUpdate(spreadsheetId, [
    colWidth(sheetId, 0, 100), colWidth(sheetId, 1, 200),
    colWidth(sheetId, 2, 160), colWidth(sheetId, 3, 100),
    colWidth(sheetId, 4, 110),
  ]);

  // Sample data rows 5-19 (indices 4-18)
  const dataRows = SAMPLE_TRANSACTIONS.map(([date, desc, cat, type, amt]) => ({
    values: [
      { userEnteredValue: { stringValue: date } },
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

  // Input styling: pale cream for A-D, pale yellow for Amount (E)
  batchUpdate(spreadsheetId, [
    bgColor(sheetId, 4, 54, 0, 4, COLORS.cream),
    bgColor(sheetId, 4, 54, 4, 5, COLORS.inputYellow),
  ]);

  // Conditional formatting on F2: green bg if positive, coral bg if negative
  batchUpdate(spreadsheetId, [
    cfSingleColor(sheetId, 1, 2, 5, 6, '=$F$2>=0', COLORS.positiveBg),
    cfSingleColor(sheetId, 1, 2, 5, 6, '=$F$2<0',  COLORS.negativeBg),
  ]);

  console.log('BUDGET tab done.');
}

function buildSavingsTab(spreadsheetId, sheetId) {
  console.log('SAVINGS tab — stub, will be implemented in Task 3.');
}

function buildDashboardTab(spreadsheetId, sheetId) {
  console.log('DASHBOARD tab — stub, will be implemented in Task 4.');
}

buildBudgetTab(spreadsheetId, budgetSheetId);
buildSavingsTab(spreadsheetId, savingsSheetId);
buildDashboardTab(spreadsheetId, dashboardSheetId);

shareViewOnly(spreadsheetId);
console.log('Done. Share URL above with Etsy buyer.');
