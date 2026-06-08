from fastapi import FastAPI, Response
from fastapi.middleware.cors import CORSMiddleware
from starlette.responses import Response as StarletteResponse
import asyncio

from app.api.routes.status import router as status_router
from app.api.routes.control import router as control_router
from app.api.routes.lastest import router as lastest_router
from app.api.routes.predict import router as predict_router
from app.api.routes.history import router as history_router
from app.api.routes.debug_predict import router as debug_predict_router
from app.api.routes.raw_samples import router as raw_samples_router
from app.api.routes.auth.auth import router as auth_router
from app.api.routes.user import router as user_router
from app.websocket.prediction_ws import router as prediction_ws_router
from app.core.db_init import init_db
from app.core.app_state import app_state
import os

app = FastAPI(title="CSI Backend")


@app.middleware("http")
async def log_api_response(request, call_next):
    response = await call_next(request)

    if not request.url.path.startswith("/api"):
        return response

    body = b""
    async for chunk in response.body_iterator:
        body += chunk

    body_text = body.decode("utf-8", errors="ignore")
    print(
        f"[API RESPONSE] {request.method} {request.url.path} "
        f"status={response.status_code} body={body_text}"
    )

    return StarletteResponse(
        content=body,
        status_code=response.status_code,
        headers=dict(response.headers),
        media_type=response.media_type,
    )

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(status_router, prefix="/api")
app.include_router(control_router, prefix="/api")
app.include_router(lastest_router, prefix="/api")
app.include_router(predict_router, prefix="/api")
app.include_router(history_router, prefix="/api")
app.include_router(auth_router, prefix="/api")
app.include_router(user_router, prefix="/api/auth")
app.include_router(prediction_ws_router, prefix="/api")
app.include_router(raw_samples_router, prefix="/api")
app.include_router(debug_predict_router, prefix="/api")


@app.on_event("startup")
async def on_startup() -> None:
    init_db()
    app_state.event_loop = asyncio.get_running_loop()

@app.get("/")
def root():
    return {"message": "Backend is running"}


@app.get("/favicon.ico", include_in_schema=False)
def favicon() -> Response:
    return Response(status_code=204)