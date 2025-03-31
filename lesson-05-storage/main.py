import os
import json # Import json module for reading/writing data file
from fastapi import FastAPI, HTTPException, Header, status # Added status for POST
from typing import Optional, List # Added List for type hinting
from pydantic import BaseModel # For defining request body structure

# --- Configuration ---
# Same as Lesson 4 - reading from environment variables
greeting = os.getenv('GREETING_MESSAGE', 'Hello from the Hero Registry!')
log_level = os.getenv('LOG_LEVEL', 'INFO')
api_key_secret = os.getenv('API_KEY', 'no-key-provided')
db_password_secret = os.getenv('DATABASE_PASSWORD', 'no-db-password')

print(f"--- Configuration Loaded ---")
print(f"Greeting: {greeting}")
print(f"Log Level: {log_level}")
print(f"API Key (Secret): {'*' * len(api_key_secret) if api_key_secret != 'no-key-provided' else api_key_secret}")
print(f"DB Password (Secret): {'*' * len(db_password_secret) if db_password_secret != 'no-db-password' else db_password_secret}")
print(f"--------------------------")

# --- Persistent Data Handling ---
DATA_DIR = "/data" # Directory where persistent data is stored (mounted volume)
HERO_FILE = os.path.join(DATA_DIR, "heroes.json") # Path to the data file

# Ensure the data directory exists (important for the first run)
os.makedirs(DATA_DIR, exist_ok=True)

# In-memory cache of heroes, loaded from file
heroes_db = []

def load_heroes_from_file():
    """Loads hero data from the JSON file."""
    global heroes_db
    try:
        if os.path.exists(HERO_FILE):
            with open(HERO_FILE, 'r') as f:
                heroes_db = json.load(f)
                print(f"Loaded {len(heroes_db)} heroes from {HERO_FILE}")
        else:
            # Initialize with default data if file doesn't exist
            heroes_db = [
                {"id": 1, "name": "Iron Man", "secret_identity": "Tony Stark"},
                {"id": 2, "name": "Captain America", "secret_identity": "Steve Rogers"},
                {"id": 3, "name": "Black Widow", "secret_identity": "Natasha Romanoff"},
            ]
            print(f"Hero file not found. Initializing with default data.")
            save_heroes_to_file() # Save the initial data
    except (json.JSONDecodeError, IOError) as e:
        print(f"Error loading heroes from {HERO_FILE}: {e}. Using empty list.")
        heroes_db = []

def save_heroes_to_file():
    """Saves the current hero data to the JSON file."""
    try:
        with open(HERO_FILE, 'w') as f:
            json.dump(heroes_db, f, indent=2) # Use indent for readability
            print(f"Saved {len(heroes_db)} heroes to {HERO_FILE}")
    except IOError as e:
        print(f"Error saving heroes to {HERO_FILE}: {e}")

# --- Pydantic Models ---
# Define the structure for creating/updating heroes
class HeroCreate(BaseModel):
    name: str
    secret_identity: str

class Hero(HeroCreate): # Inherits from HeroCreate
    id: int

# --- FastAPI App ---
app = FastAPI(title="Hero Registry API (Persistent)", version="0.3.0")

# Load initial data when the application starts
@app.on_event("startup")
async def startup_event():
    load_heroes_from_file()

# --- API Endpoints ---
@app.get("/")
async def read_root():
    return {"message": greeting}

# GET all heroes - now reads from the loaded heroes_db
@app.get("/heroes", response_model=List[Hero]) # Add response model for better docs
async def get_heroes(x_api_key: Optional[str] = Header(None)):
    # Simple check (same as lesson 4)
    if api_key_secret != 'no-key-provided' and x_api_key != api_key_secret:
         print(f"Attempted access with invalid API key: {x_api_key}")
         # raise HTTPException(status_code=401, detail="Invalid API Key")
         pass
    print(f"API Key check passed (or skipped). Returning hero list.")
    return heroes_db # Return the list loaded from file

# GET hero by ID - reads from loaded heroes_db
@app.get("/heroes/{hero_id}", response_model=Hero)
async def get_hero_by_id(hero_id: int):
    hero = next((h for h in heroes_db if h["id"] == hero_id), None)
    if hero:
        return hero
    else:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Hero not found")

# POST - Add a new hero
@app.post("/heroes", response_model=Hero, status_code=status.HTTP_201_CREATED)
async def create_hero(hero_data: HeroCreate, x_api_key: Optional[str] = Header(None)):
    # Simple check (same as lesson 4)
    if api_key_secret != 'no-key-provided' and x_api_key != api_key_secret:
         print(f"Attempted POST with invalid API key: {x_api_key}")
         # raise HTTPException(status_code=401, detail="Invalid API Key")
         pass

    # Find the next available ID
    new_id = max(h["id"] for h in heroes_db) + 1 if heroes_db else 1
    new_hero = Hero(id=new_id, **hero_data.dict()) # Create Hero object

    heroes_db.append(new_hero.dict()) # Add to our in-memory list
    save_heroes_to_file() # Save the updated list to the file
    print(f"Added new hero: {new_hero.name}")
    return new_hero

# Main entry point
if __name__ == "__main__":
    import uvicorn
    print("Starting Hero Registry API server (Persistent)...")
    # Load data immediately if running directly
    load_heroes_from_file()
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
