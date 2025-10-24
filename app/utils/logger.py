import logging
import sys
from pathlib import Path
from logging.handlers import RotatingFileHandler
from app.config import settings

def setup_logging():
    """Configure logging for the application"""
    logs_dir = Path("logs")
    logs_dir.mkdir(exist_ok=True)

    log_level = getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)

    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            RotatingFileHandler(
                logs_dir / "attendance_system.log",
                maxBytes=10 * 1024 * 1024,  # 10MB
                backupCount=5
            )
        ]
    )

    uvicorn_logger = logging.getLogger("uvicorn")
    uvicorn_logger.setLevel(log_level)

    sqlalchemy_logger = logging.getLogger("sqlalchemy.engine")
    if settings.ENVIRONMENT == "development":
        sqlalchemy_logger.setLevel(logging.INFO)
    else:
        sqlalchemy_logger.setLevel(logging.WARNING)

def get_logger(name: str):
    """Get a logger instance"""
    return logging.getLogger(name)