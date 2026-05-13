from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from src.models.models import Organization, user_organization
from src.repositories.base import BaseRepository
from src.schemas.organization import OrganizationCreate, OrganizationUpdate

class OrganizationRepository(BaseRepository[Organization, OrganizationCreate, OrganizationUpdate]):
    async def get_by_slug(self, db: AsyncSession, slug: str) -> Optional[Organization]:
        query = select(self.model).where(self.model.slug == slug)
        result = await db.execute(query)
        return result.scalar_one_or_none()

    async def get_user_role(self, db: AsyncSession, *, user_id: str, organization_id: str) -> Optional[str]:
        query = select(user_organization.c.role).where(
            user_organization.c.user_id == user_id,
            user_organization.c.organization_id == organization_id
        )
        result = await db.execute(query)
        return result.scalar()

organization_repo = OrganizationRepository(Organization)
