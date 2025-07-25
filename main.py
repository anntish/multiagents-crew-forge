from contextlib import asynccontextmanager

from fastapi import FastAPI
from hivetrace import SyncHivetraceSDK

from src.config import HIVETRACE_ACCESS_TOKEN, HIVETRACE_URL
from src.routers.topic_router import router


@asynccontextmanager
async def lifespan(app: FastAPI):
    hivetrace = SyncHivetraceSDK(
        config={
            "HIVETRACE_URL": HIVETRACE_URL,
            "HIVETRACE_ACCESS_TOKEN": HIVETRACE_ACCESS_TOKEN,
        }
    )
    app.state.hivetrace = hivetrace
    try:
        yield
    finally:
        hivetrace.close()


app = FastAPI(lifespan=lifespan)
app.include_router(router)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8004, reload=True)
