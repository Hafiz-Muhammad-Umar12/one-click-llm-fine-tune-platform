from typing import List, Optional
from fastapi import Depends, Path
from sqlalchemy.ext.asyncio import AsyncSession
from src.api.deps.auth import get_current_user
from src.db.session import get_db
from src.models.models import User
from src.repositories.organization import organization_repo
from src.security.permissions import Permission, Role, ROLE_PERMISSIONS
from src.exceptions.base import PermissionException

class PermissionChecker:
    def __init__(self, required_permissions: List[Permission]):
        self.required_permissions = required_permissions

    async def __call__(
        self,
        organization_id: str = Path(...),
        current_user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_db),
    ):
        if current_user.is_superuser:
            return True

        role = await organization_repo.get_user_role(
            db, user_id=current_user.id, organization_id=organization_id
        )
        
        if not role:
            raise PermissionException(detail="Not a member of this organization")

        user_permissions = ROLE_PERMISSIONS.get(role, [])
        for perm in self.required_permissions:
            if perm not in user_permissions:
                raise PermissionException(
                    detail=f"Missing required permission: {perm}"
                )
        
        return True
