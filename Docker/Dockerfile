# Use an official Python runtime as a parent image
# Python 3.14 with multi-arch support: amd64, arm64
# Because running stream announcements requires the absolute latest Python.
# Can't use 3.13. That would be barbaric. We need 3.14 to tell people about Fortnite streams.
# The base image is pinned by digest so a rebuild is reproducible and a
# retagged upstream image cannot slip in; Dependabot moves the digest.
FROM python:3.14-slim@sha256:c3e521df8b2b498a7a682e7e18676771cb80c6b75b8699af886b2d554ce40151

# Set build arguments for platform detection (automatically set by buildx)
ARG TARGETPLATFORM
ARG BUILDPLATFORM

# Install system dependencies and upgrade SQLite to fix CVE-2025-7709
# CVE-2025-7709: Integer overflow in SQLite FTS5 extension (fixed in 3.50.3)
# Debian trixie ships 3.46.1-7, so we compile SQLite 3.50.4 from source
# Because a database vulnerability in our stream announcement tool is clearly
# a national security threat. The terrorists might hack our "going live" messages.
# Better compile from source. For the children.
# Build in a dedicated directory instead of `cd`-ing around (DL3003); the
# build tree is removed in the same layer, together with the build-only tools.
WORKDIR /tmp/sqlite
# `apt-get upgrade` applies pending Debian security updates (the base image lags
# them, and the image scan fails on any fixed HIGH finding such as libpcre2).
# Apt versions are left unpinned on purpose: the base image is pinned by digest,
# and Debian removes superseded package versions, so exact apt pins would break
# the build at every security update.
# hadolint ignore=DL3008
RUN apt-get update && apt-get upgrade -y && apt-get install -y --no-install-recommends \
    gcc \
    libc6-dev \
    libffi-dev \
    libssl-dev \
    wget \
    make \
    tcl \
    && wget --progress=dot:giga -O sqlite.tar.gz https://www.sqlite.org/2025/sqlite-autoconf-3500400.tar.gz \
    && tar xzf sqlite.tar.gz --strip-components=1 \
    && ./configure --prefix=/usr --enable-fts5 \
    && make -j"$(nproc)" \
    && make install \
    && ldconfig \
    && rm -rf /tmp/sqlite \
    && apt-get purge -y wget make tcl \
    && apt-get autoremove -y \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Create and activate virtual environment
ENV VIRTUAL_ENV=/opt/venv
RUN python -m venv $VIRTUAL_ENV
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

# Copy requirements first for better caching. The repository has exactly one
# requirements.txt (the root one) — the Docker/ copy it once mirrored drifted
# and shipped an image missing dependencies, so it's gone.
COPY requirements.txt /app/

# Install the pinned requirements, then take the installer out of the image.
# Upgrade pip to 25.3+ first for CVE-2025-8869 (symbolic link extraction).
#
# pip 26.x ships a CycloneDX SBOM for the libraries it vendors
# (pip/_vendor/bom.cdx.json) and Trivy reads it as installed packages, so the
# image scan reports pip's private copies of msgpack 1.1.2
# (GHSA-6v7p-g79w-8964) and setuptools 70.3.0 (CVE-2025-47273,
# CVE-2026-59890). No pip release carries fixed copies yet, nothing here calls
# them, and the running daemon never needs pip, so the runtime image ships
# without one: both the venv's copy and the base image's /usr/local copy are
# removed. Anyone who needs it back in a container can run
# `python -m ensurepip` (the bundled wheel stays).
# Cache bust: 2026-01-20 - Added ollama==0.6.1 support
RUN pip install --no-cache-dir --upgrade "pip>=25.3" && \
    pip install --no-cache-dir --require-hashes -r requirements.txt && \
    pip uninstall -y pip && \
    /usr/local/bin/python -m pip uninstall -y pip

# Copy the entire project structure from parent directory
COPY stream-daemon.py /app/
COPY stream_daemon/ /app/stream_daemon/
COPY messages.txt /app/
COPY end_messages.txt /app/

# Dedicated non-root user. UID/GID 1000: the compose deployment mounts only
# read-only message files, so there is no existing writable mount to match.
RUN groupadd --gid 1000 streamdaemon \
    && useradd --uid 1000 --gid 1000 --create-home --shell /usr/sbin/nologin streamdaemon \
    && chown -R streamdaemon:streamdaemon /app
USER 1000:1000

# Health check: probe the daemon's /healthz endpoint (hypeman-social
# observability) when HEALTH_PORT is set; otherwise verify PID 1 is alive so
# the check passes for deployments that keep health off. Uses python urllib
# because slim images ship no curl.
HEALTHCHECK --interval=60s --timeout=5s --start-period=30s --retries=3 \
    CMD ["python", "-c", "import os,sys,urllib.request;port=os.getenv('HEALTH_PORT');urllib.request.urlopen(f'http://127.0.0.1:{port}/healthz', timeout=4) if port else sys.exit(0 if os.path.isdir('/proc/1') else 1)"]

# Run stream-daemon.py when the container launches
CMD ["python", "stream-daemon.py"]
