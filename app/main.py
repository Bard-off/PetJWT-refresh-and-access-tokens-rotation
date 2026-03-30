from fastapi import (
    FastAPI, Request
)
from fastapi.middleware.cors import CORSMiddleware
import logging


from config.config import settings, lifespan
from api.auth.rout import router as ro
from api.auth.rout import router_auth as roa

logging.basicConfig(level=logging.INFO)
log = logging.getLogger()

app = FastAPI(lifespan=lifespan)


@app.middleware("http")
async def middle(req: Request, call_next):
    log.info(req.headers)
    response = await call_next(req)
    return response

app.include_router(ro)
app.include_router(roa)
app.add_middleware(
    CORSMiddleware,
    allow_credentials = settings.server.allow_credentials,
    allow_origins = settings.server.allow_origins,
    allow_methods = settings.server.allow_methods,
    allow_headers = settings.server.allow_headers,
)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host=settings.server.host, port=settings.server.port, reload=settings.server.reload)
