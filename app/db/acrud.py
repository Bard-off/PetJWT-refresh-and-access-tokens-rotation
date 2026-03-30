import json
import uuid
import logging
from redis.asyncio import Redis
from config.gen import generate_refresh, generate_access
from schemas.schemas import BaseUser
logging.basicConfig(level=logging.INFO)
log = logging.getLogger()

def token_id_generator():
    return uuid.uuid4()

class StateException(Exception): pass

async def get_all(redis_client):
    keys = []
    cursor = 0
    while True:
        cursor, batch = await redis_client.scan(cursor, match='*', count=100)
        keys.extend(batch)
        if cursor == 0:
            break
    return keys

async def delete_all_data(redis_client):
    await redis_client.flushdb()

async def make_session(redis_client, load: dict, new_refresh_token: str):
    sessions = await redis_client.hget(f"user:{load['user-id']}", "sessions")
    black = await redis_client.smembers("black")
    byte_white_list = await redis_client.lrange("white", 0, -1)
    white_list = []
    if sessions:
        for lst in byte_white_list: white_list.append(json.loads(lst.decode("utf-8")))
        sessions = json.loads(sessions.decode("utf-8"))
        print(sessions)
        print(white_list)
        print(black)
    else:
        sessions = []
        white_list = []
    if not sessions:
        new_id = str(token_id_generator())
        to_white_list = {
            "refresh_token_id": new_id,
            "token": new_refresh_token
        }
        load.update(
            refresh_token_id=new_id,
            id=len(sessions)
        )
        sessions.append(load)
        await redis_client.hset(f"user:{load['user-id']}", "sessions", json.dumps(sessions))
        await redis_client.rpush(f"white", json.dumps(to_white_list))
        return to_white_list["refresh_token_id"]
    for session in sessions:
        if session["device"] == load["device"] and session["user-agent"] == load["user-agent"]:
            for lst in white_list:
                if lst["refresh_token_id"] == session["refresh_token_id"]:
                    await redis_client.sadd("black", lst["token"])
                    log.info(f"Токен занесён в чёрный список")
                    idx = white_list.index(lst)
                    lst["token"] = new_refresh_token
                    await redis_client.lset("white", idx, json.dumps(lst))
                    log.info(f"Новый токен установлен")
                    return lst["refresh_token_id"]
    new_id = str(token_id_generator())
    to_white_list = {
        "refresh_token_id": new_id,
        "token": new_refresh_token
    }
    load.update(
        id=len(sessions),
        refresh_token_id=new_id,
    )
    sessions.append(load)
    await redis_client.hset(f"user:{load['user-id']}", "sessions", json.dumps(sessions))
    log.info(f"Функция добавления новой сессии успешно сработала")
    await redis_client.rpush(f"white", json.dumps(to_white_list))
    log.info(f"Функция добавления нового токена успешно сработала")
    return to_white_list["refresh_token_id"]

async def refresh_token_pair(redis_client, refresh_token: str, token_load: dict, load: dict):
    is_blocked = await redis_client.sismember("black", refresh_token)
    if is_blocked:
        await redis_client.hset(f"user:{token_load['sub']}", "sessions", json.dumps([]))
        raise StateException
    new_refresh: str = generate_refresh(token_load['sub'])
    jti = await make_session(redis_client, load, new_refresh)
    return new_refresh, jti

async def get_userame_by_jti(redis_client, jti: str, user_id: int):
    sessions = await redis_client.hget(f"user:{user_id}", "sessions")
    sessions = json.loads(sessions.decode("utf-8"))
    for session in sessions:
        if session["refresh_token_id"] == jti:
            return session["username"]
    return False

async def select_all_sessions(redis_client, user_id):
    sessions = await redis_client.hget(f"user:{user_id}", "sessions")
    decoded_sessions = json.loads(sessions.decode("utf-8"))
    return decoded_sessions

async def del_session_by_id(redis_client, user_id: int | str, id_to_del: int):
    sessions = await redis_client.hget(f"user:{user_id}", "sessions")
    decoded_sessions: list[dict] = json.loads(sessions.decode("utf-8"))
    for session in decoded_sessions:
        if session["id"] == id_to_del:
            decoded_sessions.pop(decoded_sessions.index(session))
            await redis_client.hset(f"user:{user_id}", "sessions", json.dumps(decoded_sessions))
            return True
    return False

async def vaildate_user(
    redis_client,
    load: dict
):
    sessions = await redis_client.hget(f"user:{load['user-id']}", "sessions")
    decoded_sessions = json.loads(sessions.decode("utf-8"))
    for session in decoded_sessions:
        if session["device"] == load['device'] and session["user-agent"] == load["user-agent"]:
            return True
    return False
