// budget-template-fr/data.js
export const TITLE = 'Modele Budget Mensuel | Google Sheets';

export const CATEGORIES = [
  'Logement','Alimentation','Transport','Factures','Abonnements',
  'Restaurants','Sante','Shopping','Loisirs',
  'Soins personnels','Education','Virement epargne','Revenu','Autre'
];

export const TYPES = ['Revenu', 'Depense'];

export const SAMPLE_TRANSACTIONS = [
  ['01/04/2026', 'Salaire',            'Revenu',           'Revenu',   3500],
  ['03/04/2026', 'Loyer',              'Logement',         'Depense',  1200],
  ['05/04/2026', 'Courses Carrefour',  'Alimentation',     'Depense',   187],
  ['08/04/2026', 'Electricite EDF',    'Factures',         'Depense',    94],
  ['10/04/2026', 'Netflix',            'Abonnements',      'Depense',    16],
  ['12/04/2026', 'Essence',            'Transport',        'Depense',    52],
  ['15/04/2026', 'Salaire',            'Revenu',           'Revenu',   3500],
  ['17/04/2026', 'Restaurant',         'Restaurants',      'Depense',    67],
  ['20/04/2026', 'Courses Monoprix',   'Alimentation',     'Depense',   143],
  ['22/04/2026', 'Internet Orange',    'Factures',         'Depense',    60],
  ['24/04/2026', 'Commande Amazon',    'Shopping',         'Depense',    35],
  ['26/04/2026', 'Cafe',               'Restaurants',      'Depense',    23],
  ['28/04/2026', 'Assurance auto',     'Transport',        'Depense',   120],
  ['29/04/2026', 'Salle de sport',     'Sante',            'Depense',    35],
  ['30/04/2026', 'Virement epargne',   'Virement epargne', 'Depense',   500],
];

export const HEADERS = ['Date', 'Description', 'Categorie', 'Type', 'Montant'];

export const KPI_LABELS = {
  income:      'REVENUS',
  spent:       'DEPENSES',
  remaining:   'SOLDE',
  thisMonth:   'Ce mois-ci',
  underBudget: '✓ Dans le budget',
  overBudget:  '⚠ Depassement',
};

export const BANNER_LABELS = {
  budget:    'BUDGET',
  savings:   'EPARGNE',
  dashboard: 'TABLEAU DE BORD',
};

export const SAVINGS_HEADERS = [
  'Objectif','Cible','Epargne','Date cible','% Atteint','Mensuel','Progression','Statut'
];

export const SAMPLE_GOALS = [
  ["Fonds d'urgence", 5000, 1800, '31/12/2026'],
  ['Vacances',        2000,  650, '01/08/2026'],
  ['Nouvel ordinateur', 1200, 400, '01/07/2026'],
];

export const INCOME_TYPE  = 'Revenu';
export const EXPENSE_TYPE = 'Depense';
export const CURRENCY_FORMAT = '#,##0.00 "€"';
export const PCT_FORMAT = '0%';

export const DASHBOARD_LABELS = {
  spendingSplit:  'REPARTITION DEPENSES',
  spending:       'Depenses',
  savingsLabel:   'Epargne',
  topSavingsGoal: 'OBJECTIF EPARGNE',
};
