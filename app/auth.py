import os
from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from app.models.schemas import LoginRequest, TokenResponse

SECRET_KEY = os.getenv("JWT_SECRET_KEY", "brightcone_super_secret_key_2026_secure")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24 hours

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/token", auto_error=False)

router = APIRouter()

# Default demo/operator credentials
ADMIN_EMAIL = os.getenv("ADMIN_EMAIL", "admin@brightcone.ai")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "brightcone_agentic_2026")

def verify_credentials(email_or_user: str, password: str) -> bool:
    """Validate enterprise credentials against configured admin or demo credentials."""
    return (
        (email_or_user.lower() == ADMIN_EMAIL.lower() or email_or_user == "brightcone_admin_user")
        and password == ADMIN_PASSWORD
    )

def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    """Sign and create JWT access token."""
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest):
    """Authenticate enterprise operator and return JWT access token."""
    if not verify_credentials(payload.email.strip(), payload.password.strip()):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials. Please verify your enterprise email and access key."
        )
    token = create_access_token({
        "sub": payload.email.strip(),
        "role": "Enterprise Operator",
        "tier": "Level-3 Autonomous Commander"
    })
    return TokenResponse(
        access_token=token,
        token_type="bearer",
        role="Enterprise Operator",
        email=payload.email.strip()
    )

@router.post("/token", response_model=TokenResponse)
def token_endpoint(form_data: OAuth2PasswordRequestForm = Depends()):
    """OAuth2 password form endpoint for API token issuance."""
    if not verify_credentials(form_data.username.strip(), form_data.password.strip()):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    token = create_access_token({
        "sub": form_data.username.strip(),
        "role": "Enterprise Operator"
    })
    return TokenResponse(
        access_token=token,
        token_type="bearer",
        role="Enterprise Operator",
        email=form_data.username.strip()
    )

def get_current_user(token: str | None = Depends(oauth2_scheme)) -> str | None:
    """Extract authenticated identity from Bearer token."""
    if not token:
        return None
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        return username
    except JWTError:
        return None