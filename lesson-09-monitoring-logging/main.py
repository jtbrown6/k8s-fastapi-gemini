import os
import json
import logging # Import logging module
from fastapi import FastAPI, HTTPException, Header, status, Request # Added Request for logging middleware
from typing import Optional, List
from pydantic import BaseModel
from prometheus_fastapi_instrumentator import Instrumentator # Prometheus instrumentator
from pythonjsonlogger import jsonlogger # Structured logging

# --- Configuration ---
greeting = os.getenv('GREETING_MESSAGE', 'Hello from the Hero Registry!')
log_level_str = os.getenv('LOG_LEVEL', 'INFO').upper() # Read log level, default INFO
api_key_secret = os.getenv('API_KEY', 'no-key-provided')
db_password_secret = os.getenv('DATABASE_PASSWORD', 'no-db-password')

# --- Structured Logging Setup ---
# Use python-json-logger to format logs as JSON for easier parsing by Fluentd/Loki
logHandler = logging.StreamHandler()
formatter = jsonlogger.JsonFormatter('%(asctime)s %(levelname)s %(name)s %(message)s')
logHandler.setFormatter(formatter)

# Get the root logger and add our handler
logger = logging.getLogger() # Could use specific logger name like logging.getLogger("hero_registry")
logger.addHandler(logHandler)
logger.setLevel(log_level_str) # Set level from environment variable

# Prevent duplicate logging if uvicorn also configures root logger
logging.getLogger("uvicorn.access").disabled = True
logging.getLogger("uvicorn.error").disabled = True
logging.getLogger("uvicorn").propagate = False


logger.info("--- Configuration Loading ---", extra={"greeting": greeting, "log_level": log_level_str})
# Avoid logging secrets directly, even masked, in production logs
# logger.info(f"API Key (Secret): {'*' * len(api_key_secret) if api_key_secret != 'no-key-provided' else api_key_secret}")
# logger.info(f"DB Password (Secret): {'*' * len(db_password_secret) if db_password_secret != 'no-db-password' else db_password_secret}")
logger.info("Secrets loaded (values masked).")
logger.info("--------------------------")


# --- Persistent Data Handling ---
DATA_DIR = "/data"
HERO_FILE = os.path.join(DATA_DIR, "heroes.json")
os.makedirs(DATA_DIR, exist_ok=True)
heroes_db = []

def load_heroes_from_file():
    global heroes_db
    try:
        if os.path.exists(HERO_FILE):
            with open(HERO_FILE, 'r') as f:
                heroes_db = json.load(f)
                logger.info(f"Loaded heroes from file.", extra={"count": len(heroes_db), "file": HERO_FILE})
        else:
            heroes_db = [
                {"id": 1, "name": "Iron Man", "secret_identity": "Tony Stark"},
                {"id": 2, "name": "Captain America", "secret_identity": "Steve Rogers"},
                {"id": 3, "name": "Black Widow", "secret_identity": "Natasha Romanoff"},
            ]
            logger.info(f"Hero file not found. Initializing with default data.", extra={"count": len(heroes_db), "file": HERO_FILE})
            save_heroes_to_file()
    except (json.JSONDecodeError, IOError) as e:
        logger.error(f"Error loading heroes from file.", exc_info=True, extra={"file": HERO_FILE, "error": str(e)})
        heroes_db = []

def save_heroes_to_file():
    try:
        with open(HERO_FILE, 'w') as f:
            json.dump(heroes_db, f, indent=2)
            logger.info(f"Saved heroes to file.", extra={"count": len(heroes_db), "file": HERO_FILE})
    except IOError as e:
        logger.error(f"Error saving heroes to file.", exc_info=True, extra={"file": HERO_FILE, "error": str(e)})

# --- Pydantic Models ---
class HeroCreate(BaseModel):
    name: str
    secret_identity: str

class Hero(HeroCreate):
    id: int

# --- FastAPI App ---
app = FastAPI(title="Hero Registry API (Monitored & Logged)", version="0.4.0")

# --- Prometheus Metrics Setup ---
# Exposes /metrics endpoint
# Analogy: Installing monitoring sensors (instrumentator) throughout the HQ (app)
# that report status to the Eye of Agamotto (Prometheus).
instrumentator = Instrumentator().instrument(app)

@app.on_event("startup")
async def startup():
    # Expose basic server metrics
    instrumentator.expose(app)
    # Load initial data
    load_heroes_from_file()
    logger.info("Application startup complete.")

# --- Logging Middleware (Optional but useful) ---
@app.middleware("http")
async def log_requests(request: Request, call_next):
    # Log basic request info before processing
    logger.info("Incoming request", extra={"method": request.method, "url": str(request.url)})
    response = await call_next(request)
    # Log response status code after processing
    logger.info("Request finished", extra={"method": request.method, "url": str(request.url), "status_code": response.status_code})
    return response


# --- API Endpoints ---
@app.get("/")
async def read_root():
    logger.debug("Root endpoint accessed.")
    return {"message": greeting}

@app.get("/heroes", response_model=List[Hero])
async def get_heroes(x_api_key: Optional[str] = Header(None)):
    logger.debug("Get heroes endpoint accessed.")
    if api_key_secret != 'no-key-provided' and x_api_key != api_key_secret:
         logger.warning(f"Attempted access to /heroes with invalid API key.", extra={"provided_key_masked": x_api_key[:1] + '***' if x_api_key else None})
         # raise HTTPException(status_code=401, detail="Invalid API Key")
         pass
    logger.info(f"Returning hero list.", extra={"count": len(heroes_db)})
    return heroes_db

@app.get("/heroes/{hero_id}", response_model=Hero)
async def get_hero_by_id(hero_id: int):
    logger.debug(f"Get hero by ID endpoint accessed.", extra={"hero_id": hero_id})
    hero = next((h for h in heroes_db if h["id"] == hero_id), None)
    if hero:
        logger.info(f"Found hero by ID.", extra={"hero_id": hero_id, "hero_name": hero.get('name')})
        return hero
    else:
        logger.warning(f"Hero not found by ID.", extra={"hero_id": hero_id})
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Hero not found")

@app.post("/heroes", response_model=Hero, status_code=status.HTTP_201_CREATED)
async def create_hero(hero_data: HeroCreate, x_api_key: Optional[str] = Header(None)):
    logger.debug(f"Create hero endpoint accessed.", extra={"hero_name": hero_data.name})
    if api_key_secret != 'no-key-provided' and x_api_key != api_key_secret:
         logger.warning(f"Attempted POST to /heroes with invalid API key.", extra={"provided_key_masked": x_api_key[:1] + '***' if x_api_key else None})
         # raise HTTPException(status_code=401, detail="Invalid API Key")
         pass

    new_id = max(h["id"] for h in heroes_db) + 1 if heroes_db else 1
    new_hero = Hero(id=new_id, **hero_data.dict())

    heroes_db.append(new_hero.dict())
    save_heroes_to_file() # This function now logs success/failure
    logger.info(f"Added new hero.", extra={"hero_id": new_hero.id, "hero_name": new_hero.name})
    return new_hero

# Main entry point
if __name__ == "__main__":
    import uvicorn
    logger.info("Starting Hero Registry API server directly (Persistent & Monitored)...")
    # Load data immediately if running directly
    # load_heroes_from_file() # Already called by startup event
    # Note: Uvicorn logs might still appear here if run directly, depending on exact setup.
    # The JSON logger setup primarily targets containerized execution where stdout is captured.
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True, log_config=None) # Pass log_config=None to prevent uvicorn overriding our logger
