from fastapi import FastAPI

# Think of FastAPI as the blueprint for our hero's headquarters.
# It helps organize how requests (missions) come in and how responses (results) go out.
app = FastAPI(title="Hero Registry API", version="0.1.0")

# Our initial team roster - stored directly in the code for now.
# Later, we'll learn how to manage data more dynamically!
heroes_db = [
    {"id": 1, "name": "Iron Man", "secret_identity": "Tony Stark"},
    {"id": 2, "name": "Captain America", "secret_identity": "Steve Rogers"},
    {"id": 3, "name": "Black Widow", "secret_identity": "Natasha Romanoff"},
]

# This is an endpoint - like a specific department in the headquarters.
# This one handles requests for the list of all heroes.
# The '@app.get("/heroes")' is like the sign on the door, telling everyone
# what kind of mission this department handles (GET requests for /heroes).
@app.get("/heroes")
async def get_heroes():
    """
    Retrieve the list of all registered heroes.
    Think of this as asking Mission Control for the current active roster.
    """
    return {"heroes": heroes_db}

# This endpoint allows fetching a single hero by their ID.
# The '{hero_id}' part is a path parameter - like asking for a specific hero's file
# by their unique ID number.
@app.get("/heroes/{hero_id}")
async def get_hero_by_id(hero_id: int):
    """
    Retrieve details for a specific hero by their ID.
    Imagine asking JARVIS to pull up the file for a specific Avenger.
    """
    hero = next((h for h in heroes_db if h["id"] == hero_id), None)
    if hero:
        return {"hero": hero}
    else:
        # If the hero isn't found, we need to report that back.
        # This uses standard HTTP status codes - like mission outcome codes. 404 means "Not Found".
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Hero not found")

# This is the main entry point when running the app directly (like starting up the HQ).
# Uvicorn is the high-performance server (like the power source) that runs our FastAPI app.
# 'host="0.0.0.0"' is important for Docker - it means "listen for requests from anywhere",
# not just the local machine. Think of it as opening all communication channels.
# 'port=8000' is the specific channel (frequency) it listens on.
if __name__ == "__main__":
    import uvicorn
    print("Starting Hero Registry API server...")
    # When running directly (python main.py), it uses port 8000.
    # When run via Docker, the Dockerfile will specify the command.
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
