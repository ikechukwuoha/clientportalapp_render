from contextlib import asynccontextmanager
import os
from fastapi import FastAPI
from dotenv import load_dotenv
from app.routers.user_routes import router as user_router
from fastapi.middleware.cors import CORSMiddleware
import logging
from logging.handlers import RotatingFileHandler
import uvicorn
from app.config.settings import settings
from app.database.db import engine



# Load environment variables from .env file
load_dotenv()


# Create FastAPI instance
app = FastAPI(title=settings.PROJECT_NAME)

# CORS configuration
origins = [
    "http://localhost:3000",  # Local frontend (e.g., React)
    "https://yourfrontenddomain.com",  # Production frontend URL
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],  # Allow all HTTP methods
    allow_headers=["*"],  # Allow all headers
)

# Get route prefix from environment variables
ROUTE_PREFIX = os.getenv("ROUTE_PREFIX")

# Include Routers
app.include_router(user_router, prefix=ROUTE_PREFIX)


def setup_logging():
    # Setup a file handler for logging
    file_handler = RotatingFileHandler("app.log", maxBytes=1024*1024*10, backupCount=5)
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))

    # Get the SQLAlchemy engine logger and remove its handlers
    sqlalchemy_logger = logging.getLogger('sqlalchemy.engine')
    sqlalchemy_logger.setLevel(logging.INFO)
    sqlalchemy_logger.propagate = False
    sqlalchemy_logger.handlers.clear()
    
    # Add only the file handler to the SQLAlchemy logger
    sqlalchemy_logger.addHandler(file_handler)

    # Root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    root_logger.addHandler(file_handler)

    # Uvicorn logger
    uvicorn_logger = logging.getLogger('uvicorn')
    uvicorn_logger.setLevel(logging.INFO)
    uvicorn_logger.handlers.clear()
    uvicorn_logger.addHandler(file_handler)

setup_logging()


# Log the app starting
logging.info("App started successfully!")

try:
    with engine.connect() as connection:
        logging.info("Database connected successfully!")
except Exception as e:
    logging.error(f"Failed to connect to the database: {e}")
    

if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, log_config=None, reload=True)
