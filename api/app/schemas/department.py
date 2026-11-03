from pydantic import BaseModel, ConfigDict


class DepartmentResponse(BaseModel):
    id: int
    name: str

    model_config = ConfigDict(from_attributes=True)


class DepartmentListResponse(BaseModel):
    items: list[DepartmentResponse]
