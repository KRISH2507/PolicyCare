from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.user import User
from app.schemas.auth import LoginRequest, SignupRequest, GoogleAuthRequest, LoginResponse
from app.core.security import verify_password, get_password_hash, create_access_token, decode_access_token
from app.core.config import settings

router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


@router.post("/login", response_model=LoginResponse)
def login(request: LoginRequest, db: Session = Depends(get_db)):
    if request.email == settings.ADMIN_EMAIL:
        if request.password != settings.ADMIN_PASSWORD:
            raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Incorrect email or password",
                                headers={"WWW-Authenticate": "Bearer"})
        token = create_access_token({"sub": settings.ADMIN_EMAIL, "role": "admin"})
        return LoginResponse(access_token=token, role="admin",
                             email=settings.ADMIN_EMAIL, full_name="Admin")

    db_user = db.query(User).filter(User.email == request.email).first()
    if not db_user:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED,
                            "No account found with this email. Please sign up first.",
                            headers={"WWW-Authenticate": "Bearer"})

    if db_user.is_google_user and not db_user.hashed_password:
        raise HTTPException(status.HTTP_400_BAD_REQUEST,
                            "This account uses Google Sign-In. Please use the Google button.")

    if not verify_password(request.password, db_user.hashed_password):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Incorrect email or password",
                            headers={"WWW-Authenticate": "Bearer"})

    token = create_access_token({"sub": db_user.email, "role": db_user.role})
    return LoginResponse(access_token=token, role=db_user.role,
                         email=db_user.email, full_name=db_user.full_name)


@router.post("/signup", response_model=LoginResponse, status_code=status.HTTP_201_CREATED)
def signup(request: SignupRequest, db: Session = Depends(get_db)):
    if request.email == settings.ADMIN_EMAIL:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "This email is reserved.")

    if db.query(User).filter(User.email == request.email).first():
        raise HTTPException(status.HTTP_409_CONFLICT,
                            "An account with this email already exists. Please sign in.")

    user = User(
        email=request.email,
        hashed_password=get_password_hash(request.password),
        full_name=request.full_name.strip(),
        role="user",
        is_google_user=False,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    token = create_access_token({"sub": user.email, "role": user.role})
    return LoginResponse(access_token=token, role=user.role,
                         email=user.email, full_name=user.full_name)


@router.post("/google", response_model=LoginResponse)
def google_signin(request: GoogleAuthRequest, db: Session = Depends(get_db)):
    if not settings.GOOGLE_CLIENT_ID:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE,
                            "Google Sign-In is not configured.")

    try:
        from google.oauth2 import id_token as google_id_token
        from google.auth.transport import requests as google_requests
        id_info = google_id_token.verify_oauth2_token(
            request.id_token, google_requests.Request(), settings.GOOGLE_CLIENT_ID)
    except ValueError as e:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, f"Invalid Google token: {e}")

    google_sub = id_info.get("sub")
    email = id_info.get("email", "")
    full_name = id_info.get("name", "")

    if not google_sub or not email:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Google token missing required fields.")

    db_user = db.query(User).filter(User.email == email).first()
    if db_user:
        if not db_user.google_id:
            db_user.google_id = google_sub
            db_user.is_google_user = True
            db.commit()
            db.refresh(db_user)
    else:
        db_user = User(email=email, full_name=full_name, google_id=google_sub,
                       role="user", is_google_user=True, hashed_password=None)
        db.add(db_user)
        db.commit()
        db.refresh(db_user)

    token = create_access_token({"sub": db_user.email, "role": db_user.role})
    return LoginResponse(access_token=token, role=db_user.role,
                         email=db_user.email, full_name=db_user.full_name)


def get_current_user(token: str = Depends(oauth2_scheme)):
    payload = decode_access_token(token)
    email = payload.get("sub")
    role = payload.get("role")
    if not email or not role:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Could not validate credentials",
                            headers={"WWW-Authenticate": "Bearer"})
    return {"email": email, "role": role}


def require_admin(current_user: dict = Depends(get_current_user)):
    if current_user.get("role") != "admin":
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Admin access required.")
    return current_user
