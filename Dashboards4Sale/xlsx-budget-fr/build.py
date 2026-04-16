# Dashboards4Sale/xlsx-budget-fr/build.py
"""Build budget_fr.xlsx - Modele Budget Mensuel (Francais)."""
import sys
import xlsxwriter
from datetime import datetime

sys.path.insert(0, 'Dashboards4Sale/shared')
sys.path.insert(0, 'Dashboards4Sale/xlsx-budget-fr')

from xl_builder import add_formats, COLORS
from data import (
    TITLE, CATEGORIES, TYPES, SAMPLE_TRANSACTIONS, HEADERS,
    KPI_LABELS, BANNER_LABEL, SAVINGS_LABEL, DASHBOARD_LABEL,
    SAMPLE_GOALS, SAVINGS_HEADERS, INCOME_TYPE, EXPENSE_TYPE,
    STATUS_ON_TRACK, STATUS_BEHIND,
    CURRENCY_FORMAT, PCT_FORMAT, DATE_FORMAT, DASHBOARD_LABELS,
)

OUTPUT = 'Dashboards4Sale/xlsx-budget-fr/budget_fr.xlsx'
BLANK_ROWS = 35


def build():
    wb = xlsxwriter.Workbook(OUTPUT, {'strings_to_numbers': False})
    wb.set_properties({'title': TITLE})
    fmt = add_formats(wb)

    for key in ('kpi_value', 'kpi_value_coral', 'kpi_value_sage',
                'data_currency', 'income_currency', 'savings_currency', 'dash_value'):
        fmt[key].set_num_format(CURRENCY_FORMAT)
    for key in ('data_date', 'income_date'):
        fmt[key].set_num_format(DATE_FORMAT)
    fmt['savings_pct'].set_num_format(PCT_FORMAT)

    build_budget_tab(wb, fmt)
    build_savings_tab(wb, fmt)
    build_dashboard_tab(wb, fmt)

    wb.close()
    print(f'Built: {OUTPUT}')


def build_budget_tab(wb, fmt):
    ws = wb.add_worksheet(BANNER_LABEL)
    ws.set_zoom(90)
    ws.hide_gridlines(2)

    ws.set_column(0, 0, 13)
    ws.set_column(1, 1, 28)
    ws.set_column(2, 2, 18)
    ws.set_column(3, 3, 12)
    ws.set_column(4, 4, 14)

    ws.merge_range(0, 0, 0, 4, BANNER_LABEL, fmt['banner'])
    ws.set_row(0, 36)

    ws.set_row(1, 18)
    ws.write(1, 0, KPI_LABELS['income'],    fmt['kpi_label'])
    ws.merge_range(1, 1, 1, 2, KPI_LABELS['spent'],     fmt['kpi_label'])
    ws.merge_range(1, 3, 1, 4, KPI_LABELS['remaining'], fmt['kpi_label'])

    ws.set_row(2, 34)
    ws.write_formula(2, 0, f'=SUMIF(D:D,"{INCOME_TYPE}",E:E)', fmt['kpi_value'])
    ws.merge_range(2, 1, 2, 2, '', fmt['kpi_value_coral'])
    ws.write_formula(2, 1, f'=SUMIF(D:D,"{EXPENSE_TYPE}",E:E)', fmt['kpi_value_coral'])
    ws.merge_range(2, 3, 2, 4, '', fmt['kpi_value_sage'])
    ws.write_formula(2, 3, '=A3-B3', fmt['kpi_value_sage'])

    ws.set_row(3, 8)
    for c in range(5):
        ws.write_blank(3, c, None, fmt['empty'])

    ws.set_row(4, 22)
    for c, h in enumerate(HEADERS):
        ws.write(4, c, h, fmt['col_header'])

    first_data_row = 5
    for i, tx in enumerate(SAMPLE_TRANSACTIONS):
        r = first_data_row + i
        ws.set_row(r, 18)
        tx_date, desc, cat, tx_type, amount = tx
        is_income = (tx_type == INCOME_TYPE)
        row_fmt  = fmt['income_row']      if is_income else fmt['data_normal']
        date_fmt = fmt['income_date']     if is_income else fmt['data_date']
        curr_fmt = fmt['income_currency'] if is_income else fmt['data_currency']

        ws.write_datetime(r, 0,
            datetime(tx_date.year, tx_date.month, tx_date.day), date_fmt)
        ws.write(r, 1, desc,    row_fmt)
        ws.write(r, 2, cat,     row_fmt)
        ws.write(r, 3, tx_type, row_fmt)
        ws.write(r, 4, amount,  curr_fmt)

    blank_start = first_data_row + len(SAMPLE_TRANSACTIONS)
    for i in range(BLANK_ROWS):
        r = blank_start + i
        ws.set_row(r, 18)
        ws.write_blank(r, 0, None, fmt['data_date'])
        ws.write_blank(r, 1, None, fmt['data_input'])
        ws.write_blank(r, 2, None, fmt['data_input'])
        ws.write_blank(r, 3, None, fmt['data_input'])
        ws.write_blank(r, 4, None, fmt['data_currency'])

    last_data_row = blank_start + BLANK_ROWS - 1

    ws.data_validation(first_data_row, 2, last_data_row, 2, {
        'validate': 'list',
        'source':   CATEGORIES,
    })
    ws.data_validation(first_data_row, 3, last_data_row, 3, {
        'validate': 'list',
        'source':   TYPES,
    })

    ws.freeze_panes(5, 0)
    ws.set_tab_color(COLORS['terracotta'])


def build_savings_tab(wb, fmt):
    ws = wb.add_worksheet(SAVINGS_LABEL)
    ws.set_zoom(90)
    ws.hide_gridlines(2)
    ws.set_tab_color(COLORS['sage'])

    ws.set_column(0, 0, 22)
    ws.set_column(1, 1, 12)
    ws.set_column(2, 2, 12)
    ws.set_column(3, 3, 14)
    ws.set_column(4, 4, 10)
    ws.set_column(5, 5, 16)
    ws.set_column(6, 6, 22)
    ws.set_column(7, 7, 12)

    ws.merge_range(0, 0, 0, 7, SAVINGS_LABEL, fmt['banner'])
    ws.set_row(0, 36)

    ws.set_row(1, 8)

    ws.set_row(2, 22)
    for c, h in enumerate(SAVINGS_HEADERS):
        ws.write(2, c, h, fmt['savings_header'])

    dt = datetime
    today = dt.today().date()
    for i, goal in enumerate(SAMPLE_GOALS):
        r = 3 + i
        ws.set_row(r, 22)
        name, target, saved, target_date = goal

        pct = saved / target if target else 0
        filled = round(pct * 20)
        bar = '\u2588' * filled + '\u2591' * (20 - filled)
        months_left = max(1, (target_date.year - today.year) * 12
                          + (target_date.month - today.month))
        monthly = (target - saved) / months_left
        status = STATUS_ON_TRACK if pct >= 0.25 else STATUS_BEHIND
        status_fmt = fmt['status_on_track'] if status == STATUS_ON_TRACK else fmt['status_behind']

        ws.write(r, 0, name,   fmt['savings_data'])
        ws.write(r, 1, target, fmt['savings_currency'])
        ws.write(r, 2, saved,  fmt['savings_currency'])
        ws.write_datetime(r, 3,
            dt(target_date.year, target_date.month, target_date.day),
            fmt['savings_data'])
        ws.write(r, 4, pct,     fmt['savings_pct'])
        ws.write(r, 5, monthly, fmt['savings_currency'])
        ws.write(r, 6, bar,     fmt['progress_bar'])
        ws.write(r, 7, status,  status_fmt)

    blank_start = 3 + len(SAMPLE_GOALS)
    for i in range(7):
        r = blank_start + i
        ws.set_row(r, 22)
        for c in range(8):
            ws.write_blank(r, c, None, fmt['savings_data'])

    ws.freeze_panes(3, 0)


def build_dashboard_tab(wb, fmt):
    ws = wb.add_worksheet(DASHBOARD_LABEL)
    ws.set_zoom(90)
    ws.hide_gridlines(2)
    ws.set_tab_color(COLORS['coral'])

    ws.set_column(0, 0, 3)
    ws.set_column(1, 5, 18)
    ws.set_column(6, 6, 3)

    ws.merge_range(0, 0, 0, 6, DASHBOARD_LABEL, fmt['banner'])
    ws.set_row(0, 36)

    ws.set_row(1, 8)
    ws.set_row(2, 18)
    ws.set_row(3, 34)
    ws.set_row(4, 8)

    kpi_cards = [
        {'col': 1, 'label': KPI_LABELS['income'],
         'formula': f'={BANNER_LABEL}!A3', 'fmt_key': 'kpi_value'},
        {'col': 2, 'label': KPI_LABELS['spent'],
         'formula': f'={BANNER_LABEL}!B3', 'fmt_key': 'kpi_value_coral'},
        {'col': 3, 'label': KPI_LABELS['remaining'],
         'formula': f'={BANNER_LABEL}!D3', 'fmt_key': 'kpi_value_sage'},
        {'col': 4, 'label': 'TAUX EPARGNE',
         'formula': f'=IF({BANNER_LABEL}!A3=0,0,{BANNER_LABEL}!D3/{BANNER_LABEL}!A3)',
         'fmt_key': 'kpi_value_pct'},
    ]
    for card in kpi_cards:
        ws.write(2, card['col'], card['label'], fmt['kpi_label'])
        ws.write_formula(3, card['col'], card['formula'], fmt[card['fmt_key']])

    expense_cats = [c for c in CATEGORIES
                    if c not in (INCOME_TYPE, 'Virement epargne', 'Autre')]
    ws.write(1, 7, 'Categorie', fmt['subheader'])
    ws.write(1, 8, 'Montant',   fmt['subheader'])
    for i, cat in enumerate(expense_cats):
        r = 2 + i
        ws.write(r, 7, cat, fmt['data_normal'])
        ws.write_formula(r, 8,
            f'=SUMIF({BANNER_LABEL}!C:C,H{r+1},{BANNER_LABEL}!E:E)',
            fmt['data_currency'])

    ws.write(1, 10, 'Categorie', fmt['subheader'])
    ws.write(1, 11, 'Montant',   fmt['subheader'])
    ws.write(2, 10, KPI_LABELS['income'], fmt['data_normal'])
    ws.write_formula(2, 11, f'={BANNER_LABEL}!A3', fmt['data_currency'])
    ws.write(3, 10, KPI_LABELS['spent'],  fmt['data_normal'])
    ws.write_formula(3, 11, f'={BANNER_LABEL}!B3', fmt['data_currency'])

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

    bar = wb.add_chart({'type': 'bar'})
    bar.add_series({
        'name':       DASHBOARD_LABELS['spending'],
        'categories': [DASHBOARD_LABEL, 2, 10, 3, 10],
        'values':     [DASHBOARD_LABEL, 2, 11, 3, 11],
        'fill':       {'colors': [COLORS['sage'], COLORS['coral']]},
        'data_labels': {'value': True,
                        'num_format': '#,##0 "\u20ac"',
                        'font': {'size': 9}},
    })
    bar.set_title({'name': 'Revenus vs Depenses',
                   'name_font': {'bold': True, 'size': 12,
                                 'color': COLORS['charcoal']}})
    bar.set_legend({'none': True})
    bar.set_size({'width': 380, 'height': 240})
    bar.set_chartarea({'border': {'color': COLORS['border']},
                       'fill':   {'color': COLORS['cream']}})
    bar.set_plotarea({'fill': {'color': COLORS['cream']}})
    ws.insert_chart(21, 1, bar, {'x_offset': 5, 'y_offset': 5})

    ws.freeze_panes(1, 0)


if __name__ == '__main__':
    build()
