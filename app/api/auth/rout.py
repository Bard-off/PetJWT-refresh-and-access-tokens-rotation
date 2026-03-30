from fastapi import (
    APIRouter, HTTPException, status, Depends, Request, Response
)
from fastapi.security import (
    HTTPAuthorizationCredentials, HTTPBearer
)
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Annotated
import json
from jwt.exceptions import ExpiredSignatureError, InvalidSignatureError

from schemas.schemas import BaseUser, UserIn, TokenInfo, TokenIn
from config.config import db_helper
from db import crud, acrud

from config.utils import jwt_working, pwd_working
from models import User
from config.gen import (
    REFRESH_TYPE, ACCESS_TYPE,
    generate_access, generate_refresh
)


http_bearer = HTTPBearer()


def get_redis_client(req: Request):
    client = getattr(req.app.state, "red", None)
    if not client:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Redis клиент не был получен"
        )
    return client

async def validate_user_in_redis(
    req: Request,
    token_data: dict,
    red,
):
    load = {
        "user-id": token_data["sub"],
        "device": req.headers.get("sec-ch-ua-platform"),
        "user-agent": req.headers.get("user-agent")
    }
    state = await acrud.vaildate_user(red, load)
    return state


async def validate(
    req: Request,
    cred: HTTPAuthorizationCredentials = Depends(http_bearer),
    red = Depends(get_redis_client),
):
    token = cred.credentials
    try:
        load = jwt_working.decode_jwt(token)
        if load["type"] == REFRESH_TYPE:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Неверный тип токен"
            )
        state = await validate_user_in_redis(req, load, red)
        if not state:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Залогинтесь"
            )
    except ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Токен истёк"
        )
    except InvalidSignatureError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Неверный токен"
        )


router = APIRouter(prefix="/jwt", tags=["JWT"], dependencies=[Depends(validate)])
router_auth = APIRouter(prefix="/authorize", tags=["AUTH"])



async def validate_user(
    session: Annotated[AsyncSession, Depends(db_helper.get_db_client)],
    data: UserIn
) -> User:
    user = await crud.select_user_by_id(session, data.user_id)
    if user and pwd_working.validate_password(data.password, user.password.encode("utf-8")):
        return user
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Пользователь не был найден"
    )

@router_auth.post("/auth/")
async def auth_user(session: Annotated[AsyncSession, Depends(db_helper.get_db_client)], data: BaseUser):
    hashed = pwd_working.hash_pwd(data.password).decode("utf-8")
    data.password = hashed
    resp = await crud.make_user(session, data)
    return {"state": resp}


@router_auth.post("/login_user/", response_model=TokenInfo, response_model_exclude_none=True)
async def login_user(req: Request, data = Depends(validate_user), red = Depends(get_redis_client)):
    refresh = generate_refresh(data.user_id)
    load = {
        "user-id": data.user_id,
        "device": req.headers.get("sec-ch-ua-platform"),
        "user-agent": req.headers.get("user-agent")
    }
    jti = await acrud.make_session(red, load, refresh)
    load.update(
        jti=jti
    )
    access = generate_access(data, load)
    return TokenInfo(access_token=access, refresh_token=refresh)

@router_auth.post("/refresh/")
async def refresh_token(
    req: Request,
    data: TokenIn,
    session: Annotated[AsyncSession, Depends(db_helper.get_db_client)],
    red = Depends(get_redis_client)
):
    token_load = jwt_working.decode_jwt(data.refresh_token)
    load = {
        "user-id": token_load['sub'],
        "device": req.headers.get("sec-ch-ua-platform"),
        "user-agent": req.headers.get("user-agent")
    }
    state_in_redis = await validate_user_in_redis(req, token_load, red)
    if not state_in_redis:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Залогинтесь"
        )
    try:
        new_rf, jti = await acrud.refresh_token_pair(red, data.refresh_token, token_load, load)
    except acrud.StateException:
        raise HTTPException(
            status_code=status.HTTP_423_LOCKED,
            detail="Токен не валидный"
        )
    access = ""
    if jti:
        load.update(
            jti=jti
        )
        user = await crud.select_user_by_id(session, int(token_load['sub']))
        if user:
            user_data = BaseUser(user_id=int(token_load['sub']), username=user.username)
            access = generate_access(user_data, load)
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Не удалось достать username из redis по jti"
            )
    return TokenInfo(access_token=access, refresh_token=new_rf)

@router.get("/sessions")
async def get_sessions(
    req: Request,
    red = Depends(get_redis_client)
):
    token: str | None = req.headers.get("Authorization")
    token = token.split(" ")[1]
    load = jwt_working.decode_jwt(token)
    sessions = await acrud.select_all_sessions(red, load["sub"])
    for session in sessions:
        if session["device"] == req.headers.get("sec-ch-ua-platform") and session["user-agent"] == req.headers.get("user-agent"):
            session.update(
                current=True
            )
    return {
        "sessions": sessions
    }


@router.delete("/session/{id}")
async def get_sessions(
    id: int,
    req: Request,
    red = Depends(get_redis_client),
):

    token: str | None = req.headers.get("Authorization")
    token = token.split(" ")[1]
    load = jwt_working.decode_jwt(token)
    state = await acrud.del_session_by_id(red, load['sub'], id)
    return {
        "done": state
    }
