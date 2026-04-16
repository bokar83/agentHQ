# Dashboards4Sale/xlsx-budget-en/build.py
"""Build budget_en.xlsx - Monthly Budget Planner (English)."""
import sys
import io
import zipfile
import xlsxwriter
from datetime import datetime

sys.path.insert(0, 'Dashboards4Sale/shared')
sys.path.insert(0, 'Dashboards4Sale/xlsx-budget-en')

from xl_builder import add_formats, COLORS, COLORS_HEX
from data import (
    TITLE, CATEGORIES, TYPES, SAMPLE_TRANSACTIONS, HEADERS,
    KPI_LABELS, BANNER_LABEL, SAVINGS_LABEL, DASHBOARD_LABEL,
    SAMPLE_GOALS, SAVINGS_HEADERS, INCOME_TYPE, EXPENSE_TYPE,
    STATUS_ON_TRACK, STATUS_BEHIND,
    CURRENCY_FORMAT, PCT_FORMAT, DATE_FORMAT, DASHBOARD_LABELS,
)

OUTPUT = 'Dashboards4Sale/xlsx-budget-en/budget_en.xlsx'
BLANK_ROWS = 35

# ---------------------------------------------------------------------------
# Shape helpers
# ---------------------------------------------------------------------------

def shape_xml(shape_id, label, value, fill_rgb,
              col_from, row_from, col_to, row_to,
              label_size=700, value_size=1600):
    """Return an lxml Element for a roundRect twoCellAnchor."""
    XDRNS = 'http://schemas.openxmlformats.org/drawingml/2006/spreadsheetDrawing'
    ANS   = 'http://schemas.openxmlformats.org/drawingml/2006/main'
    xml = f'''<xdr:twoCellAnchor xmlns:xdr="{XDRNS}" xmlns:a="{ANS}" editAs="twoCell">
  <xdr:from><xdr:col>{col_from}</xdr:col><xdr:colOff>114300</xdr:colOff>
            <xdr:row>{row_from}</xdr:row><xdr:rowOff>57150</xdr:rowOff></xdr:from>
  <xdr:to>  <xdr:col>{col_to}</xdr:col><xdr:colOff>-114300</xdr:colOff>
            <xdr:row>{row_to}</xdr:row><xdr:rowOff>-57150</xdr:rowOff></xdr:to>
  <xdr:sp macro="" textlink="">
    <xdr:nvSpPr>
      <xdr:cNvPr id="{shape_id}" name="Shape{shape_id}"/>
      <xdr:cNvSpPr><a:spLocks noGrp="1"/></xdr:cNvSpPr>
    </xdr:nvSpPr>
    <xdr:spPr>
      <a:xfrm><a:off x="0" y="0"/><a:ext cx="1" cy="1"/></a:xfrm>
      <a:prstGeom prst="roundRect"><a:avLst/></a:prstGeom>
      <a:solidFill><a:srgbClr val="{fill_rgb}"/></a:solidFill>
      <a:ln><a:noFill/></a:ln>
    </xdr:spPr>
    <xdr:txBody>
      <a:bodyPr anchor="ctr" anchorCtr="1" wrap="square"/>
      <a:lstStyle/>
      <a:p><a:pPr algn="ctr"/><a:r>
        <a:rPr lang="en-US" sz="{label_size}" b="0" dirty="0">
          <a:solidFill><a:srgbClr val="FFFFFF"/></a:solidFill>
        </a:rPr>
        <a:t>{label}</a:t>
      </a:r></a:p>
      <a:p><a:pPr algn="ctr"/><a:r>
        <a:rPr lang="en-US" sz="{value_size}" b="1" dirty="0">
          <a:solidFill><a:srgbClr val="FFFFFF"/></a:solidFill>
        </a:rPr>
        <a:t>{value}</a:t>
      </a:r></a:p>
    </xdr:txBody>
  </xdr:sp>
  <xdr:clientData/>
</xdr:twoCellAnchor>'''
    from lxml import etree
    return etree.fromstring(xml.encode('utf-8'))


def _build_drawing_xml(shapes_list):
    """Wrap a list of shape elements in a wsDr root and return bytes."""
    from lxml import etree
    XDRNS = 'http://schemas.openxmlformats.org/drawingml/2006/spreadsheetDrawing'
    root = etree.Element(f'{{{XDRNS}}}wsDr',
                         nsmap={'xdr': XDRNS,
                                'a': 'http://schemas.openxmlformats.org/drawingml/2006/main'})
    for sp in shapes_list:
        root.append(sp)
    return etree.tostring(root, xml_declaration=True, encoding='UTF-8', standalone=True)


def inject_shapes_into(xlsx_path, drawing_name, shapes_list):
    """Inject lxml shape elements into an existing drawing XML inside the xlsx zip."""
    from lxml import etree

    with open(xlsx_path, 'rb') as f:
        buf = io.BytesIO(f.read())

    out = io.BytesIO()
    with zipfile.ZipFile(buf, 'r') as zin, \
         zipfile.ZipFile(out, 'w', zipfile.ZIP_DEFLATED) as zout:
        for item in zin.infolist():
            data = zin.read(item.filename)
            if item.filename == drawing_name:
                root = etree.fromstring(data)
                for sp in reversed(shapes_list):
                    root.insert(0, sp)
                data = etree.tostring(
                    root, xml_declaration=True,
                    encoding='UTF-8', standalone=True)
            zout.writestr(item, data)

    out.seek(0)
    with open(xlsx_path, 'wb') as f:
        f.write(out.read())


def inject_new_drawing(xlsx_path, sheet_xml_name, drawing_filename, shapes_list):
    """
    Create a brand-new drawing file and wire it to a sheet that has no drawing yet.

    sheet_xml_name: e.g. 'xl/worksheets/sheet1.xml'
    drawing_filename: e.g. 'xl/drawings/drawing2.xml'
    shapes_list: list of lxml Elements
    """
    from lxml import etree

    drawing_data = _build_drawing_xml(shapes_list)

    # drawing rels file (empty, no chart refs needed for shapes-only drawing)
    rels_filename = drawing_filename.replace(
        'xl/drawings/', 'xl/drawings/_rels/') + '.rels'
    rels_data = (
        b'<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        b'<Relationships xmlns="http://schemas.openxmlformats.org/'
        b'package/2006/relationships"/>'
    )

    # sheet rels entry to wire drawing to the sheet
    sheet_name = sheet_xml_name.split('/')[-1]          # e.g. sheet1.xml
    sheet_rels_filename = (
        f'xl/worksheets/_rels/{sheet_name}.rels'
    )
    # relative path from the sheet _rels dir back to drawings/
    drawing_target = '../drawings/' + drawing_filename.split('/')[-1]
    sheet_rels_data = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        f'<Relationship Id="rId1" '
        f'Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/drawing" '
        f'Target="{drawing_target}"/>'
        '</Relationships>'
    ).encode('UTF-8')

    # content type override entry
    ct_override = (
        f'<Override PartName="/{drawing_filename}" '
        f'ContentType="application/vnd.openxmlformats-officedocument.drawing+xml"/>'
    )

    with open(xlsx_path, 'rb') as f:
        buf = io.BytesIO(f.read())

    out = io.BytesIO()
    with zipfile.ZipFile(buf, 'r') as zin, \
         zipfile.ZipFile(out, 'w', zipfile.ZIP_DEFLATED) as zout:
        for item in zin.infolist():
            data = zin.read(item.filename)

            if item.filename == '[Content_Types].xml':
                # Insert override before closing </Types>
                data = data.replace(b'</Types>', ct_override.encode() + b'</Types>')

            elif item.filename == sheet_xml_name:
                # Append <drawing r:id="rId1"/> before </worksheet>
                r_ns = 'http://schemas.openxmlformats.org/officeDocument/2006/relationships'
                drawing_el = (
                    f'<drawing xmlns:r="{r_ns}" r:id="rId1"/>'
                ).encode()
                data = data.replace(b'</worksheet>', drawing_el + b'</worksheet>')

            zout.writestr(item, data)

        # Add the new drawing file
        zout.writestr(drawing_filename, drawing_data)
        # Add drawing rels
        zout.writestr(rels_filename, rels_data)
        # Add sheet rels
        zout.writestr(sheet_rels_filename, sheet_rels_data)

    out.seek(0)
    with open(xlsx_path, 'wb') as f:
        f.write(out.read())


# ---------------------------------------------------------------------------
# Build entry point
# ---------------------------------------------------------------------------

def build():
    wb = xlsxwriter.Workbook(OUTPUT, {'strings_to_numbers': False})
    wb.set_properties({'title': TITLE})
    fmt = add_formats(wb)

    # Override num_formats to locale-specific versions
    for key in ('kpi_value', 'kpi_value_coral', 'kpi_value_sage',
                'data_currency', 'income_currency', 'savings_currency', 'dash_value'):
        fmt[key].set_num_format(CURRENCY_FORMAT)
    for key in ('data_date', 'income_date'):
        fmt[key].set_num_format(DATE_FORMAT)
    fmt['savings_pct'].set_num_format(PCT_FORMAT)
    fmt['kpi_value_pct'].set_num_format(PCT_FORMAT)

    build_budget_tab(wb, fmt)
    build_savings_tab(wb, fmt)
    build_dashboard_tab(wb, fmt)

    wb.close()

    # Post-process: inject roundRect shapes
    inject_budget_shapes(OUTPUT)
    inject_dashboard_shapes(OUTPUT)
    print('Shapes injected.')

    print(f'Built: {OUTPUT}')


# ---------------------------------------------------------------------------
# Budget tab
# ---------------------------------------------------------------------------

def build_budget_tab(wb, fmt):
    ws = wb.add_worksheet(BANNER_LABEL)
    ws.set_zoom(90)
    ws.hide_gridlines(2)
    ws.set_tab_color(COLORS['terracotta'])

    # Column widths: A=margin, B=Date, C=Desc, D=Category, E=Type, F=Amount, G=margin
    ws.set_column(0, 0, 2)    # A margin
    ws.set_column(1, 1, 13)   # B Date
    ws.set_column(2, 2, 28)   # C Description
    ws.set_column(3, 3, 18)   # D Category
    ws.set_column(4, 4, 12)   # E Type
    ws.set_column(5, 5, 14)   # F Amount
    ws.set_column(6, 6, 2)    # G margin

    # Row 0 (height 36): Banner merged B1:F1 (cols 1-5)
    ws.merge_range(0, 1, 0, 5, BANNER_LABEL, fmt['banner'])
    ws.set_row(0, 36)
    ws.write_blank(0, 0, None, fmt['empty'])
    ws.write_blank(0, 6, None, fmt['empty'])

    # Row 1 (height 8): spacer
    ws.set_row(1, 8)
    for c in range(7):
        ws.write_blank(1, c, None, fmt['empty'])

    # Rows 2-3 (height 44): KPI shape zone - write cream bg + formulas under shapes
    ws.set_row(2, 44)
    ws.set_row(3, 44)
    for c in range(7):
        ws.write_blank(2, c, None, fmt['empty'])
        ws.write_blank(3, c, None, fmt['empty'])

    # KPI formula cells (under shapes, referenced by Dashboard)
    # B3 = income SUMIF
    ws.write_formula(3, 1, f'=SUMIF(E:E,"{INCOME_TYPE}",F:F)', fmt['kpi_value'])
    # C3 = expense SUMIF
    ws.write_formula(3, 2, f'=SUMIF(E:E,"{EXPENSE_TYPE}",F:F)', fmt['kpi_value_coral'])
    # D3-E3 merged = remaining
    ws.merge_range(3, 3, 3, 4, '', fmt['kpi_value_sage'])
    ws.write_formula(3, 3, '=B4-C4', fmt['kpi_value_sage'])

    # Row 4 (height 8): spacer
    ws.set_row(4, 8)
    for c in range(7):
        ws.write_blank(4, c, None, fmt['empty'])

    # Row 5 (height 22): Column headers B-F
    ws.set_row(5, 22)
    ws.write_blank(5, 0, None, fmt['empty'])
    ws.write_blank(5, 6, None, fmt['empty'])
    for c, h in enumerate(HEADERS):
        ws.write(5, c + 1, h, fmt['col_header'])

    # Rows 6+: sample transactions
    first_data_row = 6
    C = COLORS
    stripe_fmt_map = {}

    def get_stripe_fmt(is_income, cell_type, stripe):
        """Return appropriate format for striped rows."""
        key = (is_income, cell_type, stripe)
        if key not in stripe_fmt_map:
            if is_income:
                base = fmt['income_currency'] if cell_type == 'currency' else (
                    fmt['income_date'] if cell_type == 'date' else fmt['income_row'])
            else:
                if stripe:
                    if cell_type == 'currency':
                        base = wb.add_format({
                            'font_size': 10, 'font_color': C['charcoal'],
                            'bg_color': C['stripe'], 'valign': 'vcenter', 'align': 'right',
                            'font_name': 'Calibri', 'border': 1, 'border_color': C['border'],
                            'num_format': CURRENCY_FORMAT,
                        })
                    elif cell_type == 'date':
                        base = wb.add_format({
                            'font_size': 10, 'font_color': C['charcoal'],
                            'bg_color': C['stripe'], 'valign': 'vcenter', 'align': 'center',
                            'font_name': 'Calibri', 'border': 1, 'border_color': C['border'],
                            'num_format': DATE_FORMAT,
                        })
                    else:
                        base = wb.add_format({
                            'font_size': 10, 'font_color': C['charcoal'],
                            'bg_color': C['stripe'], 'valign': 'vcenter',
                            'font_name': 'Calibri', 'border': 1, 'border_color': C['border'],
                        })
                else:
                    base = (fmt['data_currency'] if cell_type == 'currency' else
                            fmt['data_date'] if cell_type == 'date' else fmt['data_normal'])
            stripe_fmt_map[key] = base
        return stripe_fmt_map[key]

    for i, tx in enumerate(SAMPLE_TRANSACTIONS):
        r = first_data_row + i
        ws.set_row(r, 18)
        tx_date, desc, cat, tx_type, amount = tx
        is_income = (tx_type == INCOME_TYPE)
        stripe = (i % 2 == 1) and not is_income

        date_fmt = fmt['income_date'] if is_income else get_stripe_fmt(False, 'date', stripe)
        row_fmt  = fmt['income_row']  if is_income else get_stripe_fmt(False, 'text', stripe)
        curr_fmt = fmt['income_currency'] if is_income else get_stripe_fmt(False, 'currency', stripe)

        ws.write_blank(r, 0, None, fmt['empty'])
        ws.write_blank(r, 6, None, fmt['empty'])
        ws.write_datetime(r, 1, datetime(tx_date.year, tx_date.month, tx_date.day), date_fmt)
        ws.write(r, 2, desc,    row_fmt)
        ws.write(r, 3, cat,     row_fmt)
        ws.write(r, 4, tx_type, row_fmt)
        ws.write(r, 5, amount,  curr_fmt)

    # Blank input rows
    blank_start = first_data_row + len(SAMPLE_TRANSACTIONS)
    for i in range(BLANK_ROWS):
        r = blank_start + i
        ws.set_row(r, 18)
        ws.write_blank(r, 0, None, fmt['empty'])
        ws.write_blank(r, 1, None, fmt['data_date'])
        ws.write_blank(r, 2, None, fmt['data_input'])
        ws.write_blank(r, 3, None, fmt['data_input'])
        ws.write_blank(r, 4, None, fmt['data_input'])
        ws.write_blank(r, 5, None, fmt['data_currency'])
        ws.write_blank(r, 6, None, fmt['empty'])

    last_data_row = blank_start + BLANK_ROWS - 1

    # Category dropdown on col D (index 3)
    ws.data_validation(first_data_row, 3, last_data_row, 3, {
        'validate': 'list',
        'source':   CATEGORIES,
    })
    # Type dropdown on col E (index 4)
    ws.data_validation(first_data_row, 4, last_data_row, 4, {
        'validate': 'list',
        'source':   TYPES,
    })

    ws.freeze_panes(6, 0)


def inject_budget_shapes(xlsx_path):
    """Create drawing2.xml for Budget sheet and inject 3 roundRect KPI cards."""
    shapes = [
        shape_xml(1, KPI_LABELS['income'],    '$0',
                  COLORS_HEX['terracotta'],
                  col_from=1, row_from=2, col_to=3, row_to=4),
        shape_xml(2, KPI_LABELS['spent'],     '$0',
                  COLORS_HEX['coral'],
                  col_from=3, row_from=2, col_to=5, row_to=4),
        shape_xml(3, KPI_LABELS['remaining'], '$0',
                  COLORS_HEX['sage'],
                  col_from=5, row_from=2, col_to=7, row_to=4),
    ]
    inject_new_drawing(
        xlsx_path,
        sheet_xml_name='xl/worksheets/sheet1.xml',
        drawing_filename='xl/drawings/drawing2.xml',
        shapes_list=shapes,
    )


# ---------------------------------------------------------------------------
# Savings tab
# ---------------------------------------------------------------------------

def build_savings_tab(wb, fmt):
    ws = wb.add_worksheet(SAVINGS_LABEL)
    ws.set_zoom(90)
    ws.hide_gridlines(2)
    ws.set_tab_color(COLORS['sage'])

    # A=margin, B=Goal, C=Target, D=Saved, E=TargetDate, F=%Funded, G=MonthlyNeeded, H=Status, I=margin
    ws.set_column(0, 0, 2)    # A margin
    ws.set_column(1, 1, 22)   # B Goal name
    ws.set_column(2, 2, 12)   # C Target amount
    ws.set_column(3, 3, 12)   # D Saved amount
    ws.set_column(4, 4, 14)   # E Target date
    ws.set_column(5, 5, 10)   # F % Funded
    ws.set_column(6, 6, 16)   # G Monthly needed
    ws.set_column(7, 7, 14)   # H Status
    ws.set_column(8, 8, 2)    # I margin

    # Row 0: Banner B1:H1
    ws.merge_range(0, 1, 0, 7, SAVINGS_LABEL, fmt['banner'])
    ws.set_row(0, 36)
    ws.write_blank(0, 0, None, fmt['empty'])
    ws.write_blank(0, 8, None, fmt['empty'])

    # Row 1: spacer
    ws.set_row(1, 8)
    for c in range(9):
        ws.write_blank(1, c, None, fmt['empty'])

    # Row 2: Column headers B-H
    ws.set_row(2, 22)
    ws.write_blank(2, 0, None, fmt['empty'])
    ws.write_blank(2, 8, None, fmt['empty'])
    for c, h in enumerate(SAVINGS_HEADERS):
        ws.write(2, c + 1, h, fmt['savings_header'])

    # Rows 3+: sample goals
    dt = datetime
    today = dt.today().date()
    for i, goal in enumerate(SAMPLE_GOALS):
        r = 3 + i
        ws.set_row(r, 26)
        name, target, saved, target_date = goal

        pct = saved / target if target else 0
        months_left = max(1, (target_date.year - today.year) * 12
                          + (target_date.month - today.month))
        monthly = (target - saved) / months_left
        status = STATUS_ON_TRACK if pct >= 0.25 else STATUS_BEHIND
        status_fmt = fmt['status_on_track'] if status == STATUS_ON_TRACK else fmt['status_behind']

        ws.write_blank(r, 0, None, fmt['empty'])
        ws.write_blank(r, 8, None, fmt['empty'])
        ws.write(r, 1, name,   fmt['savings_data'])
        ws.write(r, 2, target, fmt['savings_currency'])
        ws.write(r, 3, saved,  fmt['savings_currency'])
        ws.write_datetime(r, 4,
            dt(target_date.year, target_date.month, target_date.day),
            fmt['savings_data'])
        ws.write(r, 5, pct,     fmt['savings_pct'])
        ws.write(r, 6, monthly, fmt['savings_currency'])
        ws.write(r, 7, status,  status_fmt)

    # Blank rows for user goals
    blank_start = 3 + len(SAMPLE_GOALS)
    for i in range(7):
        r = blank_start + i
        ws.set_row(r, 26)
        ws.write_blank(r, 0, None, fmt['empty'])
        ws.write_blank(r, 8, None, fmt['empty'])
        for c in range(1, 8):
            ws.write_blank(r, c, None, fmt['savings_data'])

    last_savings_row = blank_start + 6

    # CF data bar on % Funded column (F = col 5)
    ws.conditional_format(3, 5, last_savings_row, 5, {
        'type':      'data_bar',
        'bar_color': COLORS['sage'],
    })

    # CF status highlight on Status column (H = col 7)
    ws.conditional_format(3, 7, last_savings_row, 7, {
        'type':     'text',
        'criteria': 'containing',
        'value':    STATUS_ON_TRACK,
        'format':   fmt['status_on_track'],
    })
    ws.conditional_format(3, 7, last_savings_row, 7, {
        'type':     'text',
        'criteria': 'containing',
        'value':    STATUS_BEHIND,
        'format':   fmt['status_behind'],
    })

    ws.freeze_panes(3, 0)


# ---------------------------------------------------------------------------
# Dashboard tab
# ---------------------------------------------------------------------------

def build_dashboard_tab(wb, fmt):
    ws = wb.add_worksheet(DASHBOARD_LABEL)
    ws.set_zoom(90)
    ws.hide_gridlines(2)
    ws.set_tab_color(COLORS['coral'])

    # A=margin, B-F=data (width 18 each), G=margin
    ws.set_column(0, 0, 3)
    ws.set_column(1, 5, 18)
    ws.set_column(6, 6, 3)

    # Row 0: Banner A1:G1
    ws.merge_range(0, 0, 0, 6, DASHBOARD_LABEL, fmt['banner'])
    ws.set_row(0, 36)

    # Row 1: spacer
    ws.set_row(1, 8)
    for c in range(7):
        ws.write_blank(1, c, None, fmt['empty'])

    # Rows 2-3: KPI shape zone
    ws.set_row(2, 44)
    ws.set_row(3, 44)
    for c in range(7):
        ws.write_blank(2, c, None, fmt['empty'])
        ws.write_blank(3, c, None, fmt['empty'])

    # Row 4: spacer
    ws.set_row(4, 8)
    for c in range(7):
        ws.write_blank(4, c, None, fmt['empty'])

    # Dashboard KPI formula cells (under shapes, row 3 = index 3)
    # B3=income, C3=spent, D3=remaining, E3:F3=savings rate
    ws.write_formula(3, 1, f'={BANNER_LABEL}!B4', fmt['kpi_value'])
    ws.write_formula(3, 2, f'={BANNER_LABEL}!C4', fmt['kpi_value_coral'])
    ws.write_formula(3, 3, f'={BANNER_LABEL}!D4', fmt['kpi_value_sage'])
    ws.merge_range(3, 4, 3, 5, '', fmt['kpi_value_pct'])
    ws.write_formula(3, 4,
        f'=IF({BANNER_LABEL}!B4=0,0,{BANNER_LABEL}!D4/{BANNER_LABEL}!B4)',
        fmt['kpi_value_pct'])

    # Hidden data tables for charts (cols H-L, rows 2+)
    expense_cats = [c for c in CATEGORIES
                    if c not in (INCOME_TYPE, 'Savings Transfer', 'Other')]

    ws.write(1, 7, 'Category', fmt['subheader'])
    ws.write(1, 8, 'Amount',   fmt['subheader'])
    for i, cat in enumerate(expense_cats):
        r = 2 + i
        ws.write(r, 7, cat, fmt['data_normal'])
        ws.write_formula(r, 8,
            f'=SUMIF({BANNER_LABEL}!D:D,H{r+1},{BANNER_LABEL}!F:F)',
            fmt['data_currency'])

    ws.write(1, 10, 'Category', fmt['subheader'])
    ws.write(1, 11, 'Amount',   fmt['subheader'])
    ws.write(2, 10, KPI_LABELS['income'], fmt['data_normal'])
    ws.write_formula(2, 11, f'={BANNER_LABEL}!B4', fmt['data_currency'])
    ws.write(3, 10, KPI_LABELS['spent'],  fmt['data_normal'])
    ws.write_formula(3, 11, f'={BANNER_LABEL}!C4', fmt['data_currency'])

    # Donut chart: spending by category
    n_cats = len(expense_cats)
    palette = [
        '#C8956C', '#E07A5F', '#81B29A', '#D4A5A5',
        '#B5C4B1', '#E8C9A0', '#A8B5A2', '#D4956C',
        '#C4B59A', '#E0C0A0', '#9E8B8B',
    ]
    donut = wb.add_chart({'type': 'doughnut'})
    donut.add_series({
        'name':       DASHBOARD_LABELS['spending_split'],
        'categories': [DASHBOARD_LABEL, 2, 7, 1 + n_cats, 7],
        'values':     [DASHBOARD_LABEL, 2, 8, 1 + n_cats, 8],
        'data_labels': {'percentage': True, 'separator': '\n',
                        'font': {'size': 8}},
        'points': [{'fill': {'color': c}} for c in palette[:n_cats]],
    })
    donut.set_title({'name': DASHBOARD_LABELS['spending_split'],
                     'name_font': {'bold': True, 'size': 12,
                                   'color': COLORS['charcoal']}})
    donut.set_legend({'position': 'bottom', 'font': {'size': 8}})
    donut.set_size({'width': 380, 'height': 300})
    donut.set_chartarea({'border': {'color': COLORS['border']},
                         'fill':   {'color': COLORS['cream']}})
    donut.set_plotarea({'fill': {'color': COLORS['cream']}})
    ws.insert_chart(5, 1, donut, {'x_offset': 5, 'y_offset': 5})

    # Bar chart: income vs expenses
    bar = wb.add_chart({'type': 'bar'})
    bar.add_series({
        'name':       DASHBOARD_LABELS['spending'],
        'categories': [DASHBOARD_LABEL, 2, 10, 3, 10],
        'values':     [DASHBOARD_LABEL, 2, 11, 3, 11],
        'fill':       {'colors': [COLORS['sage'], COLORS['coral']]},
        'data_labels': {'value': True,
                        'num_format': '"$"#,##0',
                        'font': {'size': 9}},
    })
    bar.set_title({'name': 'Income vs Expenses',
                   'name_font': {'bold': True, 'size': 12,
                                 'color': COLORS['charcoal']}})
    bar.set_legend({'none': True})
    bar.set_size({'width': 380, 'height': 240})
    bar.set_chartarea({'border': {'color': COLORS['border']},
                       'fill':   {'color': COLORS['cream']}})
    bar.set_plotarea({'fill': {'color': COLORS['cream']}})
    ws.insert_chart(21, 1, bar, {'x_offset': 5, 'y_offset': 5})

    ws.freeze_panes(1, 0)


def inject_dashboard_shapes(xlsx_path):
    """Inject 4 roundRect KPI cards into the Dashboard sheet drawing (drawing1.xml)."""
    shapes = [
        shape_xml(1, KPI_LABELS['income'],    '$0',
                  COLORS_HEX['terracotta'],
                  col_from=1, row_from=2, col_to=2, row_to=4,
                  label_size=700, value_size=1400),
        shape_xml(2, KPI_LABELS['spent'],     '$0',
                  COLORS_HEX['coral'],
                  col_from=2, row_from=2, col_to=3, row_to=4,
                  label_size=700, value_size=1400),
        shape_xml(3, KPI_LABELS['remaining'], '$0',
                  COLORS_HEX['sage'],
                  col_from=3, row_from=2, col_to=4, row_to=4,
                  label_size=700, value_size=1400),
        shape_xml(4, 'SAVINGS RATE',          '0%',
                  COLORS_HEX['terracotta'],
                  col_from=4, row_from=2, col_to=6, row_to=4,
                  label_size=700, value_size=1400),
    ]
    inject_shapes_into(xlsx_path, 'xl/drawings/drawing1.xml', shapes)


if __name__ == '__main__':
    build()
