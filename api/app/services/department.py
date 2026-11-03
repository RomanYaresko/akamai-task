from app.repositories.department import DepartmentRepository
from app.schemas.department import DepartmentResponse


class DepartmentService:
    def __init__(self, repository: DepartmentRepository) -> None:
        self.repository = repository

    async def get_all_departments(self) -> list[DepartmentResponse]:
        departments = await self.repository.get_all()
        return [
            DepartmentResponse.model_validate(department) for department in departments
        ]
