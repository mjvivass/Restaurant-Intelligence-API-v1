from pydantic import BaseModel, EmailStr

# =========================
# PARA REGISTRO
# =========================
class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str


# =========================
# LOGIN  ✅ (necesario para /login)
# =========================
class UserLogin(BaseModel):
    email: EmailStr
    password: str


# =========================
# RESPUESTA DE USUARIO
# =========================
class UserResponse(BaseModel):
    id: int
    username: str
    email: EmailStr

    class Config:
        from_attributes = True  # Correcto para Pydantic V2


# =========================
# TOKEN JWT
# =========================
class Token(BaseModel):
    access_token: str
    token_type: str
