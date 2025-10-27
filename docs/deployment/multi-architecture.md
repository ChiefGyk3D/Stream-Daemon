# Multi-Architecture Docker Builds

Stream Daemon supports multiple architectures for maximum compatibility across different hardware platforms.

## Supported Architectures

- **linux/amd64** - Standard x86_64 computers, servers, and cloud instances
- **linux/arm64** - ARM-based systems including:
  - Raspberry Pi 3B+ and newer (64-bit OS)
  - Apple Silicon Macs (M1, M2, M3)
  - AWS Graviton instances
  - Other ARM64 devices

## Pre-built Images

Pre-built multi-architecture images are automatically published to:

### GitHub Container Registry (GHCR)
```bash
docker pull ghcr.io/chiefgyk3d/stream-daemon:latest
```

### Docker Hub (if configured)
```bash
docker pull <username>/stream-daemon:latest
```

Docker will automatically pull the correct architecture for your system.

## Building Multi-Architecture Images Locally

### Prerequisites

1. **Docker Buildx** (included in Docker Desktop and recent Docker Engine versions)
   ```bash
   docker buildx version
   ```

2. **Create a builder instance** (one-time setup)
   ```bash
   docker buildx create --name multiarch --use
   docker buildx inspect --bootstrap
   ```

### Build for Multiple Architectures

```bash
# Build for both amd64 and arm64
docker buildx build \
  --platform linux/amd64,linux/arm64 \
  -t stream-daemon:latest \
  -f Docker/Dockerfile \
  --load \
  .
```

**Note:** The `--load` flag only works when building for a single platform. To build for multiple platforms, use `--push` to push directly to a registry:

```bash
# Build and push to a registry
docker buildx build \
  --platform linux/amd64,linux/arm64 \
  -t your-registry/stream-daemon:latest \
  -f Docker/Dockerfile \
  --push \
  .
```

### Build for Specific Architecture

```bash
# Build only for ARM64 (e.g., for Raspberry Pi)
docker buildx build \
  --platform linux/arm64 \
  -t stream-daemon:latest \
  -f Docker/Dockerfile \
  --load \
  .

# Build only for AMD64
docker buildx build \
  --platform linux/amd64 \
  -t stream-daemon:latest \
  -f Docker/Dockerfile \
  --load \
  .
```

## GitHub Actions Workflow

The project uses GitHub Actions to automatically build and publish multi-architecture images:

1. **On push to main branch** - Builds and publishes to GHCR
2. **On version tags (v*.*.*)** - Builds and publishes versioned releases
3. **Pull requests** - Builds and tests (but doesn't publish)

The workflow builds for both `linux/amd64` and `linux/arm64` platforms automatically.

## Installation Script

The `scripts/install-systemd.sh` script supports both architectures:

1. **Pull from GHCR** (recommended):
   - Automatically selects the correct architecture
   - Faster than building locally
   - Production-ready images

2. **Build locally**:
   - Builds for your current system architecture
   - Good for development and customization

## Raspberry Pi Considerations

### Recommended Models
- Raspberry Pi 4 (4GB+ RAM recommended)
- Raspberry Pi 3B+ (minimum, with 64-bit OS)

### OS Requirements
- Use a 64-bit OS (Raspberry Pi OS 64-bit or Ubuntu Server 64-bit)
- 32-bit OS is not supported by the arm64 images

### Performance Tips
1. **Use pre-built images** - Building on Raspberry Pi can be slow
2. **Monitor memory usage** - Ensure adequate swap space
3. **Use SD card or SSD** - Docker images can be large

## Verifying Architecture

Check which architecture your pulled/built image supports:

```bash
docker inspect stream-daemon:latest | grep Architecture
```

Or use buildx to see all platforms:

```bash
docker buildx imagetools inspect ghcr.io/chiefgyk3d/stream-daemon:latest
```

## Troubleshooting

### "exec format error"
This means you're trying to run an image built for a different architecture. Solutions:
1. Pull the correct multi-arch image from GHCR
2. Rebuild for your platform
3. Enable QEMU emulation (slow):
   ```bash
   docker run --privileged --rm tonistiigi/binfmt --install all
   ```

### Slow builds on ARM
- Use pre-built images from GHCR instead
- Increase swap space
- Consider using GitHub Actions to build and host images

### Image not available for platform
Check that the image was built with multi-platform support:
```bash
docker buildx imagetools inspect <image-name>
```

## Resources

- [Docker Buildx Documentation](https://docs.docker.com/build/buildx/)
- [Multi-platform Images](https://docs.docker.com/build/building/multi-platform/)
- [GitHub Actions Docker Build/Push](https://github.com/docker/build-push-action)
