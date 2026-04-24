from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.user import User
from app.schemas.auth import LoginRequest, LoginResponse
from app.core.security import verify_password, get_password_hash, create_access_token, decode_access_token
from app.core.config import settings

router = APIRouter()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")

@router.post("/login", response_model=LoginResponse)
def login(request: LoginRequest, db: Session = Depends(get_db)):
    
    db_user = db.query(User).filter(User.username == request.username).first()
    
    if db_user:
        if not verify_password(request.password, db_user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        role = db_user.role
        username = db_user.username
    else:
        if request.username == settings.ADMIN_USERNAME:
            if request.password == settings.ADMIN_PASSWORD:
                role = "admin"
                username = settings.ADMIN_USERNAME
            else:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Incorrect username or password",
                    headers={"WWW-Authenticate": "Bearer"},
                )
        else:
            # Auto-register new normal users since there is no signup page setup.
            new_user = User(
                username=request.username,
                hashed_password=get_password_hash(request.password),
                role="user"
            )
            db.add(new_user)
            db.commit()
            db.refresh(new_user)
            role = new_user.role
            username = new_user.username

    token_data = {"sub": username, "role": role}
    access_token = create_access_token(data=token_data)
    
    return LoginResponse(
        access_token=access_token,
        role=role,
        username=username
    )

def get_current_user(token: str = Depends(oauth2_scheme)):
    payload = decode_access_token(token)
    username: str = payload.get("sub")
    role: str = payload.get("role")
    
    if username is None or role is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return {"username": username, "role": role}

def require_admin(current_user: dict = Depends(get_current_user)):
    if current_user.get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions. Admin access required."
        )
    return current_user
