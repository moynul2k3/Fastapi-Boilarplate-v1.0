from typing import List
from fastapi import APIRouter, Depends, HTTPException, Form, BackgroundTasks
from pydantic import EmailStr
from app.config import settings
from app.auth import role_required
from app.utils.otp_manager import templates
from app.utils.send_email import send_email
from applications.user.models import UserRole, User

router = APIRouter(prefix="/invite", tags=["Send Invitation"])


@router.post("/send")
async def send_invitation(
    emails: List[EmailStr] = Form(...),
    background_tasks: BackgroundTasks = BackgroundTasks(),
    current_user: User = Depends(role_required(UserRole.ORGANIZATION))
):
    if not emails:
        raise HTTPException(status_code=400, detail="No emails provided")

    for email in emails:
        invitation_url = f"{settings.FRONTEND_URL}/signup?org_id={current_user.id}"

        subject = "You're invited to join"

        body = (
            f"Hello,\n\n"
            f"You have been invited by {current_user.name or "Unnamed user"} to join our platform.\n\n "
            f"to join our platform.\n\n"
            f"Please set your password using the link below:\n"
            f"{invitation_url}\n\n"
            f"If you did not expect this invitation, you can ignore this email.\n\n"
            f"Thank you!"
        )

        context = {
            "inviter_name": current_user.name,
            "invitation_url": invitation_url,
        }

        template = templates.get_template("send_invitation.html")
        html_message = template.render(context)

        background_tasks.add_task(
            send_email,
            to=email,
            subject=subject,
            message=body,
            html_message=html_message,
        )

    return {
        "status": "success",
        "message": f"Invitation sent to {len(emails)} user(s)."
    }
