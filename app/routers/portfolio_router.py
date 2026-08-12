from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session, joinedload

from .. import models, schemas, auth, calculations
from ..database import get_db

router = APIRouter(prefix="/portfolio", tags=["portfolio"])


@router.get("/summary", response_model=schemas.PortfolioSummary)
def portfolio_summary(
    db: Session = Depends(get_db),
    user: models.User = Depends(auth.get_current_user),
):
    investments = (
        db.query(models.Investment)
        .options(joinedload(models.Investment.cashflows))
        .filter(models.Investment.owner_id == user.id)
        .all()
    )

    total_committed = sum(inv.commitment_amount for inv in investments)
    total_paid_in = 0.0
    total_distributions = 0.0
    total_nav = 0.0

    # Aggregate cashflow series across the whole portfolio for a blended IRR
    combined_series = []

    for inv in investments:
        m = calculations.compute_investment_metrics(inv)
        total_paid_in += m["paid_in"]
        total_distributions += m["distributions"]
        total_nav += m["nav"]

        for cf in inv.cashflows:
            signed = -cf.amount if cf.type.value == "capital_call" else cf.amount
            combined_series.append((cf.date, signed))

    if total_nav > 0:
        import datetime as dt
        combined_series.append((dt.date.today(), total_nav))

    portfolio_irr = calculations.xirr(combined_series) if combined_series else None
    portfolio_dpi = round(total_distributions / total_paid_in, 4) if total_paid_in > 0 else 0.0
    portfolio_tvpi = round((total_distributions + total_nav) / total_paid_in, 4) if total_paid_in > 0 else 0.0

    return schemas.PortfolioSummary(
        total_committed=round(total_committed, 2),
        total_paid_in=round(total_paid_in, 2),
        total_distributions=round(total_distributions, 2),
        total_nav=round(total_nav, 2),
        portfolio_dpi=portfolio_dpi,
        portfolio_tvpi=portfolio_tvpi,
        portfolio_irr=portfolio_irr,
        num_investments=len(investments),
    )
