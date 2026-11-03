from decimal import Decimal
from typing import Annotated, Self

from app.constants.expenses_file import MONTHS, QUARTERS
from fastapi import File, UploadFile
from pydantic import BaseModel, Field, field_validator, model_validator


class ExpensesFileAggregatedRequest(BaseModel):
    department_name: str = Field(min_length=1)
    year: int | None = Field(default=None, ge=1, le=9999)
    month: str | None = None
    quarter: int | None = None
    upload_file: Annotated[UploadFile, File()]

    @field_validator("month")
    @classmethod
    def validate_month(cls, value: str | None) -> str | None:
        if value is not None and value not in MONTHS:
            raise ValueError(f"Month must be one of: {', '.join(MONTHS)}")
        return value

    @field_validator("quarter")
    @classmethod
    def validate_quarter(cls, value: int | None) -> int | None:
        if value is not None and value not in QUARTERS:
            raise ValueError(f"Quarter must be one of: {tuple(QUARTERS)}")
        return value

    @model_validator(mode="after")
    def validate_month_and_quarter(self):
        if self.month is not None and self.quarter is not None:
            raise ValueError("Only one of 'month' or 'quarter' can be provided.")
        return self

    @model_validator(mode="after")
    def check_file_type_validation(self) -> Self:
        if self.upload_file.content_type != "text/csv":
            raise ValueError("File Type not supported")

        return self


class ExpensesFileAggregatedResponse(BaseModel):
    department_name: str = Field(min_length=1)
    total: Decimal = Field(max_digits=12, decimal_places=2)


class ExpensesFileImportRequest(BaseModel):
    upload_file: Annotated[UploadFile, File()]

    @model_validator(mode="after")
    def check_file_type_validation(self) -> Self:
        if self.upload_file.content_type != "text/csv":
            raise ValueError("File Type not supported")

        return self
