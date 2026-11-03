from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.repositories.department import DepartmentRepository
from app.repositories.expense import ExpenseRepository
from app.repositories.expense_type import ExpenseTypeRepository
from app.services.department import DepartmentService
from app.services.expense import ExpenseService
from app.services.expenses_file import ExpensesFileService

SessionDep = Annotated[AsyncSession, Depends(get_db)]


def get_expenses_file_service(session: SessionDep) -> ExpensesFileService:
    expense_repository = ExpenseRepository(session)
    department_repository = DepartmentRepository(session)
    expense_type_repository = ExpenseTypeRepository(session)
    return ExpensesFileService(
        expense_repository,
        department_repository,
        expense_type_repository,
    )


ExpensesFileServiceDep = Annotated[
    ExpensesFileService,
    Depends(get_expenses_file_service),
]


def get_expense_service(session: SessionDep) -> ExpenseService:
    expense_repository = ExpenseRepository(session)
    department_repository = DepartmentRepository(session)
    return ExpenseService(expense_repository, department_repository)


ExpenseServiceDep = Annotated[
    ExpenseService,
    Depends(get_expense_service),
]


def get_department_service(session: SessionDep) -> DepartmentService:
    repository = DepartmentRepository(session)
    return DepartmentService(repository)


DepartmentServiceDep = Annotated[
    DepartmentService,
    Depends(get_department_service),
]
