from datetime import date
from typing import Optional

from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status, Form, Request, Response
from pydantic import BaseModel
from pydantic import EmailStr
from fastapi.security import OAuth2PasswordRequestForm
from passlib.context import CryptContext

from app.config import settings
from applications.user.models import User, UserRole
from applications.site.settings import PlatformSettings
from app.token import (
    get_current_user,
    create_access_token,
    create_refresh_token,
    set_auth_cookies,
    ACCESS_COOKIE_NAME,
    REFRESH_COOKIE_NAME,
)
from tortoise.contrib.pydantic import pydantic_model_creator
from app.utils.otp_manager import generate_otp, verify_otp, verify_session_key
import re

router = APIRouter()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


async def detect_input_type(value: str) -> str:
    value = value.strip()
    email_regex = r'^[\w\.-]+@[\w\.-]+\.\w+$'

    if re.match(email_regex, value):
        return 'email'
    else:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid Email address.")


class OAuth2EmailPasswordForm:
    def __init__(
            self,
            email: EmailStr = Form(...),
            password: str = Form(...),
            scope: str = Form(""),
            client_id: str = Form(None),
            client_secret: str = Form(None),
    ):
        self.email = email
        self.password = password
        self.scopes = scope.split()
        self.client_id = client_id
        self.client_secret = client_secret


User_Pydantic = pydantic_model_creator(User, name="User")


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str


@router.post("/login_auth2/", response_model=TokenResponse, tags=["User Authentication"])
async def login_auth2(response: Response, form_data: OAuth2PasswordRequestForm = Depends()):
    user = await User.get_or_none(email=form_data.username)  # <- use username as email
    if not user or not pwd_context.verify(form_data.password, user.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token_data = {
        "sub": str(user.id),
        "is_active": user.is_active,
        "role": user.role,
        "is_staff": user.is_staff,
    }

    access_token = create_access_token(token_data)
    refresh_token = create_refresh_token(token_data)
    set_auth_cookies(response, access_token, refresh_token)

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
    }


@router.post("/login/", tags=["User Authentication"] , description="""
    Login Credentials (from dummy seed):

    Super Admin > superadmin@gmail.com > pass: supadmin > Role: ADMIN (Superadmin)

    Staff One > staff1@gmail.com > pass: staff > Role: ADMIN (Staff)
    Staff Two > staff2@gmail.com > pass: staff > Role: ADMIN (Staff)
    Admin One > admin@gmail.com > pass: admin > Role: ADMIN
    Admin Two > admin1@gmail.com > pass: admin > Role: ADMIN

    Organization 1-5 > organization{1..5}@gmail.com > pass: org > Role: ORGANIZATION

    User No Org 1-5 > user_no_org{1..5}@gmail.com > pass: user > Role: USER

    Org User 1-15 > user_org{1..15}@gmail.com > pass: user > Role: USER
    """
)
async def login(
    response: Response,
    email: str = Form(...),
    password: str = Form(...)
):
    lookup_field = await detect_input_type(email)

    if lookup_field == "email":
        user = await User.get_or_none(email=email)

        if not user or not pwd_context.verify(password, user.password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials"
            )

        token_data = {
            "sub": str(user.id),
            "is_active": user.is_active,
            "role": user.role,
            "is_staff": user.is_staff,
        }

        access_token = create_access_token(token_data)
        refresh_token = create_refresh_token(token_data)
        set_auth_cookies(response, access_token, refresh_token)

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "role": user.role,
        }
    return HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid credentials")



@router.post("/send_otp/", tags=["User Authentication"])
async def send_otp(
    email: str = Form(...),
    purpose: str = Form(
        "signup",
        description="""signup, organization_signup, forgot_password, update_email"""),
):
    platform = await PlatformSettings.first()
    key_type = await detect_input_type(email)
    if key_type != "email":
        raise HTTPException(status_code=400, detail="Invalid email")

    user = await User.get_or_none(email=email)
    SIGNUP_PURPOSES = {"signup", "organization_signup"}
    FORGOT_PURPOSES = {"forgot_password", "update_email"}

    # -----------------------------
    # Purpose validation
    # -----------------------------
    if purpose in SIGNUP_PURPOSES:
        if purpose == 'signup' and not platform.allow_user_registration:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Signup is disabled")
        if purpose == 'organization_signup' and not platform.allow_organization_registration:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Signup is disabled")
        if user:
            raise HTTPException(
                status_code=400,
                detail="Email already registered. Please login.",
            )

    elif purpose in FORGOT_PURPOSES:
        if not user:
            raise HTTPException(
                status_code=400,
                detail="User not found for password reset.",
            )
    else:
        raise HTTPException(status_code=400, detail="Invalid purpose")

    # -----------------------------
    # Generate OTP
    # -----------------------------
    try:
        otp = await generate_otp(email, purpose)
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=500, detail="Failed to generate OTP")

    return {
        "status": "success",
        "message": (
            f"OTP sent to {email}. Expires in 5 minute."
            f"{f' OTP: {otp}' if settings.DEBUG else ''}"
        ),
        "purpose": purpose,
    }



@router.post("/signup/", response_model=dict, tags=["User Authentication"])
async def signup(
    email: str = Form(...),
    organization_id: Optional[UUID] = Form(None),
    password: str = Form(...),
    otp_value: str = Form(...),
    purpose: str = Form(
        "signup",
        description="""signup, organization_signup""",
    ),
):

    try:
        await verify_otp(email, otp_value, purpose)
    except Exception:
        raise HTTPException(
            status_code=400,
            detail="OTP verification failed. Enter correct OTP.",
        )

    lookup_field = await detect_input_type(email)
    if lookup_field != "email":
        raise HTTPException(status_code=400, detail="Invalid email")

    if await User.get_or_none(email=email):
        raise HTTPException(status_code=400, detail="Email already registered")

    ROLE_MAP = {
        "signup": {
            "role": UserRole.USER,
        },
        "organization_signup": {
            "role": UserRole.ORGANIZATION,
        },
    }

    if purpose not in ROLE_MAP:
        raise HTTPException(status_code=400, detail="Invalid signup purpose")

    role_data = ROLE_MAP[purpose]

    hashed_password = pwd_context.hash(password)

    user = await User.create(
        email=email,
        password=hashed_password,
        role=role_data["role"],
        organization_id=organization_id if role_data["role"] == UserRole.USER else None,
        is_active=True,
    )

    token_data = {
        "sub": str(user.id),
        "role": user.role,
        "is_active": user.is_active,
        "is_staff": user.is_staff,
    }

    return {
        "message": "User created successfully",
        "access_token": create_access_token(token_data),
        "refresh_token": create_refresh_token(token_data),
        "token_type": "bearer",
        "role": user.role,
    }


@router.post("/verify_otp/", tags=["User Authentication"])
async def verify_otp_route(
    email: str = Form(...),
    otp_value: str = Form(...),
    purpose: str = Form(...),
):
    try:
        session_key = await verify_otp(email, otp_value, purpose)
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

    return {
        "status": "success",
        "message": "OTP verified successfully.",
        "sessionKey": session_key,
        "purpose": purpose,
    }



@router.post("/reset_password/", response_model=dict, tags=["User Authentication"])
async def reset_password(
        user: User = Depends(get_current_user),
        old_password: str = Form(...),
        password: str = Form(...)
):
    is_verified = user.verify_password(old_password)
    if not is_verified:
        raise HTTPException(status_code=400, detail="Invalid Old Password")
    user.password = user.set_password(password)
    await user.save()

    token_data = {
        "sub": str(user.id),
        "is_active": user.is_active,
        "role": user.role,
        "is_staff": user.is_staff,
    }

    access_token = create_access_token(token_data)
    refresh_token = create_refresh_token(token_data)

    return {
        "message": "Password reset successfully",
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
    }


@router.post("/forgot_password/", response_model=dict, tags=["User Authentication"])
async def forgot_password(
    email: str = Form(...),
    password: str = Form(...),
    session_key: str = Form(...),
):
    lookup_field = await detect_input_type(email)


    if lookup_field == "email":
        user = await User.get_or_none(email=email)
    elif lookup_field == "phone":
        user = await User.get_or_none(phone=email)
    else:
        user = await User.get_or_none(username=email)

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    try:
        await verify_session_key(email, session_key, purpose="forgot_password")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Session key invalid: {e}")

    user.password = pwd_context.hash(password)
    await user.save()

    token_data = {
        "sub": str(user.id),
        "is_active": user.is_active,
        "role": user.role,
        "is_staff": user.is_staff,
    }

    access_token = create_access_token(token_data)
    refresh_token = create_refresh_token(token_data)

    return {
        "status": "success",
        "message": "Password reset successfully",
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
    }

@router.get("/verify-token/", tags=["User Authentication"])
async def verify_token(request: Request, response: Response, user: User = Depends(get_current_user)):
    response_data = {
        "status": "success",
        "id": user.id,
        "name": f"{user.name}",
        "role": user.role,
        "email": user.email,
        "is_active": user.is_active,
        "is_staff": user.is_staff,
        "image": getattr(user, "photo", None),
        "address": getattr(user, "address", None),
        "phone": getattr(user, "phone", None),
        "dob": getattr(user, "dob", None),
    }

    if hasattr(request.state, "new_tokens"):
        response_data["new_tokens"] = request.state.new_tokens
        set_auth_cookies(
            response,
            request.state.new_tokens["access_token"],
            request.state.new_tokens["refresh_token"],
        )

    return response_data


@router.get("/swagger-auth-token/", tags=['swagger-auth'])
async def swagger_auth_token(
    request: Request,
    response: Response,
    user: User = Depends(get_current_user),
):
    access_token = request.cookies.get("access_token")

    if hasattr(request.state, "new_tokens"):
        access_token = request.state.new_tokens["access_token"]
        set_auth_cookies(
            response,
            request.state.new_tokens["access_token"],
            request.state.new_tokens["refresh_token"],
        )

    return {"access_token": access_token}


@router.post("/logout/", tags=['swagger-auth'])
async def logout(response: Response):
    # Clear cookies in a browser-compatible way by both deleting and expiring.
    cookie_secure = not settings.DEBUG
    for cookie_name in (ACCESS_COOKIE_NAME, REFRESH_COOKIE_NAME):
        response.delete_cookie(key=cookie_name, path="/")
        response.set_cookie(
            key=cookie_name,
            value="",
            max_age=0,
            expires=0,
            path="/",
            secure=cookie_secure,
            httponly=True,
            samesite="lax",
        )
    # Ask browser to clear local/session storage used by Swagger persisted auth.
    response.headers["Clear-Site-Data"] = "\"cookies\", \"storage\""
    return {"status": "success", "message": "Logged out successfully"}


