from datetime import datetime
from typing import Optional, Dict, Any
from fastapi import APIRouter, HTTPException, Depends, Form, UploadFile, File, Query
from tortoise.contrib.pydantic import pydantic_model_creator
from tortoise.transactions import in_transaction

from app.auth import role_required
from applications.user.models import User, UserRole
from app.utils.file_manager import save_file
from applications.user.schemas import serialize_user

router = APIRouter(prefix="/users/create", tags=["Create Users"])

# Serializers
UserOut = pydantic_model_creator(User, name="UserOut", exclude=("password",))




@router.post("/create", response_model=Dict[str, Any], dependencies=[Depends(role_required(UserRole('ADMIN')))], description="Only ADMIN can create users")
async def create_user(
    email: str = Form(...),
    password: str = Form(...),
    name: Optional[str] = Form(None),
    phone: Optional[str] = Form(None),
    address: Optional[str] = Form(None),
    date_of_birth: Optional[str] = Form(None),
    role: Optional[UserRole] = Form(UserRole.USER),
    photo: Optional[UploadFile] = File(None),
):
    # Check if user already exists
    existing = await User.get_or_none(email=email)
    if existing:
        raise HTTPException(status_code=400, detail="User with this email already exists")

    # Parse date_of_birth if provided
    dob = None
    if date_of_birth:
        try:
            dob = datetime.strptime(date_of_birth, "%Y-%m-%d").date()
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid date format, expected YYYY-MM-DD")

    # Save photo if provided
    photo_path = None
    if photo:
        photo_path = await save_file(photo, upload_to="users")  # Assuming save_file returns file path

    async with in_transaction():
        user = await User.create(
            email=email,
            password=password,
            name=name,
            phone=phone,
            address=address,
            dob=dob,
            role=role,
            photo=photo_path
        )

    return await serialize_user(user)
