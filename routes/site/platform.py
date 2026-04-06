from fastapi import APIRouter, HTTPException, Depends, Form
from applications.site.settings import PlatformSettings
from app.auth import role_required
from applications.user.models import UserRole

router = APIRouter(
    prefix="/platform-settings",
    tags=["Platform Settings"],
    dependencies=[Depends(role_required(UserRole("ADMIN")))]
)


# -----------------------------
# Get platform settings
# -----------------------------
@router.get("/", response_model=dict)
async def get_platform_settings():
    settings = await PlatformSettings.first()
    if not settings:
        data = {
            "support_email": "support_email@gmail.com",
            "admin_email": 'admin_email@gmail.com',
            "allow_user_registration": True,
            "allow_organization_registration": True
        }
        settings = await PlatformSettings.create(**data)

    return {
        "support_email": settings.support_email,
        "admin_email": settings.admin_email,
        "allow_user_registration": settings.allow_user_registration,
        "allow_organization_registration": settings.allow_organization_registration
    }


# -----------------------------
# Create or update platform settings using Form
# -----------------------------
@router.patch("/", response_model=dict)
async def create_or_update_platform_settings(
        support_email: str = Form(...),
        admin_email: str = Form(...),
        allow_user_registration: bool = Form(True),
        allow_organization_registration: bool = Form(True)
):
    settings = await PlatformSettings.first()

    data = {
        "support_email": support_email,
        "admin_email": admin_email,
        "allow_user_registration": allow_user_registration,
        "allow_organization_registration": allow_organization_registration
    }

    if settings:
        await settings.update_from_dict(data)
        await settings.save()
    else:
        settings = await PlatformSettings.create(**data)

    return {
        "id": str(settings.id),
        "support_email": settings.support_email,
        "admin_email": settings.admin_email,
        "allow_user_registration": settings.allow_user_registration,
        "allow_organization_registration": settings.allow_organization_registration
    }
