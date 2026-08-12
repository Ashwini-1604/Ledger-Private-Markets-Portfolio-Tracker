"""
Private-equity style performance metrics.

Definitions (the ones you should be able to explain in an interview):

- Paid-in capital: total cash the investor has actually sent to the fund
  (sum of capital calls).
- Distributions: total cash the fund has sent back to the investor.
- NAV (Net Asset Value): the fund's current estimate of what the investor's
  remaining stake is worth (unrealized value).
- DPI (Distributions to Paid-In): distributions / paid_in.
  "How much cash have I actually gotten back, per dollar invested?"
- RVPI (Residual Value to Paid-In): NAV / paid_in.
  "How much unrealized value is still sitting in the fund?"
- TVPI (Total Value to Paid-In) = DPI + RVPI = (distributions + NAV) / paid_in.
  Also commonly called MOIC (Multiple on Invested Capital) in PE/VC contexts.
- IRR (Internal Rate of Return): the annualized discount rate that makes the
  net present value of all cashflows (calls as negative, distributions +
  current NAV as a final positive "cashflow") equal to zero. We use XIRR,
  which handles irregularly-dated cashflows (real capital calls almost never
  land on neat annual intervals).
"""

import datetime as dt
from typing import List, Optional, Tuple


def xnpv(rate: float, cashflows: List[Tuple[dt.date, float]]) -> float:
    """Net present value for irregularly dated cashflows."""
    t0 = cashflows[0][0]
    return sum(
        amount / (1.0 + rate) ** ((date - t0).days / 365.0)
        for date, amount in cashflows
    )


def xirr(cashflows: List[Tuple[dt.date, float]]) -> Optional[float]:
    """
    Solve for the annualized rate where XNPV == 0 using Newton's method,
    falling back to bisection if Newton doesn't converge. Returns None if
    the cashflow series has no sign change (IRR is undefined).
    """
    if len(cashflows) < 2:
        return None

    amounts = [c[1] for c in cashflows]
    if not (any(a > 0 for a in amounts) and any(a < 0 for a in amounts)):
        return None  # no sign change -> IRR undefined

    cashflows = sorted(cashflows, key=lambda c: c[0])

    # --- Try Newton's method first ---
    rate = 0.1
    for _ in range(100):
        npv = xnpv(rate, cashflows)
        # numerical derivative
        h = 1e-6
        d_npv = (xnpv(rate + h, cashflows) - npv) / h
        if d_npv == 0:
            break
        new_rate = rate - npv / d_npv
        if abs(new_rate - rate) < 1e-7:
            return round(new_rate, 6)
        rate = new_rate
        if rate <= -0.999:  # guard against runaway rates
            break

    # --- Fallback: bisection over a wide, sane range ---
    low, high = -0.999, 10.0
    f_low = xnpv(low, cashflows)
    f_high = xnpv(high, cashflows)
    if f_low * f_high > 0:
        return None  # can't bracket a root; give up gracefully

    for _ in range(200):
        mid = (low + high) / 2
        f_mid = xnpv(mid, cashflows)
        if abs(f_mid) < 1e-6:
            return round(mid, 6)
        if f_low * f_mid < 0:
            high, f_high = mid, f_mid
        else:
            low, f_low = mid, f_mid

    return round((low + high) / 2, 6)


def compute_investment_metrics(investment) -> dict:
    """Takes an Investment ORM object (with .cashflows loaded) and returns metrics."""
    paid_in = sum(cf.amount for cf in investment.cashflows if cf.type.value == "capital_call")
    distributions = sum(cf.amount for cf in investment.cashflows if cf.type.value == "distribution")
    nav = investment.current_nav or 0.0

    dpi = round(distributions / paid_in, 4) if paid_in > 0 else 0.0
    rvpi = round(nav / paid_in, 4) if paid_in > 0 else 0.0
    tvpi = round(dpi + rvpi, 4)

    # Build the cashflow series for IRR: calls negative, distributions positive,
    # plus a final "as of today" positive cashflow representing the residual NAV.
    series: List[Tuple[dt.date, float]] = []
    for cf in investment.cashflows:
        signed = -cf.amount if cf.type.value == "capital_call" else cf.amount
        series.append((cf.date, signed))

    if nav > 0:
        as_of = investment.nav_as_of or dt.date.today()
        series.append((as_of, nav))

    irr = xirr(series) if series else None

    return {
        "investment_id": investment.id,
        "fund_name": investment.fund_name,
        "paid_in": round(paid_in, 2),
        "distributions": round(distributions, 2),
        "nav": round(nav, 2),
        "dpi": dpi,
        "rvpi": rvpi,
        "tvpi": tvpi,
        "moic": tvpi,  # MOIC and TVPI are the same figure in this context
        "irr": irr,
    }
