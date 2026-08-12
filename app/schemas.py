import datetime as dt
from typing import Optional, List
from pydantic import BaseModel, EmailStr, ConfigDict
from .models import CashflowType


# ---------- Auth ----------
class UserCreate(BaseModel):
    email: EmailStr
    password: str


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    email: EmailStr


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


# ---------- Cashflow ----------
class CashflowCreate(BaseModel):
    type: CashflowType
    amount: float
    date: dt.date
    note: Optional[str] = None


class CashflowOut(CashflowCreate):
    model_config = ConfigDict(from_attributes=True)
    id: int


# ---------- Investment ----------
class InvestmentCreate(BaseModel):
    fund_name: str
    asset_class: str = "Private Equity"
    vintage_year: Optional[int] = None
    commitment_amount: float
    current_nav: float = 0.0
    nav_as_of: Optional[dt.date] = None


class InvestmentUpdate(BaseModel):
    fund_name: Optional[str] = None
    asset_class: Optional[str] = None
    vintage_year: Optional[int] = None
    commitment_amount: Optional[float] = None
    current_nav: Optional[float] = None
    nav_as_of: Optional[dt.date] = None


class InvestmentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    fund_name: str
    asset_class: str
    vintage_year: Optional[int]
    commitment_amount: float
    current_nav: float
    nav_as_of: Optional[dt.date]
    cashflows: List[CashflowOut] = []


class InvestmentMetrics(BaseModel):
    investment_id: int
    fund_name: str
    paid_in: float          # total capital called
    distributions: float    # total distributed back
    nav: float               # current NAV
    dpi: float               # Distributions / Paid-In
    rvpi: float               # Residual Value / Paid-In (NAV / Paid-In)
    tvpi: float               # Total Value / Paid-In ((Distributions + NAV) / Paid-In)
    moic: float               # same as TVPI, PE industry commonly uses this term
    irr: Optional[float]     # annualized IRR (XIRR), None if not computable


class PortfolioSummary(BaseModel):
    total_committed: float
    total_paid_in: float
    total_distributions: float
    total_nav: float
    portfolio_dpi: float
    portfolio_tvpi: float
    portfolio_irr: Optional[float]
    num_investments: int
