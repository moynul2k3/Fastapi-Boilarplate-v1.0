from fastapi import Depends, HTTPException, status, Request, Header, Response
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError, ExpiredSignatureError
from datetime import datetime, timedelta, timezone
from passlib.context import CryptContext
from tortoise.exceptions import DoesNotExist
from app.config import settings

from applications.user.models import User

# =========================
# JWT SETTINGS
# =========================
SECRET_KEY = "viB2ysUJ7a91SRDPZIHWtjIUlpH-m0Ye0dnrtzsoO1M"
REFRESH_SECRET_KEY = "IeesoMBlYQjADtCqclUXr58la1ZvlRkqnfcWUNTAn4Q"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = settings.ACCESS_TOKEN_EXPIRE_MINUTES
REFRESH_TOKEN_EXPIRE_DAYS = settings.REFRESH_TOKEN_EXPIRE_DAYS

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login_auth2/", auto_error=False)

ACCESS_COOKIE_NAME = "access_token"
REFRESH_COOKIE_NAME = "refresh_token"


# =========================
# TOKEN HELPERS
# =========================
def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire, "type": "access"})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def create_refresh_token(data: dict):
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire, "type": "refresh"})
    return jwt.encode(to_encode, REFRESH_SECRET_KEY, algorithm=ALGORITHM)


def set_auth_cookies(response: Response, access_token: str, refresh_token: str) -> None:
    # In production, set secure cookies; in debug, allow HTTP for local development.
    secure = not settings.DEBUG
    response.set_cookie(
        key=ACCESS_COOKIE_NAME,
        value=access_token,
        httponly=True,
        secure=secure,
        samesite="lax",
        max_age=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        path="/",
    )
    response.set_cookie(
        key=REFRESH_COOKIE_NAME,
        value=refresh_token,
        httponly=True,
        secure=secure,
        samesite="lax",
        max_age=REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60,
        path="/",
    )


# =========================
# AUTH HELPERS
# =========================
async def get_current_user(
        request: Request,
        token: str | None = Depends(oauth2_scheme),
        refresh_token: str | None = Header(default=None, alias="refresh-token")
) -> User:
    cookie_access_token = request.cookies.get(ACCESS_COOKIE_NAME)
    if not refresh_token:
        refresh_token = request.cookies.get(REFRESH_COOKIE_NAME)

    # Prefer cookie auth for browser/docs sessions; fallback to Authorization header.
    candidate_tokens: list[str] = []
    if cookie_access_token:
        candidate_tokens.append(cookie_access_token)
    if token and token != cookie_access_token:
        candidate_tokens.append(token)

    if not candidate_tokens:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )

    payload = None
    token_expired = False
    try:
        for candidate_token in candidate_tokens:
            try:
                payload = jwt.decode(candidate_token, SECRET_KEY, algorithms=[ALGORITHM])
                break
            except ExpiredSignatureError:
                token_expired = True
            except JWTError:
                continue

        if payload is None and token_expired:
            if not refresh_token:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Access token expired. Refresh token required.",
                    headers={"WWW-Authenticate": "Bearer"},
                )

            try:
                refresh_payload = jwt.decode(refresh_token, REFRESH_SECRET_KEY, algorithms=[ALGORITHM])

                token_data = {
                    "sub": refresh_payload.get("sub"),
                    "username": refresh_payload.get("username"),
                    "is_active": refresh_payload.get("is_active"),
                    "is_staff": refresh_payload.get("is_staff"),
                    "is_superadmin": refresh_payload.get("is_superadmin"),
                }

                new_access_token = create_access_token(token_data)
                new_refresh_token = create_refresh_token(token_data)

                request.state.new_tokens = {
                    "access_token": new_access_token,
                    "refresh_token": new_refresh_token,
                }

                payload = jwt.decode(new_access_token, SECRET_KEY, algorithms=[ALGORITHM])

            except ExpiredSignatureError:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Refresh token expired. Please log in again.",
                )
            except JWTError:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid refresh token",
                )

        if payload is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid access token",
                headers={"WWW-Authenticate": "Bearer"},
            )

    except HTTPException:
        raise
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid access token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        user = await User.get(id=payload.get("sub"))
    except DoesNotExist:
        raise HTTPException(status_code=401, detail="User not found")

    if not user.is_active:
        raise HTTPException(status_code=403, detail="Inactive user")

    return user
