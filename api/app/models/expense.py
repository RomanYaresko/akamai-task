from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, ForeignKey, Index, Numeric, SmallInteger
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.department import Department
    from app.models.expense_type import ExpenseType


class Expense(Base):
    __tablename__ = "expenses"

    id: Mapped[int] = mapped_column(primary_key=True)

    department_id: Mapped[int] = mapped_column(
        ForeignKey("departments.id"),
        nullable=False,
    )

    expense_type_id: Mapped[int] = mapped_column(
        ForeignKey("expense_types.id"),
        nullable=False,
    )

    year: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    month: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=False,
    )

    department: Mapped["Department"] = relationship(
        back_populates="expenses",
    )

    expense_type: Mapped["ExpenseType"] = relationship(
        back_populates="expenses",
    )

    __table_args__ = (
        CheckConstraint("year BETWEEN 1 AND 9999", name="ck_expenses_year"),
        CheckConstraint("month BETWEEN 1 AND 12", name="ck_expenses_month"),
        Index(
            "ix_expenses_department_year_month",
            "department_id",
            "year",
            "month",
        ),
        Index(
            "ix_expenses_expense_type_id",
            "expense_type_id",
        ),
    )
