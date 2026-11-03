import re
from decimal import Decimal
from typing import BinaryIO

import pandas as pd

from app.constants.expenses_file import MONTHS, QUARTERS, ExpensesColumn
from app.models.department import Department
from app.models.expense import Expense
from app.models.expense_type import ExpenseType
from app.repositories.department import DepartmentRepository
from app.repositories.expense import ExpenseRepository
from app.repositories.expense_type import ExpenseTypeRepository


class ExpensesFileDepartmentError(Exception):
    pass


class ExpensesFileYearError(Exception):
    pass


class ExpensesFileDataframeError(Exception):
    pass


class ExpensesFileMappingError(Exception):
    pass


class ExpensesFileService:
    def __init__(
        self,
        expense_repository: ExpenseRepository,
        department_repository: DepartmentRepository,
        expense_type_repository: ExpenseTypeRepository,
    ) -> None:
        self.expense_repository = expense_repository
        self.department_repository = department_repository
        self.expense_type_repository = expense_type_repository

    @staticmethod
    def get_months_list(month: str | None, quarter: int | None) -> list[str]:
        if quarter is not None:
            return list(QUARTERS[quarter])
        elif month is not None:
            return [month]
        else:
            return list(MONTHS)

    @staticmethod
    def _convert_money_to_decimal(value: str) -> Decimal:
        return Decimal(re.sub(r"[$,()]", "", value))

    @classmethod
    def _get_expenses_dataframe(
        cls, file: BinaryIO, columns: list[str]
    ) -> pd.DataFrame:
        try:
            dataframe = pd.read_csv(
                file,
                sep=";",
                usecols=columns,
                converters=dict.fromkeys(MONTHS, cls._convert_money_to_decimal),
            )
        except (
            pd.errors.EmptyDataError,
            pd.errors.ParserError,
            UnicodeDecodeError,
        ) as exc:
            raise ExpensesFileDataframeError("Unable to read CSV file") from exc

        return dataframe

    @staticmethod
    def _get_filtered_aggregation_expenses_dataframe(
        expenses_dataframe: pd.DataFrame,
        department: str,
        year: int | None = None,
    ) -> pd.DataFrame:
        expenses_dataframe = expenses_dataframe[
            expenses_dataframe[ExpensesColumn.DEPARTMENT.value] == department
        ]

        if expenses_dataframe.empty:
            raise ExpensesFileDepartmentError("Department not found")

        if year is not None:
            expenses_dataframe = expenses_dataframe[
                expenses_dataframe[ExpensesColumn.YEAR.value] == year
            ]

            if expenses_dataframe.empty:
                raise ExpensesFileYearError("Year not found")

        return expenses_dataframe

    @classmethod
    def _get_normalized_mapping_expenses_dataframe(
        cls, dataframe: pd.DataFrame
    ) -> pd.DataFrame:
        department_column = ExpensesColumn.DEPARTMENT.value
        expense_type_column = ExpensesColumn.EXPENSE_TYPE.value
        year_column = ExpensesColumn.YEAR.value

        dataframe = dataframe.copy()

        # Validate years
        years = pd.to_numeric(dataframe[year_column], errors="coerce")

        invalid_years = years.isna() | years.mod(1).ne(0) | years.lt(1) | years.gt(9999)

        if invalid_years.any():
            raise ExpensesFileMappingError(
                "Year values must be whole numbers from 1 to 9999"
            )

        dataframe[year_column] = years.astype(int)

        # Melt rows to have one row per month
        dataframe = dataframe.reset_index(drop=True)
        dataframe["_row_number"] = dataframe.index + 2

        dataframe = dataframe.melt(
            id_vars=[
                department_column,
                expense_type_column,
                year_column,
                "_row_number",
            ],
            value_vars=list(MONTHS),
            var_name="month",
            value_name="amount",
        )

        # Convert months to numbers
        month_numbers = {month: number for number, month in enumerate(MONTHS, start=1)}

        dataframe["month"] = dataframe["month"].map(month_numbers)

        return dataframe

    @staticmethod
    def _build_mapped_expenses(
        dataframe: pd.DataFrame,
        departments: list[Department],
        expense_types: list[ExpenseType],
    ) -> list[Expense]:
        department_by_name = {department.name: department for department in departments}
        expense_type_by_name = {
            expense_type.name: expense_type for expense_type in expense_types
        }

        department_column = ExpensesColumn.DEPARTMENT.value
        expense_type_column = ExpensesColumn.EXPENSE_TYPE.value
        year_column = ExpensesColumn.YEAR.value

        return [
            Expense(
                department_id=department_by_name[row[department_column]].id,
                expense_type_id=expense_type_by_name[row[expense_type_column]].id,
                year=row[year_column],
                month=row["month"],
                amount=row["amount"],
            )
            for row in dataframe.to_dict(orient="records")
        ]

    def get_aggregated_expenses(
        self,
        file: BinaryIO,
        department: str,
        months: list[str],
        year: int | None = None,
    ) -> Decimal:
        expenses_dataframe = self._get_expenses_dataframe(
            file,
            columns=[
                ExpensesColumn.DEPARTMENT.value,
                ExpensesColumn.YEAR.value,
                *months,
            ],
        )
        filtered_expenses_dataframe = self._get_filtered_aggregation_expenses_dataframe(
            expenses_dataframe, department, year
        )

        aggregated_expenses = filtered_expenses_dataframe.aggregate(
            dict.fromkeys(months, "sum")
        )

        return aggregated_expenses.sum()

    async def import_expenses(self, file: BinaryIO) -> None:
        expenses_dataframe = self._get_expenses_dataframe(
            file, columns=[column.value for column in ExpensesColumn]
        )
        normalized_expenses_dataframe = self._get_normalized_mapping_expenses_dataframe(
            expenses_dataframe
        )

        departments = await self.department_repository.get_or_create_many(
            normalized_expenses_dataframe[ExpensesColumn.DEPARTMENT.value]
            .unique()
            .tolist()
        )

        expense_types = await self.expense_type_repository.get_or_create_many(
            normalized_expenses_dataframe[ExpensesColumn.EXPENSE_TYPE.value]
            .unique()
            .tolist()
        )

        expenses = self._build_mapped_expenses(
            normalized_expenses_dataframe,
            departments,
            expense_types,
        )

        await self.expense_repository.create_many(expenses)
