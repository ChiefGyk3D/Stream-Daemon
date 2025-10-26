# GitHub Actions Workflows

This directory contains automated CI/CD workflows for Stream Daemon.

## 📋 Workflows Overview

### 🧪 CI - Tests (`ci-tests.yml`)
**Triggers:** Push to main/develop/copilot branches, PRs, manual dispatch

**What it does:**
- Tests on Python 3.11, 3.12, and 3.13
- Runs full pytest suite with coverage
- Uploads coverage to Codecov
- Runs security scanning (Bandit)
- Lints code with Ruff
- Checks for known vulnerabilities (Safety)

**Required Secrets:**
- `CODECOV_TOKEN` (optional, for coverage reports)

---

### 🔍 Dependency Review (`dependency-review.yml`)
**Triggers:** PRs to main/develop, weekly schedule (Mondays), manual dispatch

**What it does:**
- Reviews dependency changes in PRs
- Scans for vulnerabilities with Safety and pip-audit
- Optional Snyk scanning (requires token)
- Uploads security reports as artifacts

**Required Secrets:**
- `SNYK_TOKEN` (optional, for enhanced scanning)

---

### 🐳 Docker Build & Publish (`docker-build-publish.yml`)
**Triggers:** Push to main, version tags (v*.*.*), PRs, manual dispatch

**What it does:**
- Builds Docker image from `Docker/Dockerfile`
- Tests image can import stream_daemon
- Scans image with Trivy for vulnerabilities
- Publishes to GitHub Container Registry (ghcr.io)
- Publishes to Docker Hub (on main branch/tags only)
- Multi-architecture builds (amd64, arm64)

**Image Tags Generated:**
- `latest` (main branch only)
- `v1.2.3`, `v1.2`, `v1` (from git tags)
- `main-<sha>` (branch + commit SHA)
- `pr-123` (pull request number)

**Required Secrets:**
- `GITHUB_TOKEN` (auto-provided)
- `DOCKERHUB_USERNAME` (for Docker Hub publishing)
- `DOCKERHUB_TOKEN` (for Docker Hub publishing)

---

### 🔐 CodeQL Analysis (`codeql-analysis.yml`)
**Triggers:** Push to main/develop, PRs, weekly schedule (Sundays), manual dispatch

**What it does:**
- Static code analysis for security issues
- Scans Python code for vulnerabilities
- Uploads results to GitHub Security tab
- Runs extended security and quality queries

**Required Secrets:** None (uses GITHUB_TOKEN)

---

## 🤖 Dependabot Configuration (`dependabot.yml`)

Automatically creates PRs for dependency updates:

- **Python packages** (requirements.txt): Weekly on Mondays
- **Docker base images**: Weekly on Mondays
- **GitHub Actions**: Weekly on Mondays

All PRs are labeled and assigned for review.

---

## 🚀 Setup Instructions

### 1. Enable GitHub Actions
GitHub Actions are enabled by default for public repositories.

### 2. Configure Secrets

#### Required for Docker Hub Publishing:
```bash
# Go to: Settings → Secrets and variables → Actions → New repository secret

DOCKERHUB_USERNAME: your_dockerhub_username
DOCKERHUB_TOKEN: your_dockerhub_access_token
```

#### Optional Integrations:
```bash
CODECOV_TOKEN: your_codecov_token  # For coverage reports at codecov.io
SNYK_TOKEN: your_snyk_token        # For enhanced vulnerability scanning
```

### 3. Docker Hub Access Token
1. Log in to Docker Hub
2. Go to Account Settings → Security
3. Click "New Access Token"
4. Name: `github-actions-stream-daemon`
5. Permissions: Read, Write, Delete
6. Copy token and add to GitHub secrets

### 4. Enable GitHub Container Registry
1. Go to your profile → Packages
2. Find the stream-daemon package
3. Package settings → Change visibility (Public/Private)
4. Connect to repository

---

## 📊 Workflow Status Badges

Add these to your README.md:

```markdown
[![CI Tests](https://github.com/ChiefGyk3D/Stream-Daemon/actions/workflows/ci-tests.yml/badge.svg)](https://github.com/ChiefGyk3D/Stream-Daemon/actions/workflows/ci-tests.yml)
[![Docker Build](https://github.com/ChiefGyk3D/Stream-Daemon/actions/workflows/docker-build-publish.yml/badge.svg)](https://github.com/ChiefGyk3D/Stream-Daemon/actions/workflows/docker-build-publish.yml)
[![CodeQL](https://github.com/ChiefGyk3D/Stream-Daemon/actions/workflows/codeql-analysis.yml/badge.svg)](https://github.com/ChiefGyk3D/Stream-Daemon/actions/workflows/codeql-analysis.yml)
```

---

## 🔧 Testing Workflows Locally

### Using `act` (GitHub Actions local runner):
```bash
# Install act
brew install act  # macOS
# or
curl https://raw.githubusercontent.com/nektos/act/master/install.sh | sudo bash

# Run a specific workflow
act -W .github/workflows/ci-tests.yml

# Run with secrets
act -W .github/workflows/ci-tests.yml -s CODECOV_TOKEN=your_token
```

### Testing Docker builds locally:
```bash
# Build the image
docker build -f Docker/Dockerfile -t stream-daemon:test .

# Test the image
docker run --rm stream-daemon:test python -c "import stream_daemon; print('Success')"

# Scan with Trivy
trivy image stream-daemon:test
```

---

## 🎯 Workflow Triggers Reference

| Workflow | Push | PR | Tag | Schedule | Manual |
|----------|------|----|----|----------|--------|
| CI Tests | ✅ main/develop/copilot | ✅ | ❌ | ❌ | ✅ |
| Dependency Review | ❌ | ✅ | ❌ | ✅ Weekly | ✅ |
| Docker Build/Publish | ✅ main | ✅ | ✅ v*.*.* | ❌ | ✅ |
| CodeQL Analysis | ✅ main/develop | ✅ | ❌ | ✅ Weekly | ✅ |

---

## 🛡️ Security Features

### Automated Scans:
- **Trivy**: Container vulnerability scanning
- **CodeQL**: Static code analysis
- **Bandit**: Python security linting
- **Safety**: Known vulnerability database
- **pip-audit**: PyPI vulnerability scanner
- **Snyk**: Comprehensive dependency scanning (optional)

### Dependency Management:
- **Dependabot**: Automated dependency updates
- **Dependency Review**: PR-based dependency change review
- Locked versions in requirements.txt (supply chain security)

---

## 📝 Maintenance

### Updating Workflows:
1. Edit workflow files in `.github/workflows/`
2. Test locally with `act` if possible
3. Commit and push to a feature branch
4. Create PR to test workflows
5. Merge to main

### Monitoring:
- Check Actions tab for workflow runs
- Review Security tab for CodeQL/Trivy findings
- Check Dependabot PRs weekly
- Review artifact uploads for detailed reports

---

## 🔗 External Services Integration

### Codecov (Code Coverage)
1. Sign up at https://codecov.io
2. Link GitHub repository
3. Get upload token
4. Add as `CODECOV_TOKEN` secret

### Snyk (Security Scanning)
1. Sign up at https://snyk.io
2. Link GitHub repository
3. Get API token
4. Add as `SNYK_TOKEN` secret

---

## 💡 Best Practices

1. **Always test in PRs** before merging to main
2. **Review Dependabot PRs** - don't auto-merge without testing
3. **Monitor workflow failures** - fix immediately
4. **Keep secrets secure** - never commit tokens
5. **Update workflows** when adding new dependencies
6. **Check security alerts** in GitHub Security tab

---

## 🆘 Troubleshooting

### Workflow fails on pip install:
- Check requirements.txt for version conflicts
- Verify all packages are available on PyPI
- Check Python version compatibility

### Docker build fails:
- Ensure Dockerfile path is correct: `./Docker/Dockerfile`
- Verify all files in Dockerfile COPY exist
- Check .dockerignore isn't excluding needed files

### Tests fail in CI but pass locally:
- Check Python version (CI uses 3.11, 3.12, 3.13)
- Verify environment variables are set
- Check for race conditions in async tests

### Docker Hub publish fails:
- Verify DOCKERHUB_USERNAME secret is correct
- Ensure DOCKERHUB_TOKEN hasn't expired
- Check Docker Hub repository exists

---

## 📚 Resources

- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [Docker Build Push Action](https://github.com/docker/build-push-action)
- [CodeQL Documentation](https://codeql.github.com/docs/)
- [Dependabot Documentation](https://docs.github.com/en/code-security/dependabot)
- [Trivy Scanner](https://aquasecurity.github.io/trivy/)
