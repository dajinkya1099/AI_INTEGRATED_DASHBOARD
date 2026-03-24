from ast import List

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
    
class Metric(BaseModel):
    key: str
    url: str
    type: str

class Module(BaseModel):
    moduleName: str
    metrics: list[Metric]
    
class Assign(BaseModel):
    username: str
    moduleId: int