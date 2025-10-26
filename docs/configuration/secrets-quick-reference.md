# Secrets Wizard - Quick Reference

## What Goes Where?

### Option 1: Doppler

| Item | Location | Example |
|------|----------|---------|
| API Keys | Doppler | `TWITCH_CLIENT_ID`, `YOUTUBE_API_KEY` |
| Tokens | Doppler | `MASTODON_ACCESS_TOKEN`, `LLM_GEMINI_API_KEY` |
| Webhooks | Doppler | `DISCORD_WEBHOOK_URL` |
| Passwords | Doppler | `BLUESKY_APP_PASSWORD`, `MATRIX_PASSWORD` |
| **Connection** | .env | `DOPPLER_TOKEN=dp.st.xxx` |
| Usernames | .env | `TWITCH_USERNAME=yourname` |
| URLs | .env | `MASTODON_API_BASE_URL=https://mastodon.social` |
| Settings | .env | `SETTINGS_CHECK_INTERVAL=5` |
| Enable Flags | .env | `TWITCH_ENABLE=True` |

**Run with:**
```bash
doppler run --project stream-daemon --config dev -- python3 stream-daemon.py
# OR
python3 stream-daemon.py  # if DOPPLER_TOKEN in .env
```

---

### Option 2: AWS Secrets Manager

| Item | Location | Example |
|------|----------|---------|
| API Keys | AWS | `stream-daemon/twitch`: `{"client_id": "...", "client_secret": "..."}` |
| Tokens | AWS | `stream-daemon/mastodon`: `{"access_token": "..."}` |
| Webhooks | AWS | `stream-daemon/discord`: `{"webhook_url": "..."}` |
| **Connection** | .env | `SECRETS_SECRET_MANAGER=aws` |
| Secret Names | .env | `SECRETS_AWS_TWITCH_SECRET_NAME=stream-daemon/twitch` |
| Region | .env | `AWS_REGION=us-east-1` |
| Usernames | .env | `TWITCH_USERNAME=yourname` |
| Settings | .env | `SETTINGS_CHECK_INTERVAL=5` |

**Run with:**
```bash
python3 stream-daemon.py
```

---

### Option 3: HashiCorp Vault

| Item | Location | Example |
|------|----------|---------|
| API Keys | Vault | `secret/stream-daemon/twitch`: `client_id`, `client_secret` |
| Tokens | Vault | `secret/stream-daemon/mastodon`: `access_token` |
| Webhooks | Vault | `secret/stream-daemon/discord`: `webhook_url` |
| **Connection** | .env | `SECRETS_SECRET_MANAGER=vault` |
| Vault URL | .env | `SECRETS_VAULT_URL=https://vault.example.com` |
| Vault Token | .env | `SECRETS_VAULT_TOKEN=s.abc123` |
| Secret Paths | .env | `SECRETS_VAULT_TWITCH_SECRET_PATH=secret/stream-daemon/twitch` |
| Usernames | .env | `TWITCH_USERNAME=yourname` |
| Settings | .env | `SETTINGS_CHECK_INTERVAL=5` |

**Run with:**
```bash
python3 stream-daemon.py
```

---

### Option 4: .env File Only

| Item | Location | Example |
|------|----------|---------|
| **EVERYTHING** | .env | All configs + all secrets |
| API Keys | .env | `TWITCH_CLIENT_ID=abc123` |
| Tokens | .env | `MASTODON_ACCESS_TOKEN=token123` |
| Webhooks | .env | `DISCORD_WEBHOOK_URL=https://...` |
| Usernames | .env | `TWITCH_USERNAME=yourname` |
| Settings | .env | `SETTINGS_CHECK_INTERVAL=5` |

**Run with:**
```bash
python3 stream-daemon.py
```

**⚠️ Security:** `.env` contains secrets - do NOT commit to git!

---

## Decision Matrix

Choose based on your needs:

| Use Case | Recommended | Why |
|----------|-------------|-----|
| Production deployment | Doppler or AWS | Secure, auditable, easy rotation |
| Multiple environments (dev/stg/prd) | Doppler | Built-in environment support |
| AWS-heavy infrastructure | AWS Secrets | Native IAM integration |
| Self-hosted/on-prem | Vault | Full control, enterprise features |
| Quick local development | .env file | Simple, no external dependencies |
| Team collaboration | Doppler or Vault | Centralized secrets, access control |
| CI/CD pipelines | Doppler or AWS | Easy integration, service tokens |
| Learning/testing | .env file | Get started fast |

---

## Common Questions

**Q: Can I commit .env to git if I use Doppler?**  
A: Technically yes (it only has config), but still recommended to keep in .gitignore for safety.

**Q: Do I need both .env and Doppler?**  
A: Yes! Doppler stores secrets, .env stores configs + connection info to Doppler.

**Q: Can I switch secrets managers later?**  
A: Yes! Just re-run `./scripts/create-secrets.sh` and choose a different option. The wizard loads existing values.

**Q: What if I chose .env but want to use Doppler now?**  
A: Re-run wizard, select Doppler. It will load values from .env, put secrets in Doppler, keep config in .env.

**Q: Can I use different environments with AWS/Vault?**  
A: Yes, but you need to manage it yourself (e.g., separate .env.dev, .env.prod files or different secret names).

**Q: How do I know which secrets are in which platform?**  
A: See [secrets-wizard-behavior.md](secrets-wizard-behavior.md) for complete lists.

---

## Troubleshooting

### "Stream Daemon can't find my secrets"

**Doppler:**
```bash
# Check secrets exist
doppler secrets --project stream-daemon --config dev

# Run with Doppler
doppler run --project stream-daemon --config dev -- python3 stream-daemon.py
```

**AWS:**
```bash
# Check .env has
SECRETS_SECRET_MANAGER=aws
AWS_REGION=us-east-1
SECRETS_AWS_TWITCH_SECRET_NAME=stream-daemon/twitch

# Check secrets exist
aws secretsmanager get-secret-value --secret-id stream-daemon/twitch --region us-east-1
```

**Vault:**
```bash
# Check .env has
SECRETS_SECRET_MANAGER=vault
SECRETS_VAULT_URL=http://...
SECRETS_VAULT_TOKEN=s.abc123

# Check secrets exist
vault kv get secret/stream-daemon/twitch
```

**.env file:**
```bash
# Check .env has everything
grep TWITCH_CLIENT_ID .env
grep TWITCH_CLIENT_SECRET .env
grep TWITCH_USERNAME .env
```

---

## See Also

- [Secrets Wizard Guide](secrets-wizard.md) - Full documentation
- [Config vs Secrets Behavior](secrets-wizard-behavior.md) - Detailed examples
- [Secrets Management](secrets.md) - Manual configuration
