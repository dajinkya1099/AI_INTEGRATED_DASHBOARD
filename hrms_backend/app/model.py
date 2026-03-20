from pydantic import BaseModel
class LoginRequest(BaseModel):
    username: str
    password: str
    

class SignupRequest(BaseModel):
    email: str
    username: str
    password: str
    role: str  # ADMIN / USER
    otp: str = None