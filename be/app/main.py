from fastapi import FastAPI, Response
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes.status import router as status_router
from app.api.routes.control import router as control_router
from app.api.routes.lastest import router as lastest_router
from app.api.routes.predict import router as predict_router
from app.api.routes.history import router as history_router
from app.api.routes.auth.auth import router as auth_router
from app.api.routes.user import router as user_router
from app.core.db_init import init_db

app = FastAPI(title="CSI Backend")

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


@app.on_event("startup")
def on_startup() -> None:
    init_db()

@app.get("/")
def root():
    return {"message": "Backend is running"}


@app.get("/favicon.ico", include_in_schema=False)
def favicon() -> Response:
    return Response(status_code=204)