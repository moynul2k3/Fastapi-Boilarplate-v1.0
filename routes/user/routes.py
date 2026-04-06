from datetime import datetime
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, HTTPException, Depends, Form, UploadFile, File, Query
from tortoise.contrib.pydantic import pydantic_model_creator
from tortoise.expressions import Q
from tortoise.transactions import in_transaction

from app.auth import login_required
from applications.user.models import User, UserRole
from app.utils.otp_manager import verify_otp
from app.utils.file_manager import save_file, update_file, delete_file
from applications.user.schemas import serialize_user

router = APIRouter(prefix="/users", tags=["Users"])

# Serializers
UserOut = pydantic_model_creator(User, name="UserOut", exclude=("password",))



# CRUD endpoints
@router.get("/", response_model=List[Dict[str, Any]])
async def list_users(
    offset: int = 0,
    limit: int = 20,
    role: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    user: Optional[User] = Depends(login_required)
):
    query = User.all()
    if role:
        try:
            role_list = [
                UserRole(r.strip().upper())
                for r in role.split(",")
            ]
            query = query.filter(role__in=role_list).exclude(id=user.id)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid role value")

    if user.role == UserRole.ADMIN:
        query = query.exclude(role=UserRole.ADMIN)

    if search:
        q = search.strip()
        query = query.filter(
            Q(name__icontains=q) |
            Q(email__icontains=q) |
            Q(phone__icontains=q)
        )

    users = await query.offset(offset).limit(limit)

    return [await serialize_user(u) for u in users]



@router.put("/me/update-credientials", response_model=Dict[str, Any])
async def update_credentials(
    user: User = Depends(login_required),
    email: Optional[str] = Form(None),
    old_password: Optional[str] = Form(None),
    new_password: Optional[str] = Form(None),
    email_otp: Optional[str] = Form(None, description="Need otp for purpose 'update_email'"),
):
    if email and email != user.email:
        if not email_otp:
            raise HTTPException(400, "OTP required to change email")
        await verify_otp(user.email, email_otp, "update_email")
        user.email = email

    if new_password:
        if not old_password:
            raise HTTPException(400, "Old password is required")
        if not user.verify_password(old_password):
            raise HTTPException(400, "Old password incorrect")
        user.set_password(new_password)

    await user.save()
    user = await serialize_user(user)
    return {
        "details": "Password updated successfully",
        "user_data": user,
    }


# -------------------------------
# Get current user
# -------------------------------
@router.get("/me", response_model=Dict[str, Any])
async def get_user(user: User = Depends(login_required)):
    return await serialize_user(user)


# -------------------------------
# Update profile
# -------------------------------
@router.patch("/me/update-profile", response_model=Dict[str, Any])
async def update_profile(
    user: User = Depends(login_required),
    name: Optional[str] = Form(None),
    date_of_birth: Optional[str] = Form(None),
    address: Optional[str] = Form(None),
    phone: Optional[str] = Form(None),
    photo: Optional[UploadFile] = File(None)
):
    update_data = {}

    if name is not None:
        update_data["name"] = name
    if date_of_birth is not None:
        try:
            update_data["dob"] = datetime.strptime(date_of_birth, "%Y-%m-%d").date()
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid date format, expected YYYY-MM-DD")
    if address is not None:
        update_data["address"] = address
    if phone is not None:
        update_data["phone"] = phone

    if not user.photo and photo is not None:
        update_data["photo"] = await save_file(photo, "profile_photos")
    elif user.photo and photo is not None:
        update_data["photo"] = await update_file(photo, user.photo, "profile_photos")

    if not update_data:
        raise HTTPException(status_code=400, detail="No valid fields provided")

    async with in_transaction():
        for field, value in update_data.items():
            setattr(user, field, value)
        await user.save()

    return await serialize_user(user)



@router.delete("/delete", response_model=Dict[str, Any])
async def delete_user(
    user: User = Depends(login_required),
):
    user = await User.get_or_none(id=user.id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if user.photo:
        await delete_file(user.photo)
    await user.delete()
    return {
        "detail": "User successfully deleted"
    }