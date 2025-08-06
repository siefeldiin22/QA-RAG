from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from app.routes.routes_auth import router as auth_router
from app.routes.routes_ask import router as ask_router
from app.routes.routes_upload import router as upload_router
from app.routes.sessions import router as sessions_router

from app.database.session import engine
from app.database.base import Base
import uvicorn


# Optional for development
def init_db():
    Base.metadata.create_all(bind=engine)

app = FastAPI()

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Limit this in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

init_db()

app.include_router(auth_router)
app.include_router(ask_router)
app.include_router(upload_router)
app.include_router(sessions_router)
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/signup")
def get_signup():
    return FileResponse("static/signup.html")

@app.get("/upload")
def get_upload():
    return FileResponse("static/upload.html")
@app.get("/login")
def get_login():
    return FileResponse("static/login.html")

@app.get("/dashboard")
def get_dashboard():
    return FileResponse("static/dashboard.html")

@app.get("/ask")
def get_ask():
    return FileResponse("static/ask.html")

@app.get("/session_review")
def session_review():
    return FileResponse("static/session_review.html")

@app.get("/")
def root():
    return FileResponse("static/landing_page.html")


if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
