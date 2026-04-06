from typing import Optional
from pydantic_settings import BaseSettings
from tortoise import Tortoise
from app.utils.auto_routing import get_single_app_structure


class Settings(BaseSettings):
    DEBUG: bool = True
    APP_NAME: str = "shippros App"

    EMAIL_HOST: str = "smtp.gmail.com"
    EMAIL_PORT: int = 587
    EMAIL_HOST_USER: str = "moynul.officials@gmail.com"
    EMAIL_HOST_PASSWORD: str = ""
    DEFAULT_FROM_EMAIL: str = "moynul.officials@gmail.com"

    MEDIA_DIR: str = "media/"
    MEDIA_ROOT: str = "media/"
    ENV: str = "development"

    DB_HOST: str = "localhost"
    DB_NAME: str = "db.sqlite3"
    DB_USER: str = ""
    DB_PASSWORD: str = ""
    DB_PORT: int = 5432
    DB_ENGINE: str = "postgres"

    DATABASE_URL: Optional[str] = None
    SECRET_KEY: Optional[str] = None
    BASE_URL: str = "http://localhost:8000/"
    FRONTEND_URL: str = "http://localhost:3000/"
    RADIS_URL: str = "redis://redis:6379/0"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 10
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30
    STRIPE_SECRET_KEY: str = ""
    STRIPE_PUBLISHABLE_KEY: str = ""
    STRIPE_WEBHOOK_SECRET: str = ""
    STRIPE_ENDPOINT_SECRET: str = ""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        engine = self.DB_ENGINE.lower()
        if engine == "sqlite":
            self.DATABASE_URL = f"sqlite:///{self.DB_NAME}"
        elif engine in ("mariadb", "mysql"):
            self.DATABASE_URL = f"mysql://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
        elif engine == "postgres":
            self.DATABASE_URL = f"postgres://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
        else:
            raise ValueError(f"Unsupported DB_ENGINE: {self.DB_ENGINE}")


    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()

apps_config = get_single_app_structure("applications")
import json

print(json.dumps(apps_config, indent=4))

TORTOISE_ORM = {
    "connections": {
        "default": settings.DATABASE_URL,
    },
    "apps": get_single_app_structure("applications"),
    "use_tz": True,
    "timezone": "Asia/Dhaka",
}


async def init_db():
    await Tortoise.init(config=TORTOISE_ORM)
    # if settings.ENV != "production":
    #     await Tortoise.generate_schemas()
    # else:
    #     print("Skipping schema generation in production.")
