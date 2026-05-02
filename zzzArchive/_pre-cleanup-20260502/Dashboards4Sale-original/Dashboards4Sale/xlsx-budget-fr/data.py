# Dashboards4Sale/xlsx-budget-fr/data.py
from datetime import date

TITLE = 'Modele Budget Mensuel | Google Sheets'

CATEGORIES = [
    'Logement', 'Alimentation', 'Transport', 'Factures', 'Abonnements',
    'Restaurants', 'Sante', 'Shopping', 'Loisirs',
    'Soins personnels', 'Education', 'Virement epargne', 'Revenu', 'Autre',
]

TYPES = ['Revenu', 'Depense']

SAMPLE_TRANSACTIONS = [
    [date(2026, 4,  1), 'Salaire',           'Revenu',           'Revenu',  3500],
    [date(2026, 4,  3), 'Loyer',             'Logement',         'Depense', 1200],
    [date(2026, 4,  5), 'Courses Carrefour', 'Alimentation',     'Depense',  187],
    [date(2026, 4,  8), 'Electricite EDF',   'Factures',         'Depense',   94],
    [date(2026, 4, 10), 'Netflix',           'Abonnements',      'Depense',   16],
    [date(2026, 4, 12), 'Essence',           'Transport',        'Depense',   52],
    [date(2026, 4, 15), 'Salaire',           'Revenu',           'Revenu',  3500],
    [date(2026, 4, 17), 'Restaurant',        'Restaurants',      'Depense',   67],
    [date(2026, 4, 20), 'Courses Monoprix',  'Alimentation',     'Depense',  143],
    [date(2026, 4, 22), 'Internet Orange',   'Factures',         'Depense',   60],
    [date(2026, 4, 24), 'Commande Amazon',   'Shopping',         'Depense',   35],
    [date(2026, 4, 26), 'Cafe',              'Restaurants',      'Depense',   23],
    [date(2026, 4, 28), 'Assurance auto',    'Transport',        'Depense',  120],
    [date(2026, 4, 29), 'Salle de sport',    'Sante',            'Depense',   35],
    [date(2026, 4, 30), 'Virement epargne',  'Virement epargne', 'Depense',  500],
]

HEADERS = ['Date', 'Description', 'Categorie', 'Type', 'Montant']

KPI_LABELS = {
    'income':    'REVENUS',
    'spent':     'DEPENSES',
    'remaining': 'SOLDE',
}

BANNER_LABEL    = 'BUDGET'
SAVINGS_LABEL   = 'EPARGNE'
DASHBOARD_LABEL = 'TABLEAU DE BORD'

SAVINGS_HEADERS = [
    'Objectif', 'Cible', 'Epargne', 'Date cible',
    '% Atteint', 'Mensuel', 'Progression', 'Statut',
]

SAMPLE_GOALS = [
    ["Fonds d'urgence", 5000, 1800, date(2026, 12, 31)],
    ['Vacances',         2000,  650, date(2026,  8,  1)],
    ['Nouvel ordinateur', 1200, 400, date(2026,  7,  1)],
]

INCOME_TYPE  = 'Revenu'
EXPENSE_TYPE = 'Depense'

STATUS_ON_TRACK = 'En cours'
STATUS_BEHIND   = 'En retard'

CURRENCY_FORMAT = '#,##0.00 "\u20ac"'
PCT_FORMAT      = '0%'
DATE_FORMAT     = 'dd/mm/yyyy'

DASHBOARD_LABELS = {
    'spending_split':   'REPARTITION DEPENSES',
    'spending':         'Depenses',
    'savings_label':    'Epargne',
    'top_savings_goal': 'OBJECTIF EPARGNE',
}
