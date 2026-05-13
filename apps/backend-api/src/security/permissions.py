from enum import Enum
from typing import List

class Role(str, Enum):
    OWNER = "owner"
    ADMIN = "admin"
    MEMBER = "member"

class Permission(str, Enum):
    DATASET_CREATE = "dataset:create"
    DATASET_DELETE = "dataset:delete"
    TRAINING_CREATE = "training:create"
    DEPLOYMENT_CREATE = "deployment:create"
    API_KEYS_CREATE = "api_keys:create"

ROLE_PERMISSIONS = {
    Role.OWNER: [p for p in Permission],
    Role.ADMIN: [
        Permission.DATASET_CREATE,
        Permission.TRAINING_CREATE,
        Permission.DEPLOYMENT_CREATE,
        Permission.API_KEYS_CREATE,
    ],
    Role.MEMBER: [
        Permission.DATASET_CREATE,
        Permission.TRAINING_CREATE,
    ],
}
