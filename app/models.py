import enum
import datetime as dt
from sqlalchemy import (
    Column, Integer, String, Float, Date, ForeignKey, Enum, DateTime
)
from sqlalchemy.orm import relationship
from .database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=dt.datetime.utcnow)

    investments = relationship("Investment", back_populates="owner", cascade="all, delete-orphan")


class Investment(Base):
    __tablename__ = "investments"

    id = Column(Integer, primary_key=True, index=True)
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    fund_name = Column(String(255), nullable=False)
    asset_class = Column(String(100), default="Private Equity")  # PE, Real Estate, VC, etc.
    vintage_year = Column(Integer, nullable=True)
    commitment_amount = Column(Float, nullable=False)
    current_nav = Column(Float, default=0.0)  # latest reported Net Asset Value
    nav_as_of = Column(Date, nullable=True)
    created_at = Column(DateTime, default=dt.datetime.utcnow)

    owner = relationship("User", back_populates="investments")
    cashflows = relationship("Cashflow", back_populates="investment", cascade="all, delete-orphan")


class CashflowType(str, enum.Enum):
    CAPITAL_CALL = "capital_call"   # money OUT of investor's pocket (paid-in)
    DISTRIBUTION = "distribution"   # money BACK to investor


class Cashflow(Base):
    __tablename__ = "cashflows"

    id = Column(Integer, primary_key=True, index=True)
    investment_id = Column(Integer, ForeignKey("investments.id"), nullable=False)
    type = Column(Enum(CashflowType), nullable=False)
    amount = Column(Float, nullable=False)  # always stored as a positive number
    date = Column(Date, nullable=False)
    note = Column(String(500), nullable=True)

    investment = relationship("Investment", back_populates="cashflows")
