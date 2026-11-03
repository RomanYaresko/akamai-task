from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.expense import Expense


class ExpenseRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create_many(self, expenses: list[Expense]) -> int:
        self.session.add_all(expenses)
        await self.session.flush()

        return len(expenses)

    async def get_aggregated_expenses(
        self,
        department_id: int,
        year: int,
        months: list[int],
    ) -> Decimal:
        statement = select(func.coalesce(func.sum(Expense.amount), 0)).where(
            Expense.department_id == department_id,
            Expense.year == year,
            Expense.month.in_(months),
        )

        result = await self.session.scalar(statement)

        return Decimal(str(result or 0))
