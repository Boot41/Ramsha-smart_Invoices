from fastapi import HTTPException, Depends, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional, Dict, Any
import jwt
import os
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

# JWT Configuration
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-super-secret-key")
JWT_ALGORITHM = "HS256"
JWT_ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", "30"))

security = HTTPBearer()


class AuthMiddleware:
    """Authentication middleware for handling JWT tokens"""
    
    @staticmethod
    def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
        """Create JWT access token"""
        to_encode = data.copy()
        
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
        
        to_encode.update({"exp": expire, "iat": datetime.utcnow()})
        
        try:
            encoded_jwt = jwt.encode(to_encode, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
            logger.info(f"✅ Access token created for user: {data.get('email', 'unknown')}")
            return encoded_jwt
        except Exception as e:
            logger.error(f"❌ Error creating access token: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Could not create access token"
            )
    
    @staticmethod
    def verify_token(token: str) -> Dict[str, Any]:
        """Verify JWT token and return payload"""
        try:
            payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
            
            # Check if token is expired
            exp = payload.get("exp")
            if exp and datetime.utcnow() > datetime.fromtimestamp(exp):
                logger.warning("⚠️ Token has expired")
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Token has expired",
                    headers={"WWW-Authenticate": "Bearer"},
                )
            
            logger.info(f"✅ Token verified for user: {payload.get('email', 'unknown')}")
            return payload
            
        except jwt.InvalidTokenError as e:
            logger.error(f"❌ Invalid token: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token",
                headers={"WWW-Authenticate": "Bearer"},
            )
        except Exception as e:
            logger.error(f"❌ Token verification error: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )


async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Dict[str, Any]:
    """
    Get current authenticated user from JWT token
    
    Returns:
        Dict containing user information from JWT payload
    """
    try:
        token = credentials.credentials
        payload = AuthMiddleware.verify_token(token)
        
        # Extract user information from payload
        user_info = {
            "email": payload.get("email"),
            "role": payload.get("role"),
            "user_id": payload.get("user_id"),
            "name": payload.get("name"),
            "exp": payload.get("exp"),
            "iat": payload.get("iat")
        }
        
        # Validate required fields
        if not user_info.get("email"):
            logger.error("❌ Token missing required email field")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token: missing email",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        logger.info(f"🔐 Authenticated user: {user_info['email']} ({user_info.get('role', 'unknown')})")
        return user_info
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Authentication error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication failed",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_optional_user(request: Request) -> Optional[Dict[str, Any]]:
    """
    Get current user if authenticated, otherwise return None
    Used for endpoints that can work with or without authentication
    """
    try:
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            return None
        
        token = auth_header.split(" ")[1]
        payload = AuthMiddleware.verify_token(token)
        
        return {
            "email": payload.get("email"),
            "role": payload.get("role"),
            "user_id": payload.get("user_id"),
            "name": payload.get("name")
        }
    except:
        return None


def require_auth(current_user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
    """
    Dependency that requires authentication
    Use this as a dependency in routes that need authentication
    """
    return current_user


def require_role(required_role: str):
    """
    Dependency factory that requires specific role
    
    Args:
        required_role: Required user role
    
    Returns:
        Dependency function that checks user role
    """
    def role_checker(current_user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
        user_role = current_user.get("role", "").lower()
        
        if user_role != required_role.lower():
            logger.warning(f"⚠️ Access denied: User {current_user.get('email')} has role '{user_role}', required '{required_role}'")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions. Required role: {required_role}"
            )
        
        logger.info(f"✅ Role check passed: {user_role} for user {current_user.get('email')}")
        return current_user
    
    return role_checker


def require_tenant_role(current_user: Dict[str, Any] = Depends(require_role("tenant"))) -> Dict[str, Any]:
    """Dependency that requires TENANT role"""
    return current_user


def require_rent_payer_role(current_user: Dict[str, Any] = Depends(require_role("rent_payer"))) -> Dict[str, Any]:
    """Dependency that requires RENT_PAYER role"""
    return current_user


class TokenHelper:
    """Helper class for token operations"""
    
    @staticmethod
    def create_user_token(email: str, role: str, user_id: Optional[str] = None, name: Optional[str] = None) -> str:
        """Create a JWT token for user authentication"""
        token_data = {
            "email": email,
            "role": role,
            "user_id": user_id,
            "name": name,
            "token_type": "access"
        }
        
        return AuthMiddleware.create_access_token(token_data)
    
    @staticmethod
    def extract_user_email(token: str) -> Optional[str]:
        """Extract user email from token without full validation (for logging)"""
        try:
            # Decode without verification for logging purposes only
            payload = jwt.decode(token, options={"verify_signature": False})
            return payload.get("email")
        except:
            return None