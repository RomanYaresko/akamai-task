from typing import Annotated

from fastapi import APIRouter, Form, HTTPException, Response, status

from app.dependencies import (
    ExpenseServiceDep,
    ExpensesFileServiceDep,
)
from app.schemas.expense import ExpenseAggregatedRequest, ExpenseAggregatedResponse
from app.schemas.expenses_file import (
    ExpensesFileAggregatedRequest,
    ExpensesFileAggregatedResponse,
    ExpensesFileImportRequest,
)
from app.services.expense import InvalidDepartmentError
from app.services.expenses_file import (
    ExpensesFileDataframeError,
    ExpensesFileDepartmentError,
    ExpensesFileMappingError,
    ExpensesFileYearError,
)

router = APIRouter(prefix="/expenses", tags=["Expenses"])


@router.post(
    "/aggregated",
    response_model=ExpenseAggregatedResponse,
    status_code=status.HTTP_200_OK,
)
async def aggregated(
    service: ExpenseServiceDep,
    data: Annotated[
        ExpenseAggregatedRequest,
        Form(),
    ],
) -> ExpenseAggregatedResponse:
    months = service.get_months_list(data.month, data.quarter)

    try:
        total = await service.get_aggregated_expenses(
            department_id=data.department_id,
            year=data.year,
            months=months,
        )
    except InvalidDepartmentError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc

    return ExpenseAggregatedResponse(total=total)


@router.post(
    "/aggregated/file",
    response_model=ExpensesFileAggregatedResponse,
    status_code=status.HTTP_200_OK,
)
def from_file(
    service: ExpensesFileServiceDep,
    data: Annotated[
        ExpensesFileAggregatedRequest,
        Form(media_type="multipart/form-data"),
    ],
) -> ExpensesFileAggregatedResponse:
    months = service.get_months_list(data.month, data.quarter)

    try:
        total = service.get_aggregated_expenses(
            file=data.upload_file.file,
            department=data.department_name,
            year=data.year,
            months=months,
        )
    except (ExpensesFileDepartmentError, ExpensesFileYearError) as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
    except (ExpensesFileMappingError, ExpensesFileDataframeError) as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=str(exc),
        ) from exc

    return ExpensesFileAggregatedResponse(
        department_name=data.department_name,
        total=total,
    )


@router.post(
    "/import-file",
    response_class=Response,
    status_code=status.HTTP_201_CREATED,
)
async def import_file(
    service: ExpensesFileServiceDep,
    data: Annotated[
        ExpensesFileImportRequest,
        Form(media_type="multipart/form-data"),
    ],
) -> None:
    try:
        await service.import_expenses(data.upload_file.file)
    except (ExpensesFileMappingError, ExpensesFileDataframeError) as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=str(exc),
        ) from exc

    return
