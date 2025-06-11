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

# Create and set permissions for data directory
RUN mkdir -p /app/data && chmod 777 /app/data

# Expose the port Streamlit will use
EXPOSE 8501

# Set environment variables
ENV PYTHONPATH=/app
ENV STREAMLIT_SERVER_PORT=8501
ENV STREAMLIT_SERVER_ADDRESS=0.0.0.0

# Run the Streamlit app
CMD ["streamlit", "run", "app/app.py"]
