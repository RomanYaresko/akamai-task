from decimal import Decimal

from pydantic import BaseModel, Field, PositiveInt, model_validator


class ExpenseAggregatedRequest(BaseModel):
    department_id: PositiveInt
    year: int | None = Field(default=None, ge=1, le=9999)
    month: int | None = Field(default=None, ge=1, le=12)
    quarter: int | None = Field(default=None, ge=1, le=4)

    @model_validator(mode="after")
    def validate_month_and_quarter(self):
        if self.month is not None and self.quarter is not None:
            raise ValueError("Only one of 'month' or 'quarter' can be provided.")
        return self


class ExpenseAggregatedResponse(BaseModel):
    total: Decimal = Field(max_digits=12, decimal_places=2)
