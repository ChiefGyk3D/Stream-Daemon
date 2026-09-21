# Use an official Python runtime as a parent image
# Python 3.14 with multi-arch support: amd64, arm64
# Because running stream announcements requires the absolute latest Python.
# Can't use 3.13. That would be barbaric. We need 3.14 to tell people about Fortnite streams.
# The base image is pinned by digest so a rebuild is reproducible and a
# retagged upstream image cannot slip in; Dependabot moves the digest.
FROM python:3.14-slim@sha256:caaf356f40667c496d405780745b9ac25771c189a51dfcc42430d531ea09f8a2

# Set build arguments for platform detection (automatically set by buildx)
ARG TARGETPLATFORM
ARG BUILDPLATFORM

# Set the working directory in the container to /app
WORKDIR /app

# Install system dependencies and upgrade SQLite to fix CVE-2025-7709
# CVE-2025-7709: Integer overflow in SQLite FTS5 extension (fixed in 3.50.3)
# Debian trixie ships 3.46.1-7, so we compile SQLite 3.50.4 from source
# Because a database vulnerability in our stream announcement tool is clearly
# a national security threat. The terrorists might hack our "going live" messages.
# Better compile from source. For the children.
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libc6-dev \
    libffi-dev \
    libssl-dev \
    wget \
    make \
    tcl \
    && cd /tmp \
    && wget https://www.sqlite.org/2025/sqlite-autoconf-3500400.tar.gz \
    && tar xzf sqlite-autoconf-3500400.tar.gz \
    && cd sqlite-autoconf-3500400 \
    && ./configure --prefix=/usr --enable-fts5 \
    && make -j$(nproc) \
    && make install \
    && ldconfig \
    && cd / \
    && rm -rf /tmp/sqlite-autoconf-3500400* \
    && apt-get purge -y wget make tcl \
    && apt-get autoremove -y \
    && rm -rf /var/lib/apt/lists/*

# Create and activate virtual environment
ENV VIRTUAL_ENV=/opt/venv
RUN python -m venv $VIRTUAL_ENV
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

# Copy requirements first for better caching. The repository has exactly one
# requirements.txt (the root one) — the Docker/ copy it once mirrored drifted
# and shipped an image missing dependencies, so it's gone.
COPY requirements.txt /app/

# Install any needed packages specified in requirements.txt
# Upgrade pip to 25.3+ to fix CVE-2025-8869 (symbolic link extraction vulnerability)
# Cache bust: 2026-01-20 - Added ollama==0.6.1 support
RUN pip install --no-cache-dir --upgrade "pip>=25.3" && \
    pip install --no-cache-dir -r requirements.txt

# Copy the entire project structure from parent directory
COPY stream-daemon.py /app/
COPY stream_daemon/ /app/stream_daemon/
COPY messages.txt /app/
COPY end_messages.txt /app/

# Health check: probe the daemon's /healthz endpoint (hypeman-social
# observability) when HEALTH_PORT is set; otherwise verify PID 1 is alive so
# the check passes for deployments that keep health off. Uses python urllib
# because slim images ship no curl.
HEALTHCHECK --interval=60s --timeout=5s --start-period=30s --retries=3 \
    CMD ["python", "-c", "import os,sys,urllib.request;port=os.getenv('HEALTH_PORT');urllib.request.urlopen(f'http://127.0.0.1:{port}/healthz', timeout=4) if port else sys.exit(0 if os.path.isdir('/proc/1') else 1)"]

# Run stream-daemon.py when the container launches
CMD ["python", "stream-daemon.py"]
