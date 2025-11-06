# Use an official Python runtime as a parent image
# Python 3.14 with multi-arch support: amd64, arm64
FROM python:3.14-slim

# Set build arguments for platform detection (automatically set by buildx)
ARG TARGETPLATFORM
ARG BUILDPLATFORM

# Set the working directory in the container to /app
WORKDIR /app

# Install system dependencies and upgrade SQLite to fix CVE-2025-7709
# CVE-2025-7709: Integer overflow in SQLite FTS5 extension (fixed in 3.50.3)
# Debian trixie ships 3.46.1-7, so we compile SQLite 3.50.4 from source
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

# Copy requirements first for better caching
COPY Docker/requirements.txt /app/

# Install any needed packages specified in requirements.txt
# Upgrade pip to 25.3+ to fix CVE-2025-8869 (symbolic link extraction vulnerability)
RUN pip install --no-cache-dir --upgrade "pip>=25.3" && \
    pip install --no-cache-dir -r requirements.txt

# Copy the entire project structure from parent directory
COPY stream-daemon.py /app/
COPY stream_daemon/ /app/stream_daemon/
COPY messages.txt /app/
COPY end_messages.txt /app/

# Run stream-daemon.py when the container launches
CMD ["python", "stream-daemon.py"]
