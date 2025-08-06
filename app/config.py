import os
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

load_dotenv()
class Settings(BaseSettings):
    SQLALCHEMY_DATABASE_URI: str = os.getenv(
        "DATABASE_URL",
        "mysql+mysqlconnector://root:135246@localhost:3307/mysql"
    )
    SECRET_KEY: str = os.getenv("SECRET_KEY", "your-secret-key")

settings = Settings()
