import jwt
import bcrypt as bc
from .config import settings
from datetime import datetime, timedelta

class InvalidType(Exception):
    pass

class JwtWorking:
    def __init__(self) -> None:
        self.__REFRESH_TYPE = "refresh"
        self.__ACCESS_TYPE = "access"
    def encode_jwt(
        self,
        payload: dict,
        private_key: str = settings.jwt.private_key_path.read_text(),
        algorithm: str = settings.jwt.algorithm,
        expire_on_minutes: int = 15,
        expire_on_days: int = 30,
    ) -> str:
        now = datetime.utcnow()
        expire = 0
        if payload["type"] == self.__REFRESH_TYPE:
            expire = now + timedelta(days=expire_on_days)
        else:
            expire = now + timedelta(minutes=expire_on_minutes)
        payload.update(
            iat=now,
            exp=expire
        )
        encoded = jwt.encode(
            payload, private_key, algorithm=algorithm
        )
        return encoded
    def decode_jwt(
        self,
        token: str,
        public_key: str = settings.jwt.public_key_path.read_text(),
        algorithm: str = settings.jwt.algorithm,
    ) -> dict:
        return jwt.decode(token, public_key, algorithms=[algorithm])


class PwdWorking:
    def __init__(self) -> None:
        pass

    def hash_pwd(
        self,
        password: str
    ) -> bytes:
        salt = bc.gensalt()
        pwd_bytes = password.encode()
        return bc.hashpw(pwd_bytes, salt=salt)


    def validate_password(
        self,
        password: str,
        hashed_password: bytes
    ):
        return bc.checkpw(password.encode(), hashed_password)



jwt_working = JwtWorking()
pwd_working = PwdWorking()

