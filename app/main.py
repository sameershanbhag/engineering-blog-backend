from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import settings
from .database import init_db
from .routers import auth, content, interactions
from .seed import seed


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    if settings.seed_on_startup:
        seed()
    yield


app = FastAPI(title="The Engineering Commons API", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(content.router, tags=["content"])
app.include_router(auth.router)
app.include_router(interactions.router, tags=["interactions"])


@app.get("/health", tags=["meta"])
def health():
    return {"status": "ok"}
