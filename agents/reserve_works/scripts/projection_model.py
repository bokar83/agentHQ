"""
projection_model.py — Reserve Works income projection tool.

Produces realistic range estimates for wheel strategy income over time.
Uses documented historical return distributions, not marketing ceiling cases.

Usage:
    python projection_model.py --capital 50000 --monthly_contrib 1000 --years 10

Arguments:
    --capital           Starting capital in USD.
    --monthly_contrib   Monthly capital addition from other income (CW/SW profits).
    --years             Projection horizon in years.
    --return_low        Annual return lower bound (default 0.08 = 8%).
    --return_mid        Annual return mid-case (default 0.13 = 13%).
    --return_high       Annual return upper case (default 0.18 = 18%).

Output:
    Year-by-year table of capital and monthly income for each return scenario.
    Plus probability-weighted expected values.

Return scenario sources:
    Low (8%):  CBOE PUT index long-run average (~9.8%, rounded conservatively for
               individual retail execution with friction).
               Source: CBOE PUT Index annual return data, 1986-2023.
    Mid (13%): TastyTrade Research median for disciplined short-put strategy on
               large-cap underlyings, 45 DTE, 30-delta, full capital coverage.
               Source: tastylive.com Research archive, "Short Puts Performance" 2020.
    High (18%): Top quartile individual practitioner returns in favorable VIX regimes.
                Not a reliable sustained expectation; included as ceiling.
                Source: Sinclair "Volatility Trading" 2nd ed., Chapter 6.

Probability weights (rough approximation):
    Low scenario:  35% (below-average VIX regime or one bad year in the period)
    Mid scenario:  45% (normal execution, average VIX environment)
    High scenario: 20% (favorable VIX regime, no significant assignment losses)
"""

import argparse
import sys


PROB_LOW = 0.35
PROB_MID = 0.45
PROB_HIGH = 0.20

DEFAULT_RETURN_LOW = 0.08
DEFAULT_RETURN_MID = 0.13
DEFAULT_RETURN_HIGH = 0.18


def project(
    starting_capital: float,
    monthly_contribution: float,
    years: int,
    annual_return: float,
) -> list[dict]:
    """
    Project capital and monthly income over time with regular contributions.

    Returns a list of dicts, one per year-end, with:
        year: int
        capital: float (end-of-year)
        monthly_income: float (capital * annual_return / 12)
        annual_income: float
    """
    capital = starting_capital
    annual_contribution = monthly_contribution * 12
    results = []

    for year in range(1, years + 1):
        capital = capital * (1 + annual_return) + annual_contribution
        monthly_income = capital * annual_return / 12
        results.append({
            "year": year,
            "capital": capital,
            "monthly_income": monthly_income,
            "annual_income": monthly_income * 12,
        })

    return results


def weighted_income(low: float, mid: float, high: float) -> float:
    return PROB_LOW * low + PROB_MID * mid + PROB_HIGH * high


def run_projection(
    starting_capital: float,
    monthly_contribution: float,
    years: int,
    return_low: float = DEFAULT_RETURN_LOW,
    return_mid: float = DEFAULT_RETURN_MID,
    return_high: float = DEFAULT_RETURN_HIGH,
) -> None:
    results_low = project(starting_capital, monthly_contribution, years, return_low)
    results_mid = project(starting_capital, monthly_contribution, years, return_mid)
    results_high = project(starting_capital, monthly_contribution, years, return_high)

    print(
        f"\nReserve Works Income Projection"
        f"\nStarting capital: ${starting_capital:,.0f}"
        f"\nMonthly contribution: ${monthly_contribution:,.0f}"
        f"\nProjection horizon: {years} years"
        f"\nReturn scenarios: Low={return_low:.0%} / Mid={return_mid:.0%} / High={return_high:.0%}"
        f"\nProbability weights: Low={PROB_LOW:.0%} / Mid={PROB_MID:.0%} / High={PROB_HIGH:.0%}"
    )

    print(
        "\n"
        f"{'Year':>5} | "
        f"{'Capital (Low)':>15} | {'Monthly (Low)':>14} | "
        f"{'Capital (Mid)':>15} | {'Monthly (Mid)':>14} | "
        f"{'Capital (High)':>16} | {'Monthly (High)':>15} | "
        f"{'Expected Monthly':>16}"
    )
    print("-" * 130)

    target_monthly = 5000.0

    for i in range(years):
        lo = results_low[i]
        mi = results_mid[i]
        hi = results_high[i]
        expected_mo = weighted_income(
            lo["monthly_income"], mi["monthly_income"], hi["monthly_income"]
        )
        print(
            f"{lo['year']:>5} | "
            f"${lo['capital']:>14,.0f} | ${lo['monthly_income']:>13,.0f} | "
            f"${mi['capital']:>14,.0f} | ${mi['monthly_income']:>13,.0f} | "
            f"${hi['capital']:>15,.0f} | ${hi['monthly_income']:>14,.0f} | "
            f"${expected_mo:>15,.0f}"
        )

    print()

    # Find when each scenario crosses $5K/month
    def years_to_target(results: list[dict], target: float) -> str:
        for r in results:
            if r["monthly_income"] >= target:
                return f"Year {r['year']}"
        return f">Year {years}"

    print(
        f"\nYears to ${target_monthly:,.0f}/month target:"
        f"\n  Low scenario ({return_low:.0%}):  {years_to_target(results_low, target_monthly)}"
        f"\n  Mid scenario ({return_mid:.0%}):  {years_to_target(results_mid, target_monthly)}"
        f"\n  High scenario ({return_high:.0%}): {years_to_target(results_high, target_monthly)}"
    )

    print(
        f"\nNote: These projections assume:"
        f"\n  - Consistent execution with no catastrophic drawdown."
        f"\n  - Contributions funded from CW/SW income, not from options capital."
        f"\n  - No withdrawal from the options capital during the projection period."
        f"\n  - Returns are net of estimated assignment losses and commissions."
        f"\n\nThe Kiyosaki PDF implied 150% annual returns. "
        f"These projections use {return_mid:.0%} as the mid-case, "
        f"consistent with CBOE benchmark data and TastyTrade Research."
    )


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Reserve Works wheel strategy income projection"
    )
    parser.add_argument("--capital", type=float, required=True, help="Starting capital in USD")
    parser.add_argument(
        "--monthly_contrib", type=float, default=0,
        help="Monthly contribution from other income (USD)"
    )
    parser.add_argument("--years", type=int, default=10, help="Projection horizon in years")
    parser.add_argument(
        "--return_low", type=float, default=DEFAULT_RETURN_LOW, help="Low return scenario (0.08)"
    )
    parser.add_argument(
        "--return_mid", type=float, default=DEFAULT_RETURN_MID, help="Mid return scenario (0.13)"
    )
    parser.add_argument(
        "--return_high", type=float, default=DEFAULT_RETURN_HIGH, help="High return scenario (0.18)"
    )
    args = parser.parse_args()

    run_projection(
        starting_capital=args.capital,
        monthly_contribution=args.monthly_contrib,
        years=args.years,
        return_low=args.return_low,
        return_mid=args.return_mid,
        return_high=args.return_high,
    )


if __name__ == "__main__":
    main()
