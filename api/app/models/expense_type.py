from typing import TYPE_CHECKING

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.expense import Expense

if TYPE_CHECKING:
    from app.models.expense import Expense


class ExpenseType(Base):
    __tablename__ = "expense_types"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(
        String(100),
        unique=True,
        nullable=False,
    )

    expenses: Mapped[list["Expense"]] = relationship(
        back_populates="expense_type",
    )
