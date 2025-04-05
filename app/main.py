import os
import logging
import importlib
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from logging.handlers import RotatingFileHandler
import uvicorn
from app.api.config.settings import settings
from app.api.database.db import async_engine
from app.api.database.init_db import init_db
from starlette.middleware.sessions import SessionMiddleware

# Load environment variables
load_dotenv()

# Create FastAPI instance
app = FastAPI(title=settings.PROJECT_NAME)

# CORS configuration
origins = [
    'localhost:3000',
    'http://localhost:3000',
    'portal.purpledove.net',
    'https://portal.purpledove.net'
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Session middleware
app.add_middleware(SessionMiddleware, secret_key=os.getenv("SESSION_SECRET_KEY"))

# Logging setup
def setup_logging():
    file_handler = RotatingFileHandler("app.log", maxBytes=1024*1024*10, backupCount=5)
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))

    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))

    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)

    # Uvicorn logger
    uvicorn_logger = logging.getLogger('uvicorn')
    uvicorn_logger.handlers.clear()
    uvicorn_logger.addHandler(file_handler)
    uvicorn_logger.addHandler(console_handler)

setup_logging()

# Include routers dynamically
router_folder = os.path.join(os.path.dirname(__file__), "api", "v1", "endpoints")
def include_routers(app: FastAPI):
    for module_name in os.listdir(router_folder):
        if module_name.endswith(".py") and module_name != "__init__.py":
            module_path = f"app.api.v1.endpoints.{module_name[:-3]}"
            module = importlib.import_module(module_path)
            if hasattr(module, "router"):
                router = getattr(module, "router")
                app.include_router(router, prefix=settings.ROUTE_PREFIX)

include_routers(app)

# Log app startup
logging.info("App started successfully!")

# Test database connection during startup
@app.on_event("startup")
async def on_startup():
    await init_db()
    logging.info("Database initialized with default roles and permissions.")

    # Test the database connection
    try:
        async with async_engine.connect() as connection:
            logging.info("Database connection successful!")
    except Exception as e:
        logging.error(f"Failed to connect to the database: {e}")

@app.get("/")
async def home():
    return {'message': "Welcome"}

# Run the app
if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, log_config=None, reload=True)
