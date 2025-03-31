# Lesson 1: Welcome, Recruit! (Your First FastAPI App & Containerization)

**Objective:** Build a basic web API using FastAPI and package it into a runnable Docker container.

**Analogy:** Think of this lesson as your first day at the Hero Academy. You'll build your initial piece of tech (a simple API) and then forge your first suit of armor (a Docker container) to house it.

## Concepts Introduced

### 1. FastAPI: The Headquarters Blueprint

*   **What it is:** A modern, fast (high-performance) web framework for building APIs with Python.
*   **Why use it:** It's easy to learn, fast to code with, and automatically generates interactive documentation for your API (like a user manual for your tech).
*   **Analogy:** FastAPI is like the architectural blueprint for the Avengers Tower. It defines the structure, how different sections (endpoints) are laid out, and how requests (visitors/missions) are handled efficiently. Our `main.py` uses FastAPI to define endpoints like `/heroes` (the main roster display) and `/heroes/{hero_id}` (accessing a specific hero's file).

### 2. Docker & Containers: The Iron Man Suit

*   **What is a Container?** A standardized unit of software that packages up code and all its dependencies so the application runs quickly and reliably from one computing environment to another.
*   **Analogy:** A container is like Iron Man's suit. The suit contains Tony Stark (the code), the arc reactor (dependencies like Python, FastAPI), and all the necessary systems (OS libraries) self-contained. No matter where Iron Man goes (different computers/servers), the suit works the same way because everything it needs is inside it. It isolates the hero (app) from the outside world.
*   **What is Docker?** A platform and tool for building, shipping, and running containers.
*   **Analogy:** Docker is like the Stark Industries workshop and assembly line. It provides the tools (`docker build`, `docker run`) and processes (`Dockerfile`) to construct, manage, and deploy these suits (containers).

### 3. Dockerfile: Suit Assembly Instructions

*   **What it is:** A text file containing step-by-step instructions that Docker uses to build a container image.
*   **Analogy:** The `Dockerfile` is the detailed instruction manual or blueprint for assembling an Iron Man suit. Each line (`FROM`, `WORKDIR`, `COPY`, `RUN`, `EXPOSE`, `CMD`) is a specific step in the assembly process.
    *   `FROM python:3.11-slim`: Start with a standard, lightweight Python suit frame.
    *   `WORKDIR /app`: Designate the main workshop area inside the suit.
    *   `COPY requirements.txt .`: Bring the list of required components into the workshop.
    *   `RUN pip install ...`: Install the core components (FastAPI, Uvicorn) into the frame.
    *   `COPY main.py .`: Install the application's core logic (the AI).
    *   `EXPOSE 8000`: Open the communication port (like the helmet's comms channel).
    *   `CMD [...]`: Define the command to power up the suit (start the API server).

## Practical Exercise: Build and Run Your First Container

1.  **Prerequisites:** Ensure you have Docker Desktop (or Docker Engine on Linux) installed and running on your machine.
2.  **Navigate:** Open your terminal or command prompt and navigate into the `hero-academy/lesson-01-recruit` directory.
    ```bash
    cd hero-academy/lesson-01-recruit
    ```
3.  **Build the Image:** Use the `docker build` command. This reads the `Dockerfile` and creates the container image.
    *   `-t hero-registry:0.1`: This *tags* the image with a name (`hero-registry`) and version (`0.1`), making it easy to reference. Think of it as giving your suit model a name (e.g., "Mark I").
    *   `.`: This tells Docker to look for the `Dockerfile` in the current directory.
    ```bash
    docker build -t hero-registry:0.1 .
    ```
    You'll see Docker executing the steps from your `Dockerfile`.

4.  **Run the Container:** Use the `docker run` command to start a container from the image you just built.
    *   `--rm`: Automatically remove the container when it stops (cleans up).
    *   `-p 8000:8000`: This *publishes* the container's port 8000 to your host machine's port 8000. This allows you to access the API running *inside* the container from your web browser. (Analogy: Connecting an external access cable from your computer to the suit's communication port).
    *   `hero-registry:0.1`: The name and tag of the image to run.
    ```bash
    docker run --rm -p 8000:8000 hero-registry:0.1
    ```
    You should see output indicating the Uvicorn server has started.

5.  **Test the API:** Open your web browser and go to:
    *   `http://localhost:8000/heroes` - You should see the JSON list of heroes.
    *   `http://localhost:8000/heroes/1` - You should see Iron Man's details.
    *   `http://localhost:8000/heroes/99` - You should see a "Hero not found" error.
    *   `http://localhost:8000/docs` - You should see the interactive FastAPI documentation page.

6.  **Stop the Container:** Go back to your terminal where the container is running and press `Ctrl + C`. The container will stop, and because we used `--rm`, it will be removed.

## Problem-Solving Framework: Thinking Like a Hero Engineer

When things go wrong (and they often do in tech!), don't panic. Think systematically:

1.  **Identify the Symptom:** What *exactly* is happening? Is it an error message during `docker build`? Does the `docker run` command fail? Does the API endpoint give the wrong response or an error in the browser? Be specific. (e.g., "Docker build fails at the `pip install` step with a 'package not found' error", "Browser shows 'Connection Refused'").
2.  **Locate the Problem Area:** Based on the symptom, where *might* the problem be?
    *   *Build errors (`docker build`):* Likely in the `Dockerfile` syntax, the `requirements.txt` file, or network issues preventing downloads. Check the specific `RUN` command that failed.
    *   *Run errors (`docker run`):* Could be port conflicts (`-p` mapping), issues with the `CMD` instruction in the `Dockerfile`, or problems within the application code (`main.py`) that only appear at startup. Check the container logs (`docker logs <container_id>` if you didn't use `--rm`).
    *   *API errors (Browser/`curl`):* Probably an issue in the `main.py` logic (how endpoints are defined, data handling) or the `uvicorn` command configuration (`host`/`port`). Check the running container's terminal output for errors.
3.  **Consult the Blueprints/Manuals:**
    *   *Dockerfile:* Did you copy the right files? Are the commands correct? Is the base image (`FROM`) suitable?
    *   *`main.py`:* Is the Python syntax correct? Does the FastAPI logic make sense? Did you remember `host="0.0.0.0"` for Uvicorn if running in Docker?
    *   *`requirements.txt`:* Are all necessary packages listed? Are the names spelled correctly?
    *   *Error Messages:* Read them carefully! They often point directly to the file and line number causing the issue. Google specific error messages – you're likely not the first recruit to encounter them!
4.  **Isolate and Test:** Try simplifying. Can you run the Python app *outside* of Docker (`python main.py`)? Does that work? If so, the problem is likely Docker-related. If not, the problem is in the Python code itself. Can you build a *simpler* Dockerfile?
5.  **Verify Assumptions:** Did you assume a file was copied when it wasn't? Did you assume a package was installed? Double-check the steps in the `Dockerfile` output during the build.

**Example Scenario:** `docker run` command works, but `http://localhost:8000/heroes` gives "Connection Refused".

*   **Symptom:** Connection refused in the browser.
*   **Location:** Network connection between browser and container, or the server inside the container isn't listening correctly.
*   **Check:**
    *   Did you use `-p 8000:8000` in `docker run`? (External connection)
    *   Check the container logs (`docker run` output). Does it say `Uvicorn running on http://0.0.0.0:8000`? If it says `127.0.0.1:8000`, the server inside isn't listening for external Docker connections. Fix the `CMD` in the `Dockerfile` to use `host="0.0.0.0"`.
    *   Is another process already using port 8000 on your host machine? Try mapping to a different host port: `docker run --rm -p 8081:8000 hero-registry:0.1` and access `http://localhost:8081/heroes`.

By following these steps, you can systematically debug issues and understand *why* things work (or don't work) the way they do.

**Congratulations, Recruit! You've built your first API and containerized it. In the next lesson, we'll set up version control and a CI/CD pipeline to automate the build process.**
