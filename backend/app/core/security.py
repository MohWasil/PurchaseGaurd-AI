"""
Security Utilities - JWT, Password Hashing, Encryption
Production-grade security for financial data
"""
from datetime import datetime, timedelta, timezone
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from cryptography.fernet import Fernet
import os
from dotenv import load_dotenv
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

# Local imports - adjust these if your file names differ
from app.core.database import get_db
from app.models.models import User 

load_dotenv()

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
# Added: Defines the token URL for swagger UI and auth
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/v1/auth/login")

# JWT Settings
SECRET_KEY = os.getenv("SECRET_KEY", "fallback-key-change-in-production")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))

# Encryption for sensitive data
ENCRYPTION_KEY = os.getenv("ENCRYPTION_KEY", "default-key-change-in-production")
# Ensure key is proper format for Fernet
if len(ENCRYPTION_KEY) < 32:
    ENCRYPTION_KEY = ENCRYPTION_KEY.ljust(32, '=')[:32]
fernet = Fernet(ENCRYPTION_KEY.encode().ljust(44, b'=')[:44])

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password against hash"""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """Hash password securely"""
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create JWT access token"""
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def decode_access_token(token: str) -> Optional[dict]:
    """Decode and validate JWT token"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None

# Added: Fetches user from DB based on JWT token
async def get_current_user(
    token: str = Depends(oauth2_scheme), 
    db: AsyncSession = Depends(get_db)
) -> User:
    """Dependency to get authenticated user from JWT using User ID"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    payload = decode_access_token(token)
    if payload is None:
        raise credentials_exception
    
    # We stored the ID as a string in auth.py, so we get it from 'sub'
    user_id_str: str = payload.get("sub")
    if user_id_str is None:
        raise credentials_exception
        
    try:
        user_id = int(user_id_str)
        # Search by ID, not email
        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
    except (ValueError, Exception):
        raise credentials_exception
    
    if user is None:
        raise credentials_exception
        
    return user

def encrypt_sensitive_data(data: str) -> str:
    """Encrypt sensitive receipt data"""
    return fernet.encrypt(data.encode()).decode()

def decrypt_sensitive_data(encrypted_data: str) -> str:
    """Decrypt sensitive receipt data"""
    return fernet.decrypt(encrypted_data.encode()).decode()
