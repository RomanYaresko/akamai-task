import re
import sys
from argparse import ArgumentParser, Namespace
from enum import Enum
from pathlib import Path

import pandas as pd


class ExpensesColumn(Enum):
    DEPARTMENT = "Department"
    YEAR = "Year"
    JANUARY = "Jan"
    FEBRUARY = "Feb"
    MARCH = "Mar"
    APRIL = "Apr"
    MAY = "May"
    JUNE = "Jun"
    JULY = "Jul"
    AUGUST = "Aug"
    SEPTEMBER = "Sep"
    OCTOBER = "Oct"
    NOVEMBER = "Nov"
    DECEMBER = "Dec"


EXPENSES_CSV_PATH = Path(__file__).with_name("Expenses.csv")

MONTHS: tuple[str, ...] = (
    ExpensesColumn.JANUARY.value,
    ExpensesColumn.FEBRUARY.value,
    ExpensesColumn.MARCH.value,
    ExpensesColumn.APRIL.value,
    ExpensesColumn.MAY.value,
    ExpensesColumn.JUNE.value,
    ExpensesColumn.JULY.value,
    ExpensesColumn.AUGUST.value,
    ExpensesColumn.SEPTEMBER.value,
    ExpensesColumn.OCTOBER.value,
    ExpensesColumn.NOVEMBER.value,
    ExpensesColumn.DECEMBER.value,
)

QUARTERS: dict[int, tuple[str, ...]] = {
    1: (
        ExpensesColumn.JANUARY.value,
        ExpensesColumn.FEBRUARY.value,
        ExpensesColumn.MARCH.value,
    ),
    2: (
        ExpensesColumn.APRIL.value,
        ExpensesColumn.MAY.value,
        ExpensesColumn.JUNE.value,
    ),
    3: (
        ExpensesColumn.JULY.value,
        ExpensesColumn.AUGUST.value,
        ExpensesColumn.SEPTEMBER.value,
    ),
    4: (
        ExpensesColumn.OCTOBER.value,
        ExpensesColumn.NOVEMBER.value,
        ExpensesColumn.DECEMBER.value,
    ),
}


def convert_money_to_float(value: str) -> float:
    return float(re.sub(r"[$,()]", "", value))


def convert_float_to_money(value: float) -> str:
    return f"${value:,.2f}"


def get_expenses_dataframe(months: list[str]) -> pd.DataFrame:
    return pd.read_csv(
        EXPENSES_CSV_PATH,
        sep=";",
        usecols=[
            ExpensesColumn.DEPARTMENT.value,
            ExpensesColumn.YEAR.value,
            *months,
        ],
        converters={month: convert_money_to_float for month in months},
    )


def filter_expenses_dataframe(
    expenses_dataframe: pd.DataFrame, department: str, year: int | None = None
) -> pd.DataFrame:
    expenses_dataframe = expenses_dataframe[
        expenses_dataframe[ExpensesColumn.DEPARTMENT.value] == department
    ]

    if expenses_dataframe.empty:
        print(f"No expenses found for {department} department")
        sys.exit(1)

    if year is not None:
        expenses_dataframe = expenses_dataframe[
            expenses_dataframe[ExpensesColumn.YEAR.value] == year
        ]

        if expenses_dataframe.empty:
            print(f"No expenses found for {department} department in year {year}")
            sys.exit(1)

    return expenses_dataframe


def aggregate_expenses(
    department: str, months: list[str], year: int | None = None
) -> None:
    expenses_dataframe = get_expenses_dataframe(months)

    expenses_dataframe = filter_expenses_dataframe(expenses_dataframe, department, year)

    expenses_aggregated = expenses_dataframe.aggregate(
        {month: "sum" for month in months}
    )

    total_expenses = expenses_aggregated.sum()
    total_expenses_formatted = convert_float_to_money(total_expenses)

    print(f"Aggregate expenses for {department} department: {total_expenses_formatted}")


def get_command_args() -> Namespace:
    command_parser = ArgumentParser()

    command_parser.add_argument(
        "--department",
        required=True,
        type=str,
        help="Aggregated expenses of a given company department",
    )

    command_parser.add_argument(
        "--year", type=int, help="Aggregated expenses in a specific year"
    )

    period_group = command_parser.add_mutually_exclusive_group()

    period_group.add_argument(
        "--quarter",
        type=int,
        choices=QUARTERS.keys(),
        help="Aggregated expenses in a specific quarter",
    )

    period_group.add_argument(
        "--month",
        type=str,
        choices=MONTHS,
        help="Aggregated expenses in a specific month",
    )

    return command_parser.parse_args()


def main() -> None:
    command_args: Namespace = get_command_args()

    months: list[str] = []
    if command_args.quarter is not None:
        months.extend(QUARTERS[command_args.quarter])
    elif command_args.month is not None:
        months.append(command_args.month)
    else:
        months.extend(MONTHS)

    aggregate_expenses(command_args.department, months, command_args.year)


if __name__ == "__main__":
    main()
