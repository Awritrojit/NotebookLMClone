FROM python:3.12-slim

# Install system build dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends build-essential python3-setuptools python3-wheel python3-pip python3-venv python3-dev && \
    rm -rf /var/lib/apt/lists/*
RUN pip install --upgrade pip setuptools wheel

# Prevent Python from writing .pyc files to disc and buffering stdout/stderr.
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set working directory
WORKDIR /app

# Upgrade pip and install runtime dependencies.
COPY requirements.txt /app/
RUN pip install -r requirements.txt

# Copy the remaining project files.
COPY . /app/

# Copy the .env file if it exists
#COPY .env /app/.env

# Expose the port Render will use (adjust if needed)
EXPOSE 5001

# Set environment variables for Flask.
ENV FLASK_APP=app/app.py
ENV FLASK_RUN_HOST=0.0.0.0
ENV FLASK_RUN_PORT=5001

# Run the Flask app.
CMD ["flask", "run", "--port=5001"]
