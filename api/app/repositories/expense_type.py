from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.expense_type import ExpenseType


class ExpenseTypeRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_names(self, names: list[str]) -> list[ExpenseType]:
        if not names:
            return []

        statement = select(ExpenseType).where(ExpenseType.name.in_(names))
        result = await self.session.scalars(statement)

        return result.all()

    async def create_many(self, names: list[str]) -> list[ExpenseType]:
        expense_types = [ExpenseType(name=name) for name in names]
        self.session.add_all(expense_types)
        await self.session.flush()

        return expense_types

    async def get_or_create_many(
        self,
        names: list[str],
    ) -> list[ExpenseType]:
        existing_expense_types = await self.get_by_names(names)

        existing_names = {expense_type.name for expense_type in existing_expense_types}
        missing_names = [name for name in names if name not in existing_names]

        created_expense_types = await self.create_many(missing_names)

        return existing_expense_types + created_expense_types
