import logging

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_admin_user, get_current_user
from app.core.config import settings
from app.core.database import get_db
from app.core.limiter import limiter
from app.core.logic import fill_default_assessments
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)
from app.models import Employee
from app.schemas import (
    LoginRequest,
    RegisterRequest,
    TokenResponse,
    UserOut,
)

logger = logging.getLogger(__name__)

REFRESH_COOKIE_KEY = "refresh_token"

router = APIRouter(prefix="/auth", tags=["auth"])


def _set_refresh_cookie(response: Response, token: str) -> None:
    response.set_cookie(
        key=REFRESH_COOKIE_KEY,
        value=token,
        httponly=True,
        secure=settings.secure_cookie,
        samesite="lax",
        max_age=settings.refresh_token_expire_days * 86400,
        path="/api/v1/auth",
    )


def _clear_refresh_cookie(response: Response) -> None:
    response.delete_cookie(
        key=REFRESH_COOKIE_KEY,
        path="/api/v1/auth",
        httponly=True,
        samesite="lax",
    )


@router.post("/login", response_model=TokenResponse)
@limiter.limit("10/minute")
async def login(
    request: Request,
    body: LoginRequest,
    response: Response,
    db: AsyncSession = Depends(get_db),
):
    """Authenticate user and return JWT tokens."""
    result = await db.execute(select(Employee).where(Employee.email == body.email))
    user = result.scalar_one_or_none()

    if user is None or not verify_password(body.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password"
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Account is inactive"
        )

    token_data = {"sub": str(user.id)}
    refresh_token = create_refresh_token(token_data, user.token_version)
    _set_refresh_cookie(response, refresh_token)
    logger.info("User %s logged in", user.email)
    return TokenResponse(
        access_token=create_access_token(token_data, user.token_version),
        user=UserOut.model_validate(user),
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh(
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db),
):
    """Refresh an expired access token using refresh_token cookie."""
    raw_token = request.cookies.get(REFRESH_COOKIE_KEY)
    if not raw_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token cookie missing",
        )

    payload = decode_token(raw_token)
    if payload is None or payload.get("type") != "refresh":
        _clear_refresh_cookie(response)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token"
        )

    user_id = payload.get("sub")
    result = await db.execute(select(Employee).where(Employee.id == user_id))
    user = result.scalar_one_or_none()

    if user is None or not user.is_active:
        _clear_refresh_cookie(response)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive",
        )

    if payload.get("ver", 0) != user.token_version:
        _clear_refresh_cookie(response)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has been revoked",
        )

    token_data = {"sub": str(user.id)}
    new_refresh = create_refresh_token(token_data, user.token_version)
    _set_refresh_cookie(response, new_refresh)
    return TokenResponse(
        access_token=create_access_token(token_data, user.token_version),
        user=UserOut.model_validate(user),
    )


@router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
async def register(
    body: RegisterRequest,
    db: AsyncSession = Depends(get_db),
    admin: Employee = Depends(get_admin_user),
):
    """Register a new user (admin only)."""
    result = await db.execute(select(Employee).where(Employee.email == body.email))
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Email already registered"
        )

    user = Employee(
        email=body.email,
        password_hash=hash_password(body.password),
        full_name=body.full_name,
        role=body.role,
        grade=body.grade,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    if user.grade:
        await fill_default_assessments(db, user.id, user.grade)
    logger.info("Admin %s registered user %s", admin.email, user.email)
    return UserOut.model_validate(user)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    response: Response,
    db: AsyncSession = Depends(get_db),
    current_user: Employee = Depends(get_current_user),
):
    """Revoke all tokens for the current user by bumping token_version."""
    current_user.token_version += 1
    await db.commit()
    _clear_refresh_cookie(response)
    logger.info(
        "User %s logged out (token_version=%d)",
        current_user.email,
        current_user.token_version,
    )


@router.get("/me", response_model=UserOut)
async def get_me(current_user: Employee = Depends(get_current_user)):
    """Return the currently authenticated user's profile."""
    return UserOut.model_validate(current_user)
