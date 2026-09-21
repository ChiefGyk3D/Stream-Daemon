# GitHub Actions Workflows

Three thin callers. The jobs themselves live in
[ChiefGyk3D/git-your-ship-together](https://github.com/ChiefGyk3D/git-your-ship-together),
shared with Typo Sniper, Star Daemon and Boon Tube Daemon, so a pipeline fix or
a new scan step lands once. Each file here says only what is specific to
Stream Daemon: Python versions, the test command, the Dockerfile path, the
Doppler project.

| Workflow | Triggers | Calls | What it does |
|---|---|---|---|
| `ci.yml` | push to main/develop/copilot/**, PRs, manual | `python-ci.yml` | Lint (ruff), tests on Python 3.10–3.14 with coverage to Codecov, Docker build with an import check, one `CI green` gate job for branch protection |
| `release.yml` | push to main, `v*.*.*` tags, PRs, manual | `python-docker-release.yml` | Build and test on every PR; on main and tags publish a multi-arch (amd64 + arm64) image to `ghcr.io/chiefgyk3d/stream-daemon` and Docker Hub, signed with cosign, with a syft SBOM attached and SLSA provenance recorded; Trivy scan to the Security tab |
| `security.yml` | push to main/develop, PRs, weekly, manual | `security.yml` | CodeQL, gitleaks over the full history, pip-audit, dependency review on PRs, Snyk |

## Secrets: Doppler, not GitHub

No secret is stored in this repository's GitHub secrets. A job authenticates
to Doppler with a short-lived token minted from its own GitHub OIDC identity
(a Doppler Service Account Identity) and reads the `ci` config of the
`stream-daemon` project, which holds only what the pipelines need:

| Name | Used by |
|---|---|
| `DOCKERHUB_USERNAME`, `DOCKERHUB_TOKEN` | `release.yml`, Docker Hub publish |
| `CODECOV_TOKEN` | `ci.yml`, coverage upload |
| `SNYK_TOKEN` | `security.yml`, Snyk |

The one per-repository setting is the **repository variable**
`DOPPLER_IDENTITY_ID` (Settings → Secrets and variables → Actions →
Variables), the UUID of the identity. It is an identifier, not a secret.

Before that is set the pipelines still run: Docker Hub publish and Codecov
upload skip with a notice, Snyk warns and skips, GHCR publishing works
regardless because it uses the job's own `GITHUB_TOKEN`.

The setup runbook, the fallback path (a Doppler Service Token as the single
GitHub secret `DOPPLER_TOKEN`), and every input are documented in the
git-your-ship-together README.

## Verifying a published image

```sh
cosign verify ghcr.io/chiefgyk3d/stream-daemon:latest \
  --certificate-identity-regexp '^https://github.com/ChiefGyk3D/git-your-ship-together/' \
  --certificate-oidc-issuer https://token.actions.githubusercontent.com

gh attestation verify oci://ghcr.io/chiefgyk3d/stream-daemon:latest --owner ChiefGyk3D
```

The SBOM is also attached to every run of `release.yml` as the
`sbom.spdx.json` artifact.

## Image tags

- `latest` (main branch only)
- `1.2.3`, `1.2`, `1` (from `v1.2.3` tags)
- `main`, `sha-<short>` (branch and commit)
- `pr-123` (pull requests; built and tested, never pushed)

## Dependabot

`dependabot.yml` opens weekly PRs for Python packages, the Docker base image
and GitHub Actions.

## Status badges

```markdown
[![CI](https://github.com/ChiefGyk3D/Stream-Daemon/actions/workflows/ci.yml/badge.svg)](https://github.com/ChiefGyk3D/Stream-Daemon/actions/workflows/ci.yml)
[![Release](https://github.com/ChiefGyk3D/Stream-Daemon/actions/workflows/release.yml/badge.svg)](https://github.com/ChiefGyk3D/Stream-Daemon/actions/workflows/release.yml)
[![Security](https://github.com/ChiefGyk3D/Stream-Daemon/actions/workflows/security.yml/badge.svg)](https://github.com/ChiefGyk3D/Stream-Daemon/actions/workflows/security.yml)
```

## What changed in the migration

- `ci-tests.yml`, `docker-build-publish.yml`, `codeql-analysis.yml`,
  `dependency-review.yml`, `dependency-scan.yml` and `snyk-security.yml` were
  replaced by the three callers above.
- Bandit and `safety check` were dropped: `safety check` is deprecated
  upstream and needs an account, and both ran as advisory-only. CodeQL covers
  SAST and pip-audit covers the advisory database.
- pip-audit gates. Ruff lint stays advisory (`lint-continue-on-error`) until
  the tree is clean; delete that line to make it gate.
- `.gitleaks.toml` allowlists the documented placeholders (`YOUR_*`,
  `AIzaSyABC123XYZ789`, counting-digit Discord ids) and the scan reports that
  were once committed, so gitleaks fails only on a real credential.
- Images are now signed, carry an SBOM and provenance, and the multi-arch
  build uses the GitHub Actions cache instead of `no-cache: true`.
