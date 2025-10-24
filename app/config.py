from decouple import config
from typing import List

class Settings:
    DATABASE_URL: str = config("DATABASE_URL", default="postgresql://user:password@localhost:5432/attendance_db")
    REDIS_URL: str = config("REDIS_URL", default="redis://localhost:6379/0")
    SECRET_KEY: str = config("SECRET_KEY", default="your-secret-key-change-in-production")
    ALGORITHM: str = config("ALGORITHM", default="HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = config("ACCESS_TOKEN_EXPIRE_MINUTES", default=30, cast=int)

    SMTP_HOST: str = config("SMTP_HOST", default="smtp.gmail.com")
    SMTP_PORT: int = config("SMTP_PORT", default=587, cast=int)
    SMTP_USERNAME: str = config("SMTP_USERNAME", default="")
    SMTP_PASSWORD: str = config("SMTP_PASSWORD", default="")
    FROM_EMAIL: str = config("FROM_EMAIL", default="")

    CAMERA_URLS: str = config("CAMERA_URLS", default="http://localhost:8080/video")
    FACE_RECOGNITION_TOLERANCE: float = config("FACE_RECOGNITION_TOLERANCE", default=0.6, cast=float)
    FACE_DETECTION_MODEL: str = config("FACE_DETECTION_MODEL", default="hog")

    ADMIN_EMAIL: str = config("ADMIN_EMAIL", default="admin@company.com")
    MANAGER_EMAIL: str = config("MANAGER_EMAIL", default="manager@company.com")

    LOG_LEVEL: str = config("LOG_LEVEL", default="INFO")
    ENVIRONMENT: str = config("ENVIRONMENT", default="development")

    @property
    def camera_url_list(self) -> List[str]:
        return [url.strip() for url in self.CAMERA_URLS.split(',')]

settings = Settings()