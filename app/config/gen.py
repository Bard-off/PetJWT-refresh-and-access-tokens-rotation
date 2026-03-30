from .utils import jwt_working
from schemas.schemas import BaseUser, UserID
ACCESS_TYPE = 'access'
REFRESH_TYPE = 'refresh'

def create_jwt(
    token_type: str, token_data: dict
):
    payload = {"type": token_type}
    payload.update(token_data)
    return jwt_working.encode_jwt(payload)

def generate_access(
    data: BaseUser,
    new_load: dict | None = None
):
    if new_load:
        payload = {
            "sub": str(data.user_id),
            "username": data.username,
        }
        payload.update(new_load)
    else:
        payload = {
            "sub": str(data.user_id),
            "username": data.username,
        }
    return create_jwt(ACCESS_TYPE, payload)

def generate_refresh(
    user_id: int
):
    payload = {
        "sub": str(user_id),
    }
    return create_jwt(REFRESH_TYPE, payload)
