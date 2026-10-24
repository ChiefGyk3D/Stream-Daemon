# Stream Daemon threat model

`stream-daemon.threat-dragon.json` is an OWASP Threat Dragon v2 model (STRIDE,
one diagram). Open it with the Threat Dragon desktop or web app: File > Open.

## What it covers
The daemon in this repository: polling Twitch, YouTube and Kick, building the
announcement (optional LLM, otherwise `messages.txt` templates), and posting to
Mastodon, Bluesky, Discord and Matrix. Social posting, LLM, config/secrets and
health-server code lives in the `hypeman-social` library (pinned 0.3.4); that
code was read from its v0.3.4 tag and is cited as such. Each threat cites
file:function. Mitigated means a control was seen in code or config; everything
else is Open. It is a record of one read, not an audit.

## Trust boundaries
- B1 operator host or container: the daemon, env/.env, message files.
- B2 streaming platform APIs: Twitch, YouTube, Kick responses are untrusted input (titles).
- B3 social platforms: receive public posts and credentials.
- B4 LLM endpoint: Ollama (plain http, operator host) or Gemini.
- B5 secrets backends: Doppler, AWS Secrets Manager, Vault, environment.
- B6 CI, release and supply chain: GYST workflows, PyPI, base image, registries.
- B7 health endpoint: optional, loopback by default.

## Open threats (no Critical or High)
Medium:
- Prompt injection: stream title is interpolated into the prompt unescaped (also recorded on the channel-owner actor).
- Model output is posted without review; the validate-retry flow ships flagged output.
- `@everyone` / `@here` can reach Discord (title or model text; no `allowed_mentions`).
- Discord webhook token appears in logged request-error text.
- Dockerfile downloads the SQLite tarball without a checksum; pip upgrade is unhashed.

Low: no record of exact prompt/output posted; cleartext remote Ollama; http Matrix
homeserver accepted; message-file tampering; credentials in plain env vars.

## UNVERIFIED items
None marked `UNVERIFIED:` in the model. Limits of the read:
- Signing, SBOM and provenance steps are in the GYST reusable workflows; only their
  inputs and the caller config here were checked.
- Library behavior was read from the v0.3.4 tag, not from an installed copy.
- Nothing was run against live services.
