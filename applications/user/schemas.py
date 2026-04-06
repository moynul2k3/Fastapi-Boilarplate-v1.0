from typing import Dict, Any
from applications.user.models import User, UserRole


async def serialize_user(user: User | None) -> Dict[str, Any]:
    if not user:
        return {}

    await user.fetch_related("groups", "user_permissions")

    protected_data = {}

    if user.role == UserRole.ADMIN:
        protected_data = {
            "is_staff": user.is_staff,
            "is_superadmin": user.is_superadmin,
            "groups": [
                {"id": g.id, "name": g.name} for g in user.groups
            ],
            "permissions": [
                {"id": p.id, "codename": p.codename, "name": p.name}
                for p in user.user_permissions
            ],
            "organization_id": user.organization_id,
        }

    return {
        "id": user.id,
        "name": user.name,
        "email": user.email,
        "photo": user.photo,
        "phone": user.phone,
        "address": user.address,
        "dob": user.dob.isoformat() if user.dob else None,
        "role": user.role,
        "is_active": user.is_active,
        "created_at": user.created_at.isoformat() if user.created_at else None,
        "updated_at": user.updated_at.isoformat() if user.updated_at else None,
        **protected_data,
    }