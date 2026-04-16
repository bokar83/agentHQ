import { COLORS } from './colors.js';

// Background color on a cell range
export function bgColor(sheetId, startRow, endRow, startCol, endCol, color) {
  return {
    repeatCell: {
      range: { sheetId, startRowIndex: startRow, endRowIndex: endRow,
               startColumnIndex: startCol, endColumnIndex: endCol },
      cell: { userEnteredFormat: { backgroundColor: color } },
      fields: 'userEnteredFormat.backgroundColor'
    }
  };
}

// Text formatting on a cell range
export function textFormat(sheetId, startRow, endRow, startCol, endCol,
  { bold = false, fontSize = 10, color = COLORS.charcoal } = {}) {
  return {
    repeatCell: {
      range: { sheetId, startRowIndex: startRow, endRowIndex: endRow,
               startColumnIndex: startCol, endColumnIndex: endCol },
      cell: { userEnteredFormat: { textFormat: { bold, fontSize, foregroundColor: color } } },
      fields: 'userEnteredFormat.textFormat'
    }
  };
}

// Merge all cells in a range
export function mergeCells(sheetId, startRow, endRow, startCol, endCol) {
  return {
    mergeCells: {
      range: { sheetId, startRowIndex: startRow, endRowIndex: endRow,
               startColumnIndex: startCol, endColumnIndex: endCol },
      mergeType: 'MERGE_ALL'
    }
  };
}

// Thin card border (1px solid cardBorder color) on all sides
export function cardBorder(sheetId, startRow, endRow, startCol, endCol) {
  const style = { style: 'SOLID', width: 1, color: COLORS.cardBorder };
  return {
    updateBorders: {
      range: { sheetId, startRowIndex: startRow, endRowIndex: endRow,
               startColumnIndex: startCol, endColumnIndex: endCol },
      top: style, bottom: style, left: style, right: style,
      innerHorizontal: style, innerVertical: style
    }
  };
}

// Set a single column width in pixels
export function colWidth(sheetId, colIndex, pixelSize) {
  return {
    updateDimensionProperties: {
      range: { sheetId, dimension: 'COLUMNS',
               startIndex: colIndex, endIndex: colIndex + 1 },
      properties: { pixelSize },
      fields: 'pixelSize'
    }
  };
}

// Freeze the first N rows on a sheet
export function freezeRows(sheetId, rowCount) {
  return {
    updateSheetProperties: {
      properties: { sheetId, gridProperties: { frozenRowCount: rowCount } },
      fields: 'gridProperties.frozenRowCount'
    }
  };
}

// Dropdown data validation on a range
export function dropdown(sheetId, startRow, endRow, startCol, endCol, values) {
  return {
    setDataValidation: {
      range: { sheetId, startRowIndex: startRow, endRowIndex: endRow,
               startColumnIndex: startCol, endColumnIndex: endCol },
      rule: {
        condition: {
          type: 'ONE_OF_LIST',
          values: values.map(v => ({ userEnteredValue: v }))
        },
        strict: true,
        showCustomUi: true
      }
    }
  };
}

// Conditional format rule: custom formula → solid background color
export function cfSingleColor(sheetId, startRow, endRow, startCol, endCol,
  formulaStr, bgColorVal) {
  return {
    addConditionalFormatRule: {
      rule: {
        ranges: [{ sheetId, startRowIndex: startRow, endRowIndex: endRow,
                   startColumnIndex: startCol, endColumnIndex: endCol }],
        booleanRule: {
          condition: { type: 'CUSTOM_FORMULA',
                       values: [{ userEnteredValue: formulaStr }] },
          format: { backgroundColor: bgColorVal }
        }
      },
      index: 0
    }
  };
}
