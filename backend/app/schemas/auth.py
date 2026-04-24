from pydantic import BaseModel, Field, field_validator


class LoginRequest(BaseModel):
    username: str = Field(..., min_length=1, max_length=100)
    password: str = Field(..., min_length=1, max_length=200)

    @field_validator("username", "password")
    @classmethod
    def not_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Field cannot be blank")
        return v


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: str
    username: str
