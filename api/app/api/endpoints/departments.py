from fastapi import APIRouter, status

from app.dependencies import DepartmentServiceDep
from app.schemas.department import DepartmentListResponse

router = APIRouter(prefix="/departments", tags=["Departments"])


@router.get(
    "/all",
    response_model=DepartmentListResponse,
    status_code=status.HTTP_200_OK,
)
async def all(service: DepartmentServiceDep) -> DepartmentListResponse:
    departments = await service.get_all_departments()
    return DepartmentListResponse(items=departments)
