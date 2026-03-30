from pydantic import BaseModel

class TokenInfo(BaseModel):
    access_token: str | None = None
    refresh_token: str | None = None
    type: str = "Bearer"

class TokenIn(BaseModel):
    refresh_token: str

class UserID(BaseModel):
    user_id: int

class BaseUser(UserID):
    username: str
    password: str | None = None

class UserIn(UserID):
    password: str
