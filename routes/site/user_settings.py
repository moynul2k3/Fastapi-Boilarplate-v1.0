from fastapi import APIRouter, HTTPException, Depends, Form
from applications.site.settings import UserSettings
from applications.user.models import User
from app.auth import login_required

router = APIRouter(prefix="/user-settings", tags=["User Settings"])

LANGUAGE_CHOICES = ("ENGLISH", "FRENCH")


# -----------------------------
# Get user settings for logged-in user
# -----------------------------
@router.get("/", response_model=dict)
async def get_user_settings(user: User = Depends(login_required)):
    settings = await UserSettings.get_or_none(user=user)
    if not settings:
        settings = await UserSettings.create(user=user)

    return {
        "user_id": str(settings.user_id),
        "email_notifications": settings.email_notifications,
        "push_notifications": settings.push_notifications,
        "promotional_notifications": settings.promotional_notifications,
        "parental_notifications": settings.parental_notifications,
        "user_activity_alerts": settings.user_activity_alerts,
        "language": settings.language
    }


# -----------------------------
# Create or update user settings using Form
# -----------------------------
@router.post("/", response_model=dict)
async def create_or_update_user_settings(
    email_notifications: bool = Form(False),
    push_notifications: bool = Form(False),
    promotional_notifications: bool = Form(False),
    parental_notifications: bool = Form(False),
    user_activity_alerts: bool = Form(False),
    language: str = Form("ENGLISH"),
    user: User = Depends(login_required)
):
    # Validate language choice
    if language not in LANGUAGE_CHOICES:
        raise HTTPException(status_code=400, detail="Invalid language choice")

    data = {
        "email_notifications": email_notifications,
        "push_notifications": push_notifications,
        "promotional_notifications": promotional_notifications,
        "parental_notifications": parental_notifications,
        "user_activity_alerts": user_activity_alerts,
        "language": language
    }

    # Fetch existing settings
    settings = await UserSettings.get_or_none(user=user)

    if settings:
        # Update existing settings
        await settings.update_from_dict(data)
        await settings.save()
        await settings.fetch_related('user')  # <--- Refresh related user
    else:
        # Create new settings
        settings = await UserSettings.create(user=user, **data)
        await settings.fetch_related('user')  # <--- Fetch related user

    return {
        "user_id": str(settings.user.id),
        "email_notifications": settings.email_notifications,
        "push_notifications": settings.push_notifications,
        "promotional_notifications": settings.promotional_notifications,
        "parental_notifications": settings.parental_notifications,
        "user_activity_alerts": settings.user_activity_alerts,
        "language": settings.language
    }
