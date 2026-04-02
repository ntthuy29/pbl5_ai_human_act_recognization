from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes.status import router as status_router
from app.api.routes.control import router as control_router
from app.api.routes.lastest import router as lastest_router

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

@app.get("/")
def root():
    return {"message": "Backend is running"}