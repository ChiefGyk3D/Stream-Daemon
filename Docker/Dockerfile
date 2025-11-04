# Use an official Python runtime as a parent image
# Python 3.14 provides latest features and security updates
# Multi-arch support: amd64, arm64
FROM python:3.14-slim

# Set build arguments for platform detection (automatically set by buildx)
ARG TARGETPLATFORM
ARG BUILDPLATFORM

# Set the working directory in the container to /app
WORKDIR /app

# CVE-2025-7709: Update SQLite to address FTS5 integer overflow vulnerability
# Upgrade libsqlite3-0 from 3.46.1-7 (vulnerable) to 3.46.1-8 (patched)
# Using Debian unstable only for this specific security patch with APT pinning
# to prevent unintended installation of other unstable packages
RUN echo 'deb http://deb.debian.org/debian unstable main' >> /etc/apt/sources.list && \
    printf "Package: *\nPin: release a=unstable\nPin-Priority: 100\n\nPackage: libsqlite3-0\nPin: release a=unstable\nPin-Priority: 500\n" > /etc/apt/preferences.d/unstable && \
    apt-get update && \
    apt-get install -y --no-install-recommends libsqlite3-0=3.46.1-8 && \
    rm -rf /var/lib/apt/lists/*

# Install system dependencies needed for Python packages
# These packages are available on both amd64 and arm64
RUN apt-get update && apt-get install -y --no-install-recommends \
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
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy the entire project structure from parent directory
COPY stream-daemon.py /app/
COPY stream_daemon/ /app/stream_daemon/
COPY messages.txt /app/
COPY end_messages.txt /app/

# Run stream-daemon.py when the container launches
CMD ["python", "stream-daemon.py"]
