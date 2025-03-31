import os # Import the 'os' module to access environment variables
from fastapi import FastAPI, HTTPException, Header # Import Header for API key check
from typing import Optional # To make Header optional

# --- Configuration ---
# Read configuration values from environment variables.
# os.getenv('VAR_NAME', 'default_value') reads the variable VAR_NAME.
# If it's not set in the environment, it uses the 'default_value'.
# Kubernetes will inject values from ConfigMaps and Secrets into these env vars.

# Read from ConfigMap (non-sensitive)
greeting = os.getenv('GREETING_MESSAGE', 'Hello from the Hero Registry!')
log_level = os.getenv('LOG_LEVEL', 'INFO') # We'll use this later in logging lesson

# Read from Secret (sensitive)
# For demonstration, we'll just print it at startup (NEVER do this in production!)
api_key_secret = os.getenv('API_KEY', 'no-key-provided')
db_password_secret = os.getenv('DATABASE_PASSWORD', 'no-db-password') # Example

print(f"--- Configuration Loaded ---")
print(f"Greeting: {greeting}")
print(f"Log Level: {log_level}")
print(f"API Key (Secret): {'*' * len(api_key_secret) if api_key_secret != 'no-key-provided' else api_key_secret}") # Mask secret
print(f"DB Password (Secret): {'*' * len(db_password_secret) if db_password_secret != 'no-db-password' else db_password_secret}") # Mask secret
print(f"--------------------------")

# --- FastAPI App ---
app = FastAPI(title="Hero Registry API (Configured)", version="0.2.0")

heroes_db = [
    {"id": 1, "name": "Iron Man", "secret_identity": "Tony Stark"},
    {"id": 2, "name": "Captain America", "secret_identity": "Steve Rogers"},
    {"id": 3, "name": "Black Widow", "secret_identity": "Natasha Romanoff"},
]

# New root endpoint to display the greeting message from the ConfigMap
@app.get("/")
async def read_root():
    """
    Returns the welcome message configured via environment variable.
    """
    return {"message": greeting}

@app.get("/heroes")
async def get_heroes(x_api_key: Optional[str] = Header(None)): # Optional Header for API Key
    """
    Retrieve the list of all registered heroes.
    Optionally checks for X-API-Key header (using value from Secret).
    """
    # Simple check for demonstration - not real security!
    if api_key_secret != 'no-key-provided' and x_api_key != api_key_secret:
         print(f"Attempted access with invalid API key: {x_api_key}")
         # raise HTTPException(status_code=401, detail="Invalid API Key")
         # Commenting out the actual block for easier initial testing.
         # In a real app, you'd uncomment the HTTPException.
         pass # Allow access even if key is wrong/missing for now

    print(f"API Key check passed (or skipped). Returning hero list.")
    return {"heroes": heroes_db}

@app.get("/heroes/{hero_id}")
async def get_hero_by_id(hero_id: int):
    """
    Retrieve details for a specific hero by their ID.
    """
    hero = next((h for h in heroes_db if h["id"] == hero_id), None)
    if hero:
        return {"hero": hero}
    else:
        raise HTTPException(status_code=404, detail="Hero not found")

# Main entry point (no changes needed here for config)
if __name__ == "__main__":
    import uvicorn
    print("Starting Hero Registry API server (Configured)...")
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
