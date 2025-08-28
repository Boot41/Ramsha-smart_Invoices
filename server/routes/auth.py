from fastapi import APIRouter, Depends, Request, HTTPException, status
from typing import Dict, Any
from schemas.auth_schemas import (
    UserRegistrationRequest, UserRegistrationResponse, UserLoginRequest, UserLoginResponse,
    ChangePasswordRequest, ForgotPasswordRequest, ResetPasswordRequest, PasswordResetResponse,
    UpdateProfileRequest, UserProfileResponse, EmailVerificationRequest, VerificationResponse
)
from controller.auth_controller import get_auth_controller
from middleware.auth import get_current_user

router = APIRouter(prefix="/auth", tags=["authentication"])

@router.post("/register", response_model=UserRegistrationResponse)
async def register(
    registration: UserRegistrationRequest,
    request: Request
) -> UserRegistrationResponse:
    """Register a new user"""
    auth_controller = get_auth_controller()
    return await auth_controller.register_user(registration, request)

@router.post("/login", response_model=UserLoginResponse)
async def login(
    login_request: UserLoginRequest,
    request: Request
) -> UserLoginResponse:
    """Login user and return access token"""
    auth_controller = get_auth_controller()
    return await auth_controller.login_user(login_request, request)

@router.post("/logout")
async def logout(
    request: Request,
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """Logout current user"""
    auth_controller = get_auth_controller()
    return await auth_controller.logout_user(current_user, request)

@router.post("/change-password")
async def change_password(
    change_request: ChangePasswordRequest,
    request: Request,
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """Change password for authenticated user"""
    auth_controller = get_auth_controller()
    return await auth_controller.change_password(change_request, current_user, request)

@router.post("/forgot-password", response_model=PasswordResetResponse)
async def forgot_password(
    forgot_request: ForgotPasswordRequest,
    request: Request
) -> PasswordResetResponse:
    """Request password reset"""
    auth_controller = get_auth_controller()
    return await auth_controller.forgot_password(forgot_request, request)

@router.post("/reset-password")
async def reset_password(
    reset_request: ResetPasswordRequest,
    request: Request
) -> Dict[str, Any]:
    """Reset password with token"""
    auth_controller = get_auth_controller()
    return await auth_controller.reset_password(reset_request, request)

@router.get("/profile", response_model=UserProfileResponse)
async def get_profile(
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> UserProfileResponse:
    """Get current user profile"""
    auth_controller = get_auth_controller()
    profile = await auth_controller.get_user_profile(current_user)
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User profile not found"
        )
    return profile

@router.put("/profile")
async def update_profile(
    update_request: UpdateProfileRequest,
    request: Request,
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """Update current user profile"""
    auth_controller = get_auth_controller()
    success, message, updated_profile = await auth_controller.update_user_profile(
        update_request, current_user, request
    )
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=message
        )
    
    return {
        "success": True,
        "message": message,
        "profile": updated_profile
    }

@router.post("/verify-email", response_model=VerificationResponse)
async def verify_email(
    verification_request: EmailVerificationRequest
) -> VerificationResponse:
    """Verify email address"""
    auth_controller = get_auth_controller()
    return await auth_controller.verify_email(verification_request)

@router.get("/me")
async def get_current_user_info(
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """Get current authenticated user information"""
    return {
        "user": current_user,
        "authenticated": True,
        "permissions": current_user.get("permissions", {})
    }
