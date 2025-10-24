# Use an official Python runtime as a parent image
# Python 3.13 is the latest STABLE version with full package support
# Python 3.14 is too new - many packages don't support it yet
FROM python:3.13-alpine

# Set the working directory in the container to /app
WORKDIR /app

# Install system dependencies needed for Python packages
# Alpine uses apk, not apt-get
RUN apk add --no-cache \
    gcc \
    musl-dev \
    libffi-dev \
    openssl-dev \
    python3-dev \
    cargo \
    build-base

# Create and activate virtual environment
ENV VIRTUAL_ENV=/opt/venv
RUN python -m venv $VIRTUAL_ENV
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

# Copy requirements first for better caching
COPY requirements.txt /app/

# Install any needed packages specified in requirements.txt
# Now installs into the virtual environment
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Add the current directory contents into the container at /app
COPY . /app

# Run stream-daemon.py when the container launches
# Virtual environment is already in PATH, so python will use venv
CMD ["python", "stream-daemon-docker.py"]
