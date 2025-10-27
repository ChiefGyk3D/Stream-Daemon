# Use an official Python runtime as a parent image
# Python 3.13 is the latest STABLE version with full package support
# Multi-arch support: amd64, arm64
FROM python:3.13-slim

# Set build arguments for platform detection (automatically set by buildx)
ARG TARGETPLATFORM
ARG BUILDPLATFORM

# Set the working directory in the container to /app
WORKDIR /app

# Install system dependencies needed for Python packages
# These packages are available on both amd64 and arm64
# Apply security updates to address vulnerabilities in base image
RUN apt-get update && apt-get upgrade -y && apt-get install -y --no-install-recommends \
    gcc \
    libffi-dev \
    libssl-dev \
    && rm -rf /var/lib/apt/lists/*

# Create and activate virtual environment
ENV VIRTUAL_ENV=/opt/venv
RUN python -m venv $VIRTUAL_ENV
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

# Copy requirements first for better caching
COPY Docker/requirements.txt /app/

# Install any needed packages specified in requirements.txt
# Upgrade pip to latest version to address security vulnerabilities
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy the entire project structure from parent directory
COPY stream-daemon.py /app/
COPY stream_daemon/ /app/stream_daemon/
COPY messages.txt /app/
COPY end_messages.txt /app/

# Run stream-daemon.py when the container launches
CMD ["python", "stream-daemon.py"]
