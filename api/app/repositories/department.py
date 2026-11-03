from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.department import Department


class DepartmentRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_id(
        self,
        id: int,
    ) -> Department | None:
        statement = select(Department).where(Department.id == id)
        result = await self.session.scalar(statement)

        return result

    async def get_all(self) -> list[Department]:
        statement = select(Department)
        result = await self.session.scalars(statement)

        return result.all()

    async def get_by_names(self, names: list[str]) -> list[Department]:
        if not names:
            return []

        statement = select(Department).where(Department.name.in_(names))
        result = await self.session.scalars(statement)

        return result.all()

    async def create_many(self, names: list[str]) -> list[Department]:
        departments = [Department(name=name) for name in names]
        self.session.add_all(departments)
        await self.session.flush()

        return departments

    async def get_or_create_many(
        self,
        names: list[str],
    ) -> list[Department]:
        existing_departments = await self.get_by_names(names)

        existing_names = {department.name for department in existing_departments}
        missing_names = [name for name in names if name not in existing_names]

        created_departments = await self.create_many(missing_names)

        return existing_departments + created_departments
