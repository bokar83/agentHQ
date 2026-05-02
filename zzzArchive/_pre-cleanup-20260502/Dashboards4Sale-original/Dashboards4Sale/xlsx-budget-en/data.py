# Dashboards4Sale/xlsx-budget-en/data.py
from datetime import date

TITLE = 'Monthly Budget Planner | Google Sheets'

CATEGORIES = [
    'Housing', 'Food', 'Transport', 'Utilities', 'Subscriptions',
    'Dining Out', 'Health', 'Shopping', 'Entertainment',
    'Personal Care', 'Education', 'Savings Transfer', 'Income', 'Other',
]

TYPES = ['Income', 'Expense']

# [date, description, category, type, amount]
SAMPLE_TRANSACTIONS = [
    [date(2026, 4,  1), 'Paycheck',         'Income',           'Income',   3500],
    [date(2026, 4,  3), 'Rent',             'Housing',          'Expense',  1200],
    [date(2026, 4,  5), 'Groceries',        'Food',             'Expense',   187],
    [date(2026, 4,  8), 'Electric bill',    'Utilities',        'Expense',    94],
    [date(2026, 4, 10), 'Netflix',          'Subscriptions',    'Expense',    16],
    [date(2026, 4, 12), 'Gas',              'Transport',        'Expense',    52],
    [date(2026, 4, 15), 'Paycheck',         'Income',           'Income',   3500],
    [date(2026, 4, 17), 'Dinner out',       'Dining Out',       'Expense',    67],
    [date(2026, 4, 20), 'Groceries',        'Food',             'Expense',   143],
    [date(2026, 4, 22), 'Internet',         'Utilities',        'Expense',    60],
    [date(2026, 4, 24), 'Amazon',           'Shopping',         'Expense',    35],
    [date(2026, 4, 26), 'Coffee',           'Dining Out',       'Expense',    23],
    [date(2026, 4, 28), 'Car insurance',    'Transport',        'Expense',   120],
    [date(2026, 4, 29), 'Gym',              'Health',           'Expense',    35],
    [date(2026, 4, 30), 'Savings transfer', 'Savings Transfer', 'Expense',   500],
]

HEADERS = ['Date', 'Description', 'Category', 'Type', 'Amount']

KPI_LABELS = {
    'income':    'INCOME',
    'spent':     'SPENT',
    'remaining': 'REMAINING',
}

BANNER_LABEL    = 'BUDGET'
SAVINGS_LABEL   = 'SAVINGS'
DASHBOARD_LABEL = 'DASHBOARD'

SAVINGS_HEADERS = [
    'Goal', 'Target', 'Saved', 'Target Date', '% Funded',
    'Monthly Needed', 'Progress', 'Status',
]

# [goal_name, target_amount, saved_amount, target_date]
SAMPLE_GOALS = [
    ['Emergency Fund', 5000, 1800, date(2026, 12, 31)],
    ['Vacation',       2000,  650, date(2026,  8,  1)],
    ['New Laptop',     1200,  400, date(2026,  7,  1)],
]

INCOME_TYPE  = 'Income'
EXPENSE_TYPE = 'Expense'

STATUS_ON_TRACK = 'On Track'
STATUS_BEHIND   = 'Behind'

# xlsxwriter num_format strings
CURRENCY_FORMAT = '"$"#,##0.00'
PCT_FORMAT      = '0%'
DATE_FORMAT     = 'mm/dd/yyyy'

DASHBOARD_LABELS = {
    'spending_split':   'SPENDING SPLIT',
    'spending':         'Spending',
    'savings_label':    'Savings',
    'top_savings_goal': 'TOP SAVINGS GOAL',
}
