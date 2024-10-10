from contextlib import asynccontextmanager
import os
from fastapi import FastAPI
from dotenv import load_dotenv
from app.routers import user_routes, email_routes
from fastapi.middleware.cors import CORSMiddleware
import logging
import importlib
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



# # Include Routers
# app.include_router(user_routes.router, prefix=ROUTE_PREFIX)
# app.include_router(email_routes.router, prefix=ROUTE_PREFIX)
# Load all routers from the router folder
# Get the router folder path
router_folder = os.path.join(os.path.dirname(__file__), "routers")

def include_routers(app: FastAPI):
    # Iterate through the router folder modules
    for module_name in os.listdir(router_folder):
        if module_name.endswith(".py") and module_name != "__init__.py":
            # Import the router module
            module_path = f"app.routers.{module_name[:-3]}"  # Remove .py extension
            module = importlib.import_module(module_path)

            # Check for 'router' attribute in the module
            if hasattr(module, "router"):
                router = getattr(module, "router")
                # Include the router with a prefix if necessary
                app.include_router(router, prefix=settings.ROUTE_PREFIX)

include_routers(app)









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
