import csv
import io
import datetime as dt
from typing import List
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session, joinedload

from .. import models, schemas, auth, calculations
from ..database import get_db

router = APIRouter(prefix="/investments", tags=["investments"])


def _get_owned_investment(investment_id: int, db: Session, user: models.User) -> models.Investment:
    inv = (
        db.query(models.Investment)
        .options(joinedload(models.Investment.cashflows))
        .filter(models.Investment.id == investment_id, models.Investment.owner_id == user.id)
        .first()
    )
    if not inv:
        raise HTTPException(status_code=404, detail="Investment not found")
    return inv


@router.post("", response_model=schemas.InvestmentOut, status_code=201)
def create_investment(
    payload: schemas.InvestmentCreate,
    db: Session = Depends(get_db),
    user: models.User = Depends(auth.get_current_user),
):
    inv = models.Investment(owner_id=user.id, **payload.model_dump())
    db.add(inv)
    db.commit()
    db.refresh(inv)
    return inv


@router.get("", response_model=List[schemas.InvestmentOut])
def list_investments(
    db: Session = Depends(get_db),
    user: models.User = Depends(auth.get_current_user),
):
    return (
        db.query(models.Investment)
        .options(joinedload(models.Investment.cashflows))
        .filter(models.Investment.owner_id == user.id)
        .order_by(models.Investment.created_at.desc())
        .all()
    )


@router.get("/{investment_id}", response_model=schemas.InvestmentOut)
def get_investment(
    investment_id: int,
    db: Session = Depends(get_db),
    user: models.User = Depends(auth.get_current_user),
):
    return _get_owned_investment(investment_id, db, user)


@router.patch("/{investment_id}", response_model=schemas.InvestmentOut)
def update_investment(
    investment_id: int,
    payload: schemas.InvestmentUpdate,
    db: Session = Depends(get_db),
    user: models.User = Depends(auth.get_current_user),
):
    inv = _get_owned_investment(investment_id, db, user)
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(inv, field, value)
    db.commit()
    db.refresh(inv)
    return inv


@router.delete("/{investment_id}", status_code=204)
def delete_investment(
    investment_id: int,
    db: Session = Depends(get_db),
    user: models.User = Depends(auth.get_current_user),
):
    inv = _get_owned_investment(investment_id, db, user)
    db.delete(inv)
    db.commit()
    return None


# ---------- Cashflows ----------
@router.post("/{investment_id}/cashflows", response_model=schemas.CashflowOut, status_code=201)
def add_cashflow(
    investment_id: int,
    payload: schemas.CashflowCreate,
    db: Session = Depends(get_db),
    user: models.User = Depends(auth.get_current_user),
):
    inv = _get_owned_investment(investment_id, db, user)
    cf = models.Cashflow(investment_id=inv.id, **payload.model_dump())
    db.add(cf)
    db.commit()
    db.refresh(cf)
    return cf


@router.delete("/{investment_id}/cashflows/{cashflow_id}", status_code=204)
def delete_cashflow(
    investment_id: int,
    cashflow_id: int,
    db: Session = Depends(get_db),
    user: models.User = Depends(auth.get_current_user),
):
    inv = _get_owned_investment(investment_id, db, user)
    cf = next((c for c in inv.cashflows if c.id == cashflow_id), None)
    if not cf:
        raise HTTPException(status_code=404, detail="Cashflow not found")
    db.delete(cf)
    db.commit()
    return None


# ---------- CSV import ----------
# Expected CSV columns: type,amount,date,note
# type must be "capital_call" or "distribution"; date as YYYY-MM-DD
@router.post("/{investment_id}/cashflows/import-csv", response_model=List[schemas.CashflowOut])
async def import_cashflows_csv(
    investment_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    user: models.User = Depends(auth.get_current_user),
):
    inv = _get_owned_investment(investment_id, db, user)
    raw = (await file.read()).decode("utf-8-sig")
    reader = csv.DictReader(io.StringIO(raw))

    required_cols = {"type", "amount", "date"}
    if not required_cols.issubset(set(reader.fieldnames or [])):
        raise HTTPException(
            status_code=400,
            detail=f"CSV must contain columns: {', '.join(required_cols)}",
        )

    created = []
    for i, row in enumerate(reader, start=2):  # row 1 is header
        try:
            cf_type = row["type"].strip().lower()
            if cf_type not in ("capital_call", "distribution"):
                raise ValueError(f"invalid type '{row['type']}'")
            amount = float(row["amount"])
            date = dt.datetime.strptime(row["date"].strip(), "%Y-%m-%d").date()
        except (ValueError, KeyError) as e:
            raise HTTPException(status_code=400, detail=f"Row {i}: {e}")

        cf = models.Cashflow(
            investment_id=inv.id,
            type=cf_type,
            amount=amount,
            date=date,
            note=row.get("note") or None,
        )
        db.add(cf)
        created.append(cf)

    db.commit()
    for cf in created:
        db.refresh(cf)
    return created


# ---------- Metrics ----------
@router.get("/{investment_id}/metrics", response_model=schemas.InvestmentMetrics)
def get_investment_metrics(
    investment_id: int,
    db: Session = Depends(get_db),
    user: models.User = Depends(auth.get_current_user),
):
    inv = _get_owned_investment(investment_id, db, user)
    return calculations.compute_investment_metrics(inv)


@router.get("/{investment_id}/cashflow-timeline")
def get_cashflow_timeline(
    investment_id: int,
    db: Session = Depends(get_db),
    user: models.User = Depends(auth.get_current_user),
):
    """Returns cumulative paid-in vs distributions over time, for charting."""
    inv = _get_owned_investment(investment_id, db, user)
    events = sorted(inv.cashflows, key=lambda c: c.date)

    timeline = []
    cum_paid_in = 0.0
    cum_dist = 0.0
    for cf in events:
        if cf.type.value == "capital_call":
            cum_paid_in += cf.amount
        else:
            cum_dist += cf.amount
        timeline.append({
            "date": cf.date.isoformat(),
            "cumulative_paid_in": round(cum_paid_in, 2),
            "cumulative_distributions": round(cum_dist, 2),
            "net_cashflow": round(cum_dist - cum_paid_in, 2),
        })
    return timeline
