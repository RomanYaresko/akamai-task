from decimal import Decimal

import pytest
from app.core.config import settings
from app.models import Department, Expense, ExpenseType
from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker

API_PATH = f"{settings.api_prefix}/expenses"


async def persist_expenses(engine, rows):
    session_factory = async_sessionmaker(engine, expire_on_commit=False)

    async with session_factory() as session:
        departments = {}
        expense_types = {}

        for department_name, expense_type_name, *_ in rows:
            if department_name not in departments:
                departments[department_name] = Department(name=department_name)
            if expense_type_name not in expense_types:
                expense_types[expense_type_name] = ExpenseType(name=expense_type_name)

        session.add_all([*departments.values(), *expense_types.values()])
        await session.flush()
        session.add_all(
            [
                Expense(
                    department_id=departments[department_name].id,
                    expense_type_id=expense_types[expense_type_name].id,
                    year=year,
                    month=month,
                    amount=amount,
                )
                for department_name, expense_type_name, year, month, amount in rows
            ]
        )
        await session.commit()

    return departments


@pytest.mark.asyncio
async def test_aggregated_expenses_sums_department_year_and_quarter(
    client, test_engine
):
    departments = await persist_expenses(
        test_engine,
        [
            ("Finance", "Travel", 2025, 4, Decimal("10.25")),
            ("Finance", "Travel", 2025, 5, Decimal("20.25")),
            ("Finance", "Travel", 2025, 7, Decimal("30.25")),
            ("Finance", "Travel", 2024, 4, Decimal("40.25")),
            ("Operations", "Travel", 2025, 4, Decimal("50.25")),
        ],
    )

    response = await client.post(
        f"{API_PATH}/aggregated",
        data={
            "department_id": str(departments["Finance"].id),
            "year": "2025",
            "quarter": "2",
        },
    )

    assert response.status_code == 200
    assert response.json() == {"total": "30.50"}


@pytest.mark.asyncio
async def test_aggregated_expenses_returns_not_found_for_unknown_department(client):
    response = await client.post(
        f"{API_PATH}/aggregated",
        data={"department_id": "999"},
    )

    assert response.status_code == 404
    assert response.json() == {"detail": "Invalid Department"}


@pytest.mark.asyncio
async def test_aggregated_expenses_rejects_month_and_quarter(client):
    response = await client.post(
        f"{API_PATH}/aggregated",
        data={"department_id": "1", "month": "4", "quarter": "2"},
    )

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_aggregated_file_sums_selected_months_and_year(client):
    csv_content = (
        "Department;Year;Apr;May;Jun;Jul\n"
        "Finance;2025;$10.25;$20.25;$30.25;$100.00\n"
        "Finance;2024;$40.00;$50.00;$60.00;$100.00\n"
        "Operations;2025;$70.00;$80.00;$90.00;$100.00\n"
    )

    response = await client.post(
        f"{API_PATH}/aggregated/file",
        data={"department_name": "Finance", "year": "2025", "quarter": "2"},
        files={"upload_file": ("expenses.csv", csv_content, "text/csv")},
    )

    assert response.status_code == 200
    assert response.json() == {"department_name": "Finance", "total": "60.75"}


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("department_name", "year", "csv_content", "status_code", "detail"),
    [
        (
            "Unknown",
            None,
            "Department;Year;Apr\nFinance;2025;$10.00\n",
            404,
            "Department not found",
        ),
        (
            "Finance",
            "2024",
            "Department;Year;Apr\nFinance;2025;$10.00\n",
            404,
            "Year not found",
        ),
        ("Finance", None, "", 422, "Unable to read CSV file"),
    ],
)
async def test_aggregated_file_reports_csv_and_filter_errors(
    client, department_name, year, csv_content, status_code, detail
):
    data = {"department_name": department_name, "month": "Apr"}
    if year is not None:
        data["year"] = year

    response = await client.post(
        f"{API_PATH}/aggregated/file",
        data=data,
        files={"upload_file": ("expenses.csv", csv_content, "text/csv")},
    )

    assert response.status_code == status_code
    assert response.json() == {"detail": detail}


@pytest.mark.asyncio
async def test_import_file_persists_expenses_and_reuses_existing_entities(
    client, test_engine
):
    existing = await persist_expenses(
        test_engine,
        [("Finance", "Travel", 2024, 1, Decimal("1.00"))],
    )
    csv_content = (
        "Department;Expense Type;Year;Jan;Feb;Mar;Apr;May;Jun;Jul;Aug;Sep;Oct;Nov;Dec\n"
        "Finance;Travel;2025;$10.00;$20.00;$30.00;$40.00;$50.00;$60.00;"
        "$70.00;$80.00;$90.00;$100.00;$110.00;$120.00\n"
        "Operations;Meals;2025;$1.00;$2.00;$3.00;$4.00;$5.00;$6.00;"
        "$7.00;$8.00;$9.00;$10.00;$11.00;$12.00\n"
    )

    response = await client.post(
        f"{API_PATH}/import-file",
        files={"upload_file": ("expenses.csv", csv_content, "text/csv")},
    )

    assert response.status_code == 201
    assert response.content == b""

    session_factory = async_sessionmaker(test_engine, expire_on_commit=False)
    async with session_factory() as session:
        departments = (await session.scalars(select(Department))).all()
        expense_types = (await session.scalars(select(ExpenseType))).all()
        imported_expenses = (
            await session.scalars(
                select(Expense)
                .where(Expense.year == 2025)
                .order_by(Expense.department_id, Expense.month)
            )
        ).all()

    assert {department.name for department in departments} == {
        "Finance",
        "Operations",
    }
    assert next(dept for dept in departments if dept.name == "Finance").id == (
        existing["Finance"].id
    )
    assert {expense_type.name for expense_type in expense_types} == {
        "Travel",
        "Meals",
    }
    assert len(imported_expenses) == 24
    assert [
        (expense.month, expense.amount)
        for expense in imported_expenses
        if expense.department_id == existing["Finance"].id
    ] == [
        (month, Decimal(amount))
        for month, amount in enumerate(
            (
                "10.00",
                "20.00",
                "30.00",
                "40.00",
                "50.00",
                "60.00",
                "70.00",
                "80.00",
                "90.00",
                "100.00",
                "110.00",
                "120.00",
            ),
            start=1,
        )
    ]


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("csv_content", "detail"),
    [
        (
            "Department;Expense Type;Year;Jan;Feb;Mar;Apr;May;Jun;Jul;Aug;Sep;Oct;Nov;Dec\n"
            "Finance;Travel;invalid;1;2;3;4;5;6;7;8;9;10;11;12\n",
            "Year values must be whole numbers from 1 to 9999",
        ),
        ("", "Unable to read CSV file"),
    ],
)
async def test_import_file_rejects_invalid_data_without_persisting(
    client, test_engine, csv_content, detail
):
    response = await client.post(
        f"{API_PATH}/import-file",
        files={"upload_file": ("expenses.csv", csv_content, "text/csv")},
    )

    assert response.status_code == 422
    assert response.json() == {"detail": detail}

    session_factory = async_sessionmaker(test_engine, expire_on_commit=False)
    async with session_factory() as session:
        assert (await session.scalar(select(Department))) is None
        assert (await session.scalar(select(ExpenseType))) is None
        assert (await session.scalar(select(Expense))) is None


@pytest.mark.asyncio
async def test_import_file_rejects_unsupported_content_type(client):
    response = await client.post(
        f"{API_PATH}/import-file",
        files={"upload_file": ("expenses.txt", b"data", "text/plain")},
    )

    assert response.status_code == 422
