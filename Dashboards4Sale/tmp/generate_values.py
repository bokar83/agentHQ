"""
Generates and applies ALL cell values to the Smart 50/30/20 Budget Planner.
"""
import json, os, subprocess

SHEET_ID = "1pkO1G5q_qDe0nLCm7W12O3-jurzYKH16bcw8X5AOmQ0"
GIT_BASH  = r"C:\Program Files\Git\bin\bash.exe"
OUT       = r"D:\Ai_Sandbox\agentsHQ\Dashboards4Sale\tmp"

def to_unix(p):
    p = p.replace("\\", "/")
    if len(p) > 1 and p[1] == ":":
        p = "/" + p[0].lower() + p[2:]
    return p

def apply_values(data_list, label):
    payload = {"valueInputOption": "USER_ENTERED", "data": data_list}
    fname = os.path.join(OUT, "_vtmp.json")
    with open(fname, "w", encoding="utf-8") as f:
        json.dump(payload, f)
    unix = to_unix(fname)
    cmd = (f"gws sheets spreadsheets values batchUpdate "
           f"--params '{{\"spreadsheetId\":\"{SHEET_ID}\"}}' "
           f"--json \"$(cat '{unix}')\"")
    r = subprocess.run([GIT_BASH, "-c", cmd],
                       capture_output=True, text=True, encoding="utf-8", errors="replace")
    os.remove(fname)
    out = r.stdout + r.stderr
    if "totalUpdatedCells" in out or "updatedCells" in out:
        print(f"  OK  {label}")
    else:
        print(f"  ERR {label}: {out[:250]}")

def col(n):
    """0-indexed column number to letter(s)."""
    result = ""
    n += 1
    while n:
        n, r = divmod(n - 1, 26)
        result = chr(65 + r) + result
    return result

# ═══════════════════════════════════════════════════════════════════════════════
# _REF TAB
# ═══════════════════════════════════════════════════════════════════════════════
print("Applying _Ref data...")
months = ["January","February","March","April","May","June",
          "July","August","September","October","November","December"]
categories = [
    "Salary / Wages","Freelance / Side Income","Business Income","Rental Income",
    "Dividends / Interest","Other Income",
    "Housing / Rent","Mortgage","HOA / Condo Fees",
    "Groceries","Dining Out","Coffee & Drinks",
    "Electric","Gas & Heating","Water & Sewer","Internet","Phone",
    "Car Payment","Gas Station","Parking","Public Transit","Rideshare",
    "Health Insurance","Doctor / Copay","Dentist","Pharmacy","Gym / Fitness",
    "Entertainment","Subscriptions","Shopping","Clothing","Personal Care",
    "Savings & Investing","Emergency Fund","Retirement / IRA",
    "Debt Payment","Vacation Fund",
]
apply_values([
    {"range": "_Ref!A1",  "values": [["Month"]]},
    {"range": "_Ref!A2",  "values": [[m] for m in months]},
    {"range": "_Ref!C1",  "values": [["Budget"]]},
    {"range": "_Ref!C2",  "values": [["Needs"],["Wants"],["Savings"]]},
    {"range": "_Ref!K1",  "values": [["Category"]]},
    {"range": "_Ref!K2",  "values": [[c] for c in categories]},
    {"range": "_Ref!M1",  "values": [["Type"]]},
    {"range": "_Ref!M2",  "values": [["Income"],["Expense"]]},
], "_Ref lookups")

# ═══════════════════════════════════════════════════════════════════════════════
# SETUP TAB
# ═══════════════════════════════════════════════════════════════════════════════
print("Applying Setup data...")
apply_values([
    {"range": "Setup!A1", "values": [["Smart 50/30/20 Monthly Budget Planner"]]},
    {"range": "Setup!A2", "values": [["Configure your budget once — all tabs update automatically"]]},
    {"range": "Setup!A3:C3", "values": [["", "Active Month:", "March"]]},
    {"range": "Setup!A4",  "values": [["  INCOME SOURCES"]]},
    {"range": "Setup!A5:C5",  "values": [["", "Primary Income (Salary / Wages)", 5500]]},
    {"range": "Setup!A6:C6",  "values": [["", "Secondary Income (Freelance / Gig Work)", 800]]},
    {"range": "Setup!A7:C7",  "values": [["", "Other Income (Dividends / Rental / Other)", 200]]},
    {"range": "Setup!A8:C8",  "values": [["", "TOTAL MONTHLY INCOME", "=SUM(C5:C7)"]]},
    {"range": "Setup!A10", "values": [["  BUDGET SPLIT RATIOS  (must total 100)"]]},
    {"range": "Setup!A11:C11","values": [["", "Needs  (housing, food, utilities, transport)", 50]]},
    {"range": "Setup!A12:C12","values": [["", "Wants  (dining, entertainment, shopping, subs)", 30]]},
    {"range": "Setup!A13:C13","values": [["", "Savings & Debt  (emergency, retirement, debt)", 20]]},
    {"range": "Setup!A14:C14","values": [["", "TOTAL  (must equal 100)", "=C11+C12+C13"]]},
    {"range": "Setup!A16", "values": [["  CALCULATED MONTHLY BUDGETS"]]},
    {"range": "Setup!A17:C17","values": [["", "Needs Budget (50%)",           "=C8*C11/100"]]},
    {"range": "Setup!A18:C18","values": [["", "Wants Budget (30%)",           "=C8*C12/100"]]},
    {"range": "Setup!A19:C19","values": [["", "Savings & Debt Budget (20%)",  "=C8*C13/100"]]},
    {"range": "Setup!A22", "values": [["  HOW TO USE THIS PLANNER"]]},
    {"range": "Setup!A23:E23","values": [["STEP","WHAT TO DO","WHERE","DETAILS","PRO TIP"]]},
    {"range": "Setup!A24:E24","values": [["1","Set Your Income","Setup > C5:C7","Enter all monthly income sources in the green input cells above.","Include irregular income (freelance, bonuses) as a monthly average."]]},
    {"range": "Setup!A25:E25","values": [["2","Choose Your Split","Setup > C11:C13","Adjust the Needs/Wants/Savings percentages. Default is 50/30/20.","Try 60/20/20 if your cost of living is high."]]},
    {"range": "Setup!A26:E26","values": [["3","Set Active Month","Setup > C3","Select the month you want the Dashboard to display using the dropdown.","Change this monthly to review each month's performance."]]},
    {"range": "Setup!A27:E27","values": [["4","Log Transactions","Transactions Tab","Enter every income and expense. Use the Type, Budget & Category dropdowns.","Log weekly — it takes 5 minutes and prevents end-of-month surprises."]]},
    {"range": "Setup!A28:E28","values": [["5","Track Your Debts","Debt Tracker Tab","Enter each debt with balance, APR, and monthly payment amount.","Snowball: pay off smallest balance first. Avalanche: highest APR first."]]},
    {"range": "Setup!A29:E29","values": [["6","Set Savings Goals","Savings Goals Tab","Add goals with target amounts and monthly contribution amounts.","Even $50/month adds up. Automate transfers on payday."]]},
    {"range": "Setup!A30:E30","values": [["7","Review Dashboard","Dashboard Tab","Your Dashboard auto-updates instantly as you log transactions.","Green = under budget. Red = over budget. Focus on the Wants bucket."]]},
    {"range": "Setup!A31:E31","values": [["8","Annual Review","Annual Overview Tab","See your full 12-month history: income, spending, and savings rate.","A savings rate above 20% puts you on track for financial freedom."]]},
    {"range": "Setup!A32:E32","values": [["9","Clear Sample Data","Budget Tools Menu","Use  Budget Tools > Clear Sample Data  to remove demo rows.","Your formatting and formulas stay — only the data rows are cleared."]]},
    {"range": "Setup!A34", "values": [["  QUICK TIPS FOR SUCCESS"]]},
    {"range": "Setup!A35:D35","values": [["1","Pay Yourself First","Transfer savings on payday before spending on anything else.","Automate it so it happens without thinking."]]},
    {"range": "Setup!A36:D36","values": [["2","The 24-Hour Rule","Wait 24 hours before any non-essential purchase over $50.","Eliminates ~80% of impulse buys."]]},
    {"range": "Setup!A37:D37","values": [["3","Track Every Dollar","Small purchases add up fast. Coffee 5x/week = $1,500/year.","Even $1 transactions matter for accuracy."]]},
    {"range": "Setup!A38:D38","values": [["4","Review Weekly","Spend 10 minutes each Sunday reviewing your Transactions tab.","Early awareness of overspending prevents month-end stress."]]},
    {"range": "Setup!A39:D39","values": [["5","Use the 50/30/20 Guide","Needs over 50%? Cut a recurring bill. Savings under 20%? Automate more.","Small consistent changes compound dramatically over years."]]},
], "Setup tab")

# ═══════════════════════════════════════════════════════════════════════════════
# TRANSACTIONS TAB — headers + 35 sample rows
# ═══════════════════════════════════════════════════════════════════════════════
print("Applying Transactions data...")
txn_rows = [
    ["Date","Description","Type","Budget","Category","Amount","Month","Cleared","Notes"],
    # INCOME
    ["03/01/2026","Salary - March Paycheck","Income","Needs","Salary / Wages",5500,"March","TRUE","Direct deposit"],
    ["03/15/2026","Freelance Client - Web Design","Income","Wants","Freelance / Side Income",800,"March","TRUE","Invoice #2026-03"],
    ["03/20/2026","Dividend Income - Brokerage","Income","Savings","Dividends / Interest",200,"March","TRUE","Q1 dividend"],
    # NEEDS — Housing & Bills
    ["03/01/2026","Rent Payment - March","Expense","Needs","Housing / Rent",1350,"March","TRUE","Auto-pay"],
    ["03/04/2026","Electric Bill","Expense","Needs","Electric",87.43,"March","TRUE",""],
    ["03/05/2026","Internet Service","Expense","Needs","Internet",59.99,"March","TRUE",""],
    ["03/10/2026","Phone Bill","Expense","Needs","Phone",65.00,"March","TRUE",""],
    ["03/15/2026","Water & Sewer Bill","Expense","Needs","Water & Sewer",35.50,"March","TRUE",""],
    # NEEDS — Groceries
    ["03/02/2026","Whole Foods Market","Expense","Needs","Groceries",124.52,"March","TRUE","Weekly shop"],
    ["03/07/2026","Kroger Grocery Run","Expense","Needs","Groceries",98.17,"March","TRUE",""],
    ["03/12/2026","Trader Joe's","Expense","Needs","Groceries",112.33,"March","TRUE",""],
    ["03/22/2026","Whole Foods - Restock","Expense","Needs","Groceries",89.45,"March","TRUE",""],
    ["03/28/2026","Kroger Weekly Shop","Expense","Needs","Groceries",76.88,"March","TRUE",""],
    # NEEDS — Transport
    ["03/06/2026","Shell Gas Station","Expense","Needs","Gas Station",45.00,"March","TRUE",""],
    ["03/14/2026","BP Gas Station","Expense","Needs","Gas Station",52.00,"March","TRUE",""],
    ["03/20/2026","Chevron Gas","Expense","Needs","Gas Station",48.00,"March","TRUE",""],
    ["03/08/2026","Car Insurance - Monthly","Expense","Needs","Health Insurance",118.00,"March","TRUE","Auto-pay"],
    # NEEDS — Health & Personal
    ["03/11/2026","Doctor Visit Copay","Expense","Needs","Doctor / Copay",25.00,"March","TRUE","Annual checkup"],
    ["03/18/2026","CVS Pharmacy","Expense","Needs","Pharmacy",28.75,"March","TRUE","Prescriptions"],
    ["03/25/2026","Haircut - Great Clips","Expense","Needs","Personal Care",35.00,"March","TRUE",""],
    # WANTS — Subscriptions
    ["03/01/2026","Netflix Subscription","Expense","Wants","Subscriptions",15.99,"March","TRUE","Auto-pay"],
    ["03/09/2026","Spotify Premium","Expense","Wants","Subscriptions",9.99,"March","TRUE","Auto-pay"],
    # WANTS — Entertainment
    ["03/16/2026","AMC Movie Tickets x2","Expense","Wants","Entertainment",28.00,"March","TRUE","Date night"],
    # WANTS — Dining & Coffee
    ["03/05/2026","Starbucks - Weekly Coffee","Expense","Wants","Coffee & Drinks",28.50,"March","TRUE",""],
    ["03/07/2026","Olive Garden - Family Dinner","Expense","Wants","Dining Out",67.00,"March","TRUE",""],
    ["03/14/2026","Chipotle - Lunch","Expense","Wants","Dining Out",32.50,"March","TRUE",""],
    ["03/21/2026","Local Brewery - Happy Hour","Expense","Wants","Coffee & Drinks",18.75,"March","TRUE",""],
    ["03/23/2026","Cheesecake Factory","Expense","Wants","Dining Out",42.00,"March","TRUE",""],
    # WANTS — Shopping
    ["03/12/2026","Amazon - Household Items","Expense","Wants","Shopping",45.67,"March","TRUE",""],
    ["03/19/2026","Old Navy - Spring Clothing","Expense","Wants","Clothing",89.99,"March","TRUE",""],
    ["03/26/2026","Target - Misc","Expense","Wants","Shopping",34.99,"March","TRUE",""],
    # SAVINGS & DEBT
    ["03/01/2026","Emergency Fund Transfer","Expense","Savings","Emergency Fund",400.00,"March","TRUE","Auto-transfer to HYSA"],
    ["03/01/2026","Roth IRA Contribution","Expense","Savings","Retirement / IRA",500.00,"March","TRUE","Auto-invest"],
    ["03/15/2026","Vacation Fund - Europe","Expense","Savings","Vacation Fund",150.00,"March","TRUE",""],
    ["03/01/2026","Student Loan Payment","Expense","Savings","Debt Payment",265.00,"March","TRUE","Min + $80 extra"],
]
apply_values([
    {"range": "Transactions!A1:I36", "values": txn_rows},
], "Transactions (35 rows)")

# ═══════════════════════════════════════════════════════════════════════════════
# DASHBOARD TAB
# ═══════════════════════════════════════════════════════════════════════════════
print("Applying Dashboard formulas...")

# Helper SORTN in M18 (hidden col area — off-screen to right)
# Returns: Date | Description | Amount | Category | Budget  for top 10 expenses
sortn = ('=IFERROR(SORTN(FILTER({'
         'TEXT(Transactions!A:A,"MM/DD/YYYY"),'
         'Transactions!B:B,'
         'Transactions!F:F,'
         'Transactions!E:E,'
         'Transactions!D:D},'
         'Transactions!G:G=Setup!$C$3,'
         'Transactions!C:C="Expense"),'
         '10,0,3,-1),{"","","","",""})' )

dash_data = [
    # Title
    {"range": "Dashboard!A1", "values": [["Smart 50/30/20 Monthly Budget Planner"]]},
    # Info bar
    {"range": "Dashboard!A2", "values": [['="Active: "&Setup!$C$3&"   |   Income: "&TEXT(SUMIFS(Transactions!$F:$F,Transactions!$G:$G,Setup!$C$3,Transactions!$C:$C,"Income"),"$#,##0")&"   |   Spending: "&TEXT(SUMIFS(Transactions!$F:$F,Transactions!$G:$G,Setup!$C$3,Transactions!$C:$C,"Expense"),"$#,##0")&"   |   Remaining: "&TEXT(SUMIFS(Transactions!$F:$F,Transactions!$G:$G,Setup!$C$3,Transactions!$C:$C,"Income")-SUMIFS(Transactions!$F:$F,Transactions!$G:$G,Setup!$C$3,Transactions!$C:$C,"Expense"),"$#,##0")']]},
    # Section header
    {"range": "Dashboard!A4", "values": [['="  MONTHLY SNAPSHOT  —  "&Setup!$C$3']]},
    # KPI Labels (row 5 = A5, D5, G5, J5)
    {"range": "Dashboard!A5", "values": [["TOTAL INCOME"]]},
    {"range": "Dashboard!D5", "values": [["TOTAL SPENDING"]]},
    {"range": "Dashboard!G5", "values": [["REMAINING"]]},
    {"range": "Dashboard!J5", "values": [["SAVINGS TRANSFERRED"]]},
    # KPI Values (row 6)
    {"range": "Dashboard!A6", "values": [['=SUMIFS(Transactions!$F:$F,Transactions!$G:$G,Setup!$C$3,Transactions!$C:$C,"Income")']]},
    {"range": "Dashboard!D6", "values": [['=SUMIFS(Transactions!$F:$F,Transactions!$G:$G,Setup!$C$3,Transactions!$C:$C,"Expense")']]},
    {"range": "Dashboard!G6", "values": [["=A6-D6"]]},
    {"range": "Dashboard!J6", "values": [['=SUMIFS(Transactions!$F:$F,Transactions!$G:$G,Setup!$C$3,Transactions!$C:$C,"Expense",Transactions!$D:$D,"Savings")']]},
    # KPI Sub-labels (row 7)
    {"range": "Dashboard!A7", "values": [['="Planned: "&TEXT(Setup!$C$8,"$#,##0")']]},
    {"range": "Dashboard!D7", "values": [['="Budget: "&TEXT(Setup!$C$17+Setup!$C$18,"$#,##0")']]},
    {"range": "Dashboard!G7", "values": [['=IF(G6>=0,"Surplus — great job!","Deficit — review spending")']]},
    {"range": "Dashboard!J7", "values": [['="Target: "&TEXT(Setup!$C$19,"$#,##0")']]},
    # Budget vs Actual header
    {"range": "Dashboard!A9", "values": [['="  BUDGET VS ACTUAL  —  "&Setup!$C$3']]},
    # Table column headers
    {"range": "Dashboard!A10:L10", "values": [["CATEGORY","","BUDGET","","ACTUAL","","DIFFERENCE","","% USED","OVER?","STATUS",""]]},
    # Needs row
    {"range": "Dashboard!A11:L11", "values": [["Needs  (Essentials)","","=Setup!$C$17","",
        '=SUMIFS(Transactions!$F:$F,Transactions!$G:$G,Setup!$C$3,Transactions!$C:$C,"Expense",Transactions!$D:$D,"Needs")',
        "","=C11-E11","","=IFERROR(E11/C11,0)","",
        '=IF(I11>1,"Over Budget",IF(I11>=0.8,"On Track","Under Budget"))',""]]},
    # Wants row
    {"range": "Dashboard!A12:L12", "values": [["Wants  (Lifestyle)","","=Setup!$C$18","",
        '=SUMIFS(Transactions!$F:$F,Transactions!$G:$G,Setup!$C$3,Transactions!$C:$C,"Expense",Transactions!$D:$D,"Wants")',
        "","=C12-E12","","=IFERROR(E12/C12,0)","",
        '=IF(I12>1,"Over Budget",IF(I12>=0.8,"On Track","Under Budget"))',""]]},
    # Savings row
    {"range": "Dashboard!A13:L13", "values": [["Savings & Debt","","=Setup!$C$19","",
        '=SUMIFS(Transactions!$F:$F,Transactions!$G:$G,Setup!$C$3,Transactions!$C:$C,"Expense",Transactions!$D:$D,"Savings")',
        "","=C13-E13","","=IFERROR(E13/C13,0)","",
        '=IF(I13>=1,"On Track","Needs Attention")',""]]},
    # Total row
    {"range": "Dashboard!A14:L14", "values": [["TOTAL","","=SUM(C11:C13)","","=SUM(E11:E13)",
        "","=C14-E14","","=IFERROR(E14/C14,0)","",
        '=IF(I14>1,"Over Budget",IF(I14>=0.9,"On Track","Under Budget"))',""]]},
    # Top Transactions header
    {"range": "Dashboard!A16", "values": [["  TOP 10 EXPENSES  —  Largest amounts this month"]]},
    # Transaction table headers
    {"range": "Dashboard!A17:L17", "values": [["DATE","","DESCRIPTION","","AMOUNT","","CATEGORY","","","","BUDGET",""]]},
    # SORTN helper in hidden cols M18 (spills 10 rows × 5 cols into M18:Q27)
    {"range": "Dashboard!M18", "values": [[sortn]]},
    # Spending breakdown header
    {"range": "Dashboard!A29", "values": [["  SPENDING BREAKDOWN BY BUCKET"]]},
    # Breakdown headers
    {"range": "Dashboard!A30:L30", "values": [["BUCKET","","BUDGET","","ACTUAL","","REMAINING","","% USED","","INSIGHT",""]]},
    # Needs breakdown
    {"range": "Dashboard!A31:L31", "values": [["Needs  (50% target)","","=Setup!$C$17","",
        '=SUMIFS(Transactions!$F:$F,Transactions!$G:$G,Setup!$C$3,Transactions!$C:$C,"Expense",Transactions!$D:$D,"Needs")',
        "","=C31-E31","","=IFERROR(E31/C31,0)","",
        '=IF(I31>1,"Over budget — find one bill to cut",IF(I31<0.75,"Under budget — great!","On track"))',""]]},
    # Wants breakdown
    {"range": "Dashboard!A32:L32", "values": [["Wants  (30% target)","","=Setup!$C$18","",
        '=SUMIFS(Transactions!$F:$F,Transactions!$G:$G,Setup!$C$3,Transactions!$C:$C,"Expense",Transactions!$D:$D,"Wants")',
        "","=C32-E32","","=IFERROR(E32/C32,0)","",
        '=IF(I32>1,"Over budget — reduce dining & shopping","Excellent discipline")',""]]},
    # Savings breakdown
    {"range": "Dashboard!A33:L33", "values": [["Savings & Debt  (20% target)","","=Setup!$C$19","",
        '=SUMIFS(Transactions!$F:$F,Transactions!$G:$G,Setup!$C$3,Transactions!$C:$C,"Expense",Transactions!$D:$D,"Savings")',
        "","=C33-E33","","=IFERROR(E33/C33,0)","",
        '=IF(I33>=1,"On track — strong savings rate!","Increase monthly savings transfer")',""]]},
]

# Top 10 transaction rows — reference SORTN helper in M:Q
for i in range(10):
    r = 18 + i
    m = 18 + i  # helper row
    dash_data += [
        {"range": f"Dashboard!A{r}", "values": [[f'=IFERROR(M{m},"")']]},
        {"range": f"Dashboard!C{r}", "values": [[f'=IFERROR(N{m},"")']]},
        {"range": f"Dashboard!E{r}", "values": [[f'=IFERROR(O{m},"")']]},
        {"range": f"Dashboard!G{r}", "values": [[f'=IFERROR(P{m},"")']]},
        {"range": f"Dashboard!K{r}", "values": [[f'=IFERROR(Q{m},"")']]},
    ]

apply_values(dash_data, "Dashboard formulas")

# ═══════════════════════════════════════════════════════════════════════════════
# DEBT TRACKER TAB
# ═══════════════════════════════════════════════════════════════════════════════
print("Applying Debt Tracker data...")

debts = [
    ("Chase Sapphire Credit Card","Credit Card",4500,24.99,90,200),
    ("Student Loan (Federal Direct)","Student Loan",18500,5.05,185,80),
    ("Car Loan - Toyota","Auto Loan",12400,6.75,250,50),
    ("Medical Bill - Hospital","Medical",1200,0,100,100),
    ("Personal Loan - Credit Union","Personal Loan",3000,12.50,85,65),
    ("Store Credit Card (TJ Maxx)","Credit Card",680,26.99,25,75),
    ("Home Equity Line of Credit","HELOC",8500,8.25,170,30),
    ("Friend / Family Loan","Personal Loan",500,0,100,0),
]

debt_data = [
    {"range": "Debt Tracker!A1", "values": [["Debt Tracker  —  Snowball / Avalanche Payoff Planner"]]},
    {"range": "Debt Tracker!A2", "values": [["List all debts below. Snowball method: pay off smallest balance first for quick wins. Avalanche: highest APR first to minimize interest paid."]]},
    {"range": "Debt Tracker!A3", "values": [["Tip: Sort by Balance ascending (Snowball) or APR descending (Avalanche). Update balances each month after payments post."]]},
    {"range": "Debt Tracker!A4:J4", "values": [["Creditor / Account","Type","Balance","APR %","Min Payment","Extra Payment","Monthly Total","Months Left","Interest Saved","Status"]]},
]
for i, (name, dtype, bal, apr, minp, extra) in enumerate(debts):
    r = 5 + i
    months_formula = f'=IFERROR(IF(D{r}=0,CEILING(C{r}/G{r},1),CEILING(-LN(1-D{r}/100/12*C{r}/G{r})/LN(1+D{r}/100/12),1)),0)'
    interest_formula = f'=IFERROR(IF(D{r}=0,0,ROUND(G{r}*H{r}-C{r},2)),0)'
    debt_data.append({"range": f"Debt Tracker!A{r}:J{r}", "values": [[
        name, dtype, bal, apr, minp, extra,
        f"=E{r}+F{r}", months_formula, interest_formula, "In Progress"
    ]]})

debt_data.append({"range": "Debt Tracker!A13:J13", "values": [[
    "TOTALS","","=SUM(C5:C12)","","=SUM(E5:E12)","=SUM(F5:F12)",
    "=SUM(G5:G12)","=ROUND(AVERAGE(H5:H12),0)","=SUM(I5:I12)",""
]]})
debt_data.append({"range": "Debt Tracker!A15:G15", "values": [[
    "Estimated Debt-Free Date","","","","",
    '=TEXT(EDATE(TODAY(),MAX(H5:H12)),"MMMM YYYY")',
    '=TEXT(EDATE(TODAY(),MAX(H5:H12)),"MMMM YYYY")'
]]})

apply_values(debt_data, "Debt Tracker")

# ═══════════════════════════════════════════════════════════════════════════════
# SAVINGS GOALS TAB
# ═══════════════════════════════════════════════════════════════════════════════
print("Applying Savings Goals data...")

goals = [
    ("Emergency Fund (6 Months)",       19500, 8200, 200, "6-month expense buffer in HYSA"),
    ("Europe Vacation — Summer 2027",    5000,  1350, 150, "Flight + hotels + experiences"),
    ("New Car Down Payment (20%)",       8000,  2100, 100, "Replace aging 2012 vehicle"),
    ("Home Down Payment (20%)",         40000, 12800, 400, "5-year goal — high-yield savings"),
    ("MacBook Pro — Work Upgrade",       2500,   900,  80, "M4 Pro model"),
    ("Wedding / Engagement Fund",       15000,  3500, 200, "Ring + venue deposit"),
    ("Brokerage Investment Account",    10000,  6200, 150, "Index fund, auto-invest monthly"),
]

sav_data = [
    {"range": "Savings Goals!A1", "values": [["Savings Goals  —  Your Financial Future, One Goal at a Time"]]},
    {"range": "Savings Goals!A3:H3", "values": [["Goal Name","Target","Saved","Monthly","Months Left","Target Date","% Complete","Notes"]]},
]
for i, (name, target, saved, monthly, notes) in enumerate(goals):
    r = 4 + i
    sav_data.append({"range": f"Savings Goals!A{r}:H{r}", "values": [[
        name, target, saved, monthly,
        f"=IFERROR(CEILING((B{r}-C{r})/D{r},1),0)",
        f'=IFERROR(TEXT(EDATE(TODAY(),CEILING((B{r}-C{r})/D{r},1)),"MMMM YYYY"),"Done")',
        f"=IFERROR(MIN(C{r}/B{r},1),0)",
        notes
    ]]})

sav_data.append({"range": "Savings Goals!A11:H11", "values": [[
    "TOTALS","=SUM(B4:B10)","=SUM(C4:C10)","=SUM(D4:D10)",
    "","","=IFERROR(C11/B11,0)",""
]]})

apply_values(sav_data, "Savings Goals")

# ═══════════════════════════════════════════════════════════════════════════════
# ANNUAL OVERVIEW TAB
# ═══════════════════════════════════════════════════════════════════════════════
print("Applying Annual Overview formulas...")

MONTH_NAMES = ["January","February","March","April","May","June",
               "July","August","September","October","November","December"]
MONTH_ABBR  = ["JAN","FEB","MAR","APR","MAY","JUN","JUL","AUG","SEP","OCT","NOV","DEC"]

# Cols B-M = months 1-12 (col indices 1-12)
# Row mapping (1-based):  3=header, 4=Income, 5=Needs, 6=Wants, 7=Savings, 8=TotalSpend, 9=Net, 10=SavingsRate
R_INC  = 4   # Income row
R_NDS  = 5   # Needs spent
R_WNT  = 6   # Wants spent
R_SAV  = 7   # Savings out
R_TOT  = 8   # Total spend
R_NET  = 9   # Net cash
R_RATE = 10  # Savings rate
R_SPKL = 12  # Sparkline

def month_col(i):   # 0-indexed month → column letter (B=Jan, C=Feb, ...)
    return chr(ord('B') + i)

def sumifs_income(mname):
    return f'=SUMIFS(Transactions!$F:$F,Transactions!$G:$G,"{mname}",Transactions!$C:$C,"Income")'

def sumifs_bucket(mname, bucket):
    return f'=SUMIFS(Transactions!$F:$F,Transactions!$G:$G,"{mname}",Transactions!$C:$C,"Expense",Transactions!$D:$D,"{bucket}")'

annual_data = [
    {"range": "Annual Overview!A1", "values": [["Annual Overview  —  12-Month Financial Summary"]]},
    {"range": "Annual Overview!A3:O3", "values": [["METRIC"] + MONTH_ABBR + ["TOTAL","AVERAGE"]]},
]

# Build each row
row_defs = [
    (R_INC,  "INCOME",       lambda m: sumifs_income(m)),
    (R_NDS,  "Needs Spent",  lambda m: sumifs_bucket(m, "Needs")),
    (R_WNT,  "Wants Spent",  lambda m: sumifs_bucket(m, "Wants")),
    (R_SAV,  "Savings Out",  lambda m: sumifs_bucket(m, "Savings")),
]

for row, label, formula_fn in row_defs:
    cells = [label]
    for i, mname in enumerate(MONTH_NAMES):
        cells.append(formula_fn(mname))
    cells.append(f"=SUM(B{row}:M{row})")
    cells.append(f"=AVERAGE(B{row}:M{row})")
    annual_data.append({"range": f"Annual Overview!A{row}:O{row}", "values": [cells]})

# Total Spend = Needs + Wants + Savings
tot_cells = ["Total Spend"]
for i in range(12):
    c = month_col(i)
    tot_cells.append(f"={c}{R_NDS}+{c}{R_WNT}+{c}{R_SAV}")
tot_cells += [f"=SUM(B{R_TOT}:M{R_TOT})", f"=AVERAGE(B{R_TOT}:M{R_TOT})"]
annual_data.append({"range": f"Annual Overview!A{R_TOT}:O{R_TOT}", "values": [tot_cells]})

# Net Cash = Income - Total Spend
net_cells = ["Net Cash"]
for i in range(12):
    c = month_col(i)
    net_cells.append(f"={c}{R_INC}-{c}{R_TOT}")
net_cells += [f"=SUM(B{R_NET}:M{R_NET})", f"=AVERAGE(B{R_NET}:M{R_NET})"]
annual_data.append({"range": f"Annual Overview!A{R_NET}:O{R_NET}", "values": [net_cells]})

# Savings Rate = Savings / Income
rate_cells = ["Savings Rate"]
for i in range(12):
    c = month_col(i)
    rate_cells.append(f"=IFERROR({c}{R_SAV}/{c}{R_INC},0)")
rate_cells += [f"=IFERROR(N{R_SAV}/N{R_INC},0)", f"=AVERAGE(B{R_RATE}:M{R_RATE})"]
annual_data.append({"range": f"Annual Overview!A{R_RATE}:O{R_RATE}", "values": [rate_cells]})

# Sparkline row
annual_data.append({"range": f"Annual Overview!A{R_SPKL}", "values": [["Income Trend"]]})
annual_data.append({"range": f"Annual Overview!B{R_SPKL}", "values": [[
    '=SPARKLINE(B4:M4,{"charttype","column";"color1","#00B4A6";"nan","ignore"})'
]]})

apply_values(annual_data, "Annual Overview formulas")

print("\nAll values applied successfully!")
