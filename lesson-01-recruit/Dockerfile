# --- Base Stage ---
# Use an official Python runtime as a parent image.
# Think of this as starting with a basic, standard suit frame.
FROM python:3.11-slim as base

# Set the working directory inside the container.
# This is like designating the main workshop area within the suit.
WORKDIR /app

# Prevent python from writing pyc files to disc (optional).
ENV PYTHONDONTWRITEBYTECODE 1
# Ensure python output is sent straight to the terminal without buffering.
ENV PYTHONUNBUFFERED 1

# --- Builder Stage ---
# This stage installs dependencies.
FROM base as builder

# Install build dependencies needed for some python packages (if any).
# Sometimes, you need special tools to assemble certain suit components.
# RUN apt-get update && apt-get install -y --no-install-recommends gcc

# Copy the requirements file into the container.
COPY requirements.txt .

# Install the Python dependencies.
# This is like adding the core components and wiring to the suit frame.
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# --- Final Stage ---
# This stage builds the final, lean image.
FROM base as final

# Copy the installed dependencies from the builder stage.
# We take the assembled components and put them into the final suit.

# ----FIXING AN ERROR-----
# PREVIOUS CODE HAD THIS LINE: issue is that the below line only has the /app directory from builder
#   which has the requirements.txt but doesn't have the python packages
# COPY --from=builder /app /app

# Copy the installed packages (site-packages and executables) from the builder stage
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy the application code into the container.
# This is like installing the final software and AI into the suit.
COPY main.py .

# Expose the port the app runs on.
# This opens the communication channel (port 8000) on the suit.
EXPOSE 8000

# Define the command to run the application.
# This is the command to power up the suit: run the uvicorn server.
# It listens on all interfaces (0.0.0.0) on port 8000.
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
