from decimal import Decimal

from app.repositories.department import DepartmentRepository
from app.repositories.expense import ExpenseRepository


class InvalidDepartmentError(Exception):
    pass


class ExpenseService:
    def __init__(
        self,
        expense_repository: ExpenseRepository,
        department_repository: DepartmentRepository,
    ) -> None:
        self.expense_repository = expense_repository
        self.department_repository = department_repository

    @staticmethod
    def get_months_list(month: int | None, quarter: int | None) -> list[int]:
        months = list(range(1, 13))
        if month is not None:
            months = [month]
        elif quarter is not None:
            months = list(range((quarter - 1) * 3 + 1, quarter * 3 + 1))

        return months

    async def get_aggregated_expenses(
        self,
        department_id: str,
        year: int | None,
        months: list[int],
    ) -> Decimal:
        department = await self.department_repository.get_by_id(department_id)
        if department is None:
            raise InvalidDepartmentError("Invalid Department")

        return await self.expense_repository.get_aggregated_expenses(
            department_id=department_id, year=year, months=months
        )
