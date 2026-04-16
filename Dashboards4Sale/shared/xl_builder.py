# Dashboards4Sale/shared/xl_builder.py
"""Shared xlsxwriter helpers for budget template builds."""

COLORS = {
    'terracotta': '#C8956C',
    'coral':      '#E07A5F',
    'sage':       '#81B29A',
    'cream':      '#FDF6F0',
    'charcoal':   '#3D3535',
    'muted':      '#9E8B8B',
    'white':      '#FFFFFF',
    'input_bg':   '#FFFDE7',
    'pos_bg':     '#E8F5E9',
    'neg_bg':     '#FFF3E0',
    'pale_terra': '#F2DDD0',
    'pale_sage':  '#D4EAE0',
    'border':     '#E0D0C8',
}


def add_formats(wb):
    """Return dict of all named Format objects for this workbook."""
    C = COLORS
    f = {}

    f['banner'] = wb.add_format({
        'bold': True, 'font_size': 18, 'font_color': C['white'],
        'bg_color': C['terracotta'], 'align': 'center', 'valign': 'vcenter',
        'font_name': 'Calibri',
    })

    f['subheader'] = wb.add_format({
        'bold': True, 'font_size': 10, 'font_color': C['muted'],
        'bg_color': C['cream'], 'align': 'center', 'valign': 'vcenter',
        'font_name': 'Calibri', 'top': 1, 'bottom': 1,
        'top_color': C['border'], 'bottom_color': C['border'],
    })

    f['kpi_value'] = wb.add_format({
        'bold': True, 'font_size': 16, 'font_color': C['terracotta'],
        'bg_color': C['white'], 'align': 'center', 'valign': 'vcenter',
        'font_name': 'Calibri', 'num_format': '"$"#,##0.00',
    })

    f['kpi_value_sage'] = wb.add_format({
        'bold': True, 'font_size': 16, 'font_color': C['sage'],
        'bg_color': C['white'], 'align': 'center', 'valign': 'vcenter',
        'font_name': 'Calibri', 'num_format': '"$"#,##0.00',
    })

    f['kpi_value_coral'] = wb.add_format({
        'bold': True, 'font_size': 16, 'font_color': C['coral'],
        'bg_color': C['white'], 'align': 'center', 'valign': 'vcenter',
        'font_name': 'Calibri', 'num_format': '"$"#,##0.00',
    })

    f['kpi_value_pct'] = wb.add_format({
        'bold': True, 'font_size': 16, 'font_color': C['terracotta'],
        'bg_color': C['white'], 'align': 'center', 'valign': 'vcenter',
        'font_name': 'Calibri', 'num_format': '0%',
    })

    f['kpi_label'] = wb.add_format({
        'font_size': 9, 'font_color': C['muted'],
        'bg_color': C['white'], 'align': 'center', 'valign': 'vcenter',
        'font_name': 'Calibri',
    })

    f['col_header'] = wb.add_format({
        'bold': True, 'font_size': 10, 'font_color': C['white'],
        'bg_color': C['coral'], 'align': 'center', 'valign': 'vcenter',
        'font_name': 'Calibri', 'border': 1, 'border_color': C['border'],
    })

    f['data_normal'] = wb.add_format({
        'font_size': 10, 'font_color': C['charcoal'],
        'bg_color': C['white'], 'valign': 'vcenter',
        'font_name': 'Calibri', 'border': 1, 'border_color': C['border'],
    })

    f['data_input'] = wb.add_format({
        'font_size': 10, 'font_color': C['charcoal'],
        'bg_color': C['input_bg'], 'valign': 'vcenter',
        'font_name': 'Calibri', 'border': 1, 'border_color': C['border'],
    })

    f['data_currency'] = wb.add_format({
        'font_size': 10, 'font_color': C['charcoal'],
        'bg_color': C['white'], 'valign': 'vcenter', 'align': 'right',
        'font_name': 'Calibri', 'border': 1, 'border_color': C['border'],
        'num_format': '"$"#,##0.00',
    })

    f['data_date'] = wb.add_format({
        'font_size': 10, 'font_color': C['charcoal'],
        'bg_color': C['white'], 'valign': 'vcenter', 'align': 'center',
        'font_name': 'Calibri', 'border': 1, 'border_color': C['border'],
        'num_format': 'mm/dd/yyyy',
    })

    f['income_row'] = wb.add_format({
        'font_size': 10, 'font_color': '#2E7D32',
        'bg_color': C['pos_bg'], 'valign': 'vcenter',
        'font_name': 'Calibri', 'border': 1, 'border_color': C['border'],
    })

    f['income_currency'] = wb.add_format({
        'font_size': 10, 'font_color': '#2E7D32',
        'bg_color': C['pos_bg'], 'valign': 'vcenter', 'align': 'right',
        'font_name': 'Calibri', 'border': 1, 'border_color': C['border'],
        'num_format': '"$"#,##0.00',
    })

    f['income_date'] = wb.add_format({
        'font_size': 10, 'font_color': '#2E7D32',
        'bg_color': C['pos_bg'], 'valign': 'vcenter', 'align': 'center',
        'font_name': 'Calibri', 'border': 1, 'border_color': C['border'],
        'num_format': 'mm/dd/yyyy',
    })

    f['section_label'] = wb.add_format({
        'bold': True, 'font_size': 11, 'font_color': C['white'],
        'bg_color': C['sage'], 'align': 'center', 'valign': 'vcenter',
        'font_name': 'Calibri',
    })

    f['savings_header'] = wb.add_format({
        'bold': True, 'font_size': 10, 'font_color': C['white'],
        'bg_color': C['terracotta'], 'align': 'center', 'valign': 'vcenter',
        'font_name': 'Calibri', 'border': 1, 'border_color': C['border'],
    })

    f['savings_data'] = wb.add_format({
        'font_size': 10, 'font_color': C['charcoal'],
        'bg_color': C['white'], 'valign': 'vcenter',
        'font_name': 'Calibri', 'border': 1, 'border_color': C['border'],
    })

    f['savings_pct'] = wb.add_format({
        'font_size': 10, 'font_color': C['charcoal'],
        'bg_color': C['white'], 'valign': 'vcenter', 'align': 'center',
        'font_name': 'Calibri', 'border': 1, 'border_color': C['border'],
        'num_format': '0%',
    })

    f['savings_currency'] = wb.add_format({
        'font_size': 10, 'font_color': C['charcoal'],
        'bg_color': C['white'], 'valign': 'vcenter', 'align': 'right',
        'font_name': 'Calibri', 'border': 1, 'border_color': C['border'],
        'num_format': '"$"#,##0.00',
    })

    f['progress_bar'] = wb.add_format({
        'font_size': 9, 'font_color': C['sage'],
        'bg_color': C['white'], 'valign': 'vcenter',
        'font_name': 'Courier New', 'border': 1, 'border_color': C['border'],
    })

    f['status_on_track'] = wb.add_format({
        'bold': True, 'font_size': 10, 'font_color': '#2E7D32',
        'bg_color': C['pos_bg'], 'align': 'center', 'valign': 'vcenter',
        'font_name': 'Calibri', 'border': 1, 'border_color': C['border'],
    })

    f['status_behind'] = wb.add_format({
        'bold': True, 'font_size': 10, 'font_color': '#E65100',
        'bg_color': C['neg_bg'], 'align': 'center', 'valign': 'vcenter',
        'font_name': 'Calibri', 'border': 1, 'border_color': C['border'],
    })

    f['dash_label'] = wb.add_format({
        'bold': True, 'font_size': 10, 'font_color': C['muted'],
        'bg_color': C['cream'], 'align': 'center', 'valign': 'vcenter',
        'font_name': 'Calibri',
    })

    f['dash_value'] = wb.add_format({
        'bold': True, 'font_size': 14, 'font_color': C['terracotta'],
        'bg_color': C['white'], 'align': 'center', 'valign': 'vcenter',
        'font_name': 'Calibri', 'num_format': '"$"#,##0.00',
    })

    f['empty'] = wb.add_format({'bg_color': C['cream']})

    return f


def write_banner(ws, fmt, title, ncols=8):
    """Write merged banner header row at row 0."""
    ws.merge_range(0, 0, 0, ncols - 1, title, fmt['banner'])
    ws.set_row(0, 36)


def write_kpi_row(ws, fmt, labels, row_label=1, row_value=2):
    """
    Write a 3-column KPI card block starting at col 0.
    labels: list of 3 dicts with keys 'label', 'formula', 'color'
    color: 'terracotta' | 'coral' | 'sage'
    """
    color_map = {
        'terracotta': fmt['kpi_value'],
        'coral':      fmt['kpi_value_coral'],
        'sage':       fmt['kpi_value_sage'],
    }
    col_spans = [(0, 2), (3, 5), (6, 8)]
    for i, card in enumerate(labels):
        c0, c1 = col_spans[i]
        ws.merge_range(row_label, c0, row_label, c1, card['label'], fmt['kpi_label'])
        ws.merge_range(row_value, c0, row_value, c1, '', color_map[card['color']])
        ws.write_formula(row_value, c0, card['formula'], color_map[card['color']])
    ws.set_row(row_label, 18)
    ws.set_row(row_value, 32)
