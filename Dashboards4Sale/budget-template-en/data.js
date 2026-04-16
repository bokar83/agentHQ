// budget-template-en/data.js
export const TITLE = 'Monthly Budget Planner | Google Sheets';

export const CATEGORIES = [
  'Housing','Food','Transport','Utilities','Subscriptions',
  'Dining Out','Health','Shopping','Entertainment',
  'Personal Care','Education','Savings Transfer','Income','Other'
];

export const TYPES = ['Income', 'Expense'];

export const SAMPLE_TRANSACTIONS = [
  ['04/01/2026', 'Paycheck',        'Income',           'Income',  3500],
  ['04/03/2026', 'Rent',            'Housing',          'Expense', 1200],
  ['04/05/2026', 'Groceries',       'Food',             'Expense',  187],
  ['04/08/2026', 'Electric bill',   'Utilities',        'Expense',   94],
  ['04/10/2026', 'Netflix',         'Subscriptions',    'Expense',   16],
  ['04/12/2026', 'Gas',             'Transport',        'Expense',   52],
  ['04/15/2026', 'Paycheck',        'Income',           'Income',  3500],
  ['04/17/2026', 'Dinner out',      'Dining Out',       'Expense',   67],
  ['04/20/2026', 'Groceries',       'Food',             'Expense',  143],
  ['04/22/2026', 'Internet',        'Utilities',        'Expense',   60],
  ['04/24/2026', 'Amazon',          'Shopping',         'Expense',   35],
  ['04/26/2026', 'Coffee',          'Dining Out',       'Expense',   23],
  ['04/28/2026', 'Car insurance',   'Transport',        'Expense',  120],
  ['04/29/2026', 'Gym',             'Health',           'Expense',   35],
  ['04/30/2026', 'Savings transfer','Savings Transfer', 'Expense',  500],
];

export const HEADERS = ['Date', 'Description', 'Category', 'Type', 'Amount'];

export const KPI_LABELS = {
  income:      'INCOME',
  spent:       'SPENT',
  remaining:   'REMAINING',
  thisMonth:   'This month',
  underBudget: '✓ Under budget',
  overBudget:  '⚠ Over budget',
};

export const BANNER_LABELS = {
  budget:    'BUDGET',
  savings:   'SAVINGS',
  dashboard: 'DASHBOARD',
};

export const SAVINGS_HEADERS = [
  'Goal','Target','Saved','Target Date','% Funded','Monthly Needed','Progress','Status'
];

export const SAMPLE_GOALS = [
  ['Emergency Fund', 5000, 1800, '12/31/2026'],
  ['Vacation',       2000,  650, '08/01/2026'],
  ['New Laptop',     1200,  400, '07/01/2026'],
];

export const INCOME_TYPE  = 'Income';
export const EXPENSE_TYPE = 'Expense';
export const CURRENCY_FORMAT = '"$"#,##0.00';
export const PCT_FORMAT = '0%';

export const DASHBOARD_LABELS = {
  spendingSplit:  'SPENDING SPLIT',
  spending:       'Spending',
  savingsLabel:   'Savings',
  topSavingsGoal: 'TOP SAVINGS GOAL',
};
