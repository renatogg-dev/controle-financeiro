"""Pydantic request/response schemas for the JSON API."""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.models import TransactionType


class UserRegister(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: str
    created_at: datetime


class CategoryRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    color: str
    is_default: bool


class TransactionCreate(BaseModel):
    type: TransactionType
    amount: Decimal = Field(gt=0, decimal_places=2)
    date: date
    category_id: int
    description: str = Field(default="", max_length=200)


class TransactionUpdate(TransactionCreate):
    pass


class TransactionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    type: TransactionType
    amount: Decimal
    date: date
    description: str
    category: CategoryRead


class PaginatedTransactions(BaseModel):
    items: list[TransactionRead]
    total: int
    page: int
    page_size: int


class MonthlyTotals(BaseModel):
    income: Decimal
    expense: Decimal
    balance: Decimal


class CategoryBreakdownItem(BaseModel):
    category: str
    color: str
    amount: Decimal


class MonthlySeriesItem(BaseModel):
    month: str
    income: Decimal
    expense: Decimal


class DashboardSummary(BaseModel):
    month: str
    totals: MonthlyTotals
    category_breakdown: list[CategoryBreakdownItem]
    monthly_series: list[MonthlySeriesItem]


class ReminderCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    amount: Decimal | None = Field(default=None, ge=0, decimal_places=2)
    due_date: date
    notes: str | None = Field(default=None, max_length=200)


class ReminderRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    amount: Decimal | None
    due_date: date
    notes: str | None
    is_paid: bool
    status: str
