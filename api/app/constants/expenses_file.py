from enum import Enum


class ExpensesColumn(Enum):
    DEPARTMENT = "Department"
    EXPENSE_TYPE = "Expense Type"
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
