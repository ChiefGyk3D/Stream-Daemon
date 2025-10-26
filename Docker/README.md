# Stream Daemon - Docker Deployment

Run Stream Daemon in a Docker container for easy deployment, scalability, and consistency across environments.

## 🐳 Quick Start

```bash
cd Docker
cp docker-compose.example.yml docker-compose.yml
# Edit docker-compose.yml with your credentials
docker-compose up -d
```

That's it! Stream Daemon is now running in the background.

## 📋 Prerequisites

- Docker installed ([Get Docker](https://docs.docker.com/get-docker/))
- Docker Compose installed ([Get Docker Compose](https://docs.docker.com/compose/install/))
- API credentials for at least one streaming platform (Twitch, YouTube, or Kick)
- API credentials for at least one social platform (Mastodon, Bluesky, Discord, or Matrix)

## 🚀 Deployment Methods

### Method 1: Docker Compose (Recommended)

**Benefits:**
- ✅ Easy configuration with `docker-compose.yml`
- ✅ Automatic restart on failure
- ✅ Volume mounting for message files
- ✅ Environment variable management

**Steps:**

1. **Navigate to Docker directory:**
   ```bash
   cd Docker
   ```

2. **Copy example config:**
   ```bash
   cp docker-compose.example.yml docker-compose.yml
   ```

3. **Edit docker-compose.yml with your credentials:**
   
   Minimum required configuration:
   ```yaml
   version: '3.8'
   services:
     stream-daemon:
       build: .
       restart: unless-stopped
       environment:
         # Enable ONE streaming platform
         TWITCH_ENABLE: 'True'
         TWITCH_USERNAME: 'your_username'
         TWITCH_CLIENT_ID: 'your_client_id'
         TWITCH_CLIENT_SECRET: 'your_client_secret'
         
         # Enable ONE social platform
         MASTODON_ENABLE_POSTING: 'True'
         MASTODON_API_BASE_URL: 'https://mastodon.social'
         MASTODON_CLIENT_ID: 'your_client_id'
         MASTODON_CLIENT_SECRET: 'your_client_secret'
         MASTODON_ACCESS_TOKEN: 'your_access_token'
   ```

4. **Start the container:**
   ```bash
   docker-compose up -d
   ```

5. **View logs:**
   ```bash
   docker-compose logs -f
   ```

### Method 2: Manual Docker Build

**For more control or custom deployments:**

1. **Build the image:**
   ```bash
   docker build -t stream-daemon .
   ```

2. **Run the container:**
   ```bash
   docker run -d \
     --name stream-daemon \
     --restart unless-stopped \
     -e TWITCH_ENABLE=True \
     -e TWITCH_USERNAME=your_username \
     -e TWITCH_CLIENT_ID=your_client_id \
     -e TWITCH_CLIENT_SECRET=your_client_secret \
     -e MASTODON_ENABLE_POSTING=True \
     -e MASTODON_API_BASE_URL=https://mastodon.social \
     -e MASTODON_CLIENT_ID=your_client_id \
     -e MASTODON_CLIENT_SECRET=your_client_secret \
     -e MASTODON_ACCESS_TOKEN=your_access_token \
     stream-daemon
   ```

3. **View logs:**
   ```bash
   docker logs -f stream-daemon
   ```

### Method 3: Docker with Doppler CLI

**Automatically inject secrets without storing sensitive data in docker-compose.yml:**

```bash
doppler run -- docker-compose up -d
```

Doppler CLI automatically provides all secrets to the container.

## ⚙️ Configuration

### Environment Variables

Stream Daemon uses **pure environment variables** - no config files needed in Docker!

#### Streaming Platforms (Enable at least ONE)

**Twitch:**
```yaml
TWITCH_ENABLE: 'True'
TWITCH_USERNAME: 'your_username'
TWITCH_CLIENT_ID: 'your_client_id'
TWITCH_CLIENT_SECRET: 'your_client_secret'
```

**YouTube:**
```yaml
YOUTUBE_ENABLE: 'True'
YOUTUBE_CHANNEL_ID: 'your_channel_id'  # OR use username
YOUTUBE_API_KEY: 'your_api_key'
```

**Kick:**
```yaml
KICK_ENABLE: 'True'
KICK_USERNAME: 'your_username'
```

#### Social Platforms (Enable at least ONE)

**Mastodon:**
```yaml
MASTODON_ENABLE_POSTING: 'True'
MASTODON_API_BASE_URL: 'https://mastodon.social'
MASTODON_CLIENT_ID: 'your_client_id'
MASTODON_CLIENT_SECRET: 'your_client_secret'
MASTODON_ACCESS_TOKEN: 'your_access_token'
```

**Bluesky:**
```yaml
BLUESKY_ENABLE_POSTING: 'True'
BLUESKY_HANDLE: 'yourname.bsky.social'
BLUESKY_APP_PASSWORD: 'your_app_password'
```

**Discord:**
```yaml
DISCORD_ENABLE_POSTING: 'True'
DISCORD_WEBHOOK_URL: 'https://discord.com/api/webhooks/YOUR_WEBHOOK'
```

**Matrix:**
```yaml
MATRIX_ENABLE_POSTING: 'True'
MATRIX_HOMESERVER: 'https://matrix.org'
MATRIX_USERNAME: '@bot:matrix.org'
MATRIX_PASSWORD: 'your_password'
MATRIX_ROOM_ID: '!roomid:matrix.org'
```

#### AI / LLM (Optional)

**Google Gemini (Free API):**
```yaml
LLM_ENABLE: 'True'
LLM_PROVIDER: 'gemini'
LLM_GEMINI_API_KEY: 'your_api_key'
LLM_GEMINI_MODEL: 'gemini-2.0-flash-exp'
```

#### Settings

```yaml
SETTINGS_POST_INTERVAL: '60'    # Minutes to wait when stream is live
SETTINGS_CHECK_INTERVAL: '5'    # Minutes to wait when offline
```

### Custom Message Files

You can mount custom message files:

```yaml
volumes:
  - ./my_messages.txt:/app/messages.txt
  - ./my_end_messages.txt:/app/end_messages.txt
```

See [MESSAGES_FORMAT.md](../MESSAGES_FORMAT.md) for file format details.

## 🔐 Secrets Management

For production deployments, use a secrets manager instead of plaintext environment variables.

### Doppler (Recommended)

```yaml
environment:
  SECRET_MANAGER: doppler
  DOPPLER_TOKEN: ${DOPPLER_TOKEN}  # Set in .env file
```

See [DOPPLER_GUIDE.md](../DOPPLER_GUIDE.md) for complete setup.

### AWS Secrets Manager

```yaml
environment:
  SECRET_MANAGER: aws
  SECRETS_AWS_TWITCH_SECRET_NAME: twitch-api-keys
  SECRETS_AWS_MASTODON_SECRET_NAME: mastodon-api-keys
  # AWS credentials via IAM role or environment
```

### HashiCorp Vault

```yaml
environment:
  SECRET_MANAGER: vault
  SECRETS_VAULT_URL: https://vault.example.com
  SECRETS_VAULT_TOKEN: ${VAULT_TOKEN}
  SECRETS_VAULT_TWITCH_SECRET_PATH: secret/twitch
```

## 📊 Container Management

### View Logs
```bash
docker-compose logs -f
docker-compose logs -f --tail=100  # Last 100 lines
```

### Restart Container
```bash
docker-compose restart
```

### Stop Container
```bash
docker-compose down
```

### Rebuild After Code Changes
```bash
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

### Check Container Status
```bash
docker-compose ps
docker stats stream-daemon
```

## 🐛 Troubleshooting

### Container Won't Start

1. **Check logs:**
   ```bash
   docker-compose logs
   ```

2. **Verify environment variables:**
   ```bash
   docker-compose config
   ```

3. **Test build:**
   ```bash
   docker-compose build
   ```

### Authentication Errors

Make sure all required credentials are set in `docker-compose.yml`. Check logs for specific platform errors.

### Import Errors

The container includes all dependencies. If you see import errors, rebuild:
```bash
docker-compose build --no-cache
```

### Permission Issues

The container runs as the default user. Ensure mounted volumes have appropriate permissions.

## 🚢 Production Deployment

### Using Docker Hub / GHCR

1. **Pull pre-built image:**
   ```yaml
   services:
     stream-daemon:
       image: ghcr.io/chiefgyk3d/stream-daemon:latest
       # ... rest of config
   ```

2. **Auto-updates with Watchtower:**
   ```yaml
   services:
     stream-daemon:
       image: ghcr.io/chiefgyk3d/stream-daemon:latest
       # ... config
     
     watchtower:
       image: containrrr/watchtower
       volumes:
         - /var/run/docker.sock:/var/run/docker.sock
       command: --interval 86400  # Check daily
   ```

### Health Checks

Add health check to docker-compose.yml:
```yaml
services:
  stream-daemon:
    # ... config
    healthcheck:
      test: ["CMD", "pgrep", "-f", "stream-daemon"]
      interval: 60s
      timeout: 10s
      retries: 3
```

## 📝 License

MIT License - See [LICENSE.md](../LICENSE.md)

## 🤝 Support

- 📖 Documentation: See main [README.md](../README.md)
- 🐛 Issues: [GitHub Issues](https://github.com/ChiefGyk3D/Stream-Daemon/issues)
- 💬 Discussions: [GitHub Discussions](https://github.com/ChiefGyk3D/Stream-Daemon/discussions)

## ⚙️ Configuration

### Environment Variables

Stream Daemon uses **pure environment variables** - no config files needed in Docker!

Here's an example structure for the config.ini file:

```ini
[Twitch]
client_id = YOUR_TWITCH_CLIENT_ID
client_secret = YOUR_TWITCH_CLIENT_SECRET
user_login = YOUR_TWITCH_USERNAME

[Mastodon]
app_name = YOUR_APP_NAME
api_base_url = YOUR_INSTANCE_URL
client_id = YOUR_CLIENT_ID
client_secret = YOUR_CLIENT_SECRET
access_token = YOUR_ACCESS_TOKEN
messages_file = MESSAGES_FILE_PATH
end_messages_file = END_MESSAGES_FILE_PATH
post_end_stream_message = BOOLEAN_VALUE

[Secrets]
secret_manager = YOUR_SECRET_MANAGER_TYPE 
aws_twitch_secret_name = YOUR_TWITCH_SECRET_NAME_IN_AWS_SECRETS_MANAGER
aws_mastodon_secret_name = YOUR_MASTODON_SECRET_NAME_IN_AWS_SECRETS_MANAGER
vault_url = YOUR_VAULT_URL
vault_token = YOUR_VAULT_TOKEN
vault_twitch_secret_path = YOUR_TWITCH_SECRET_PATH_IN_VAULT
vault_mastodon_secret_path = YOUR_MASTODON_SECRET_PATH_IN_VAULT

[Settings]
post_interval = YOUR_PREFERRED_POST_INTERVAL_IN_HOURS
check_interval = YOUR_PREFERRED_CHECK_INTERVAL_IN_MINUTES
```
Please note, the config.ini should be modified to match your needs.

### Caution

While the above example demonstrates how to configure the bot with secrets directly placed into the config.ini file, this is not a recommended practice for production environments. It is highly suggested to use services like HashiCorp Vault or AWS Secrets Manager to handle secrets more securely.

If you still prefer to put your secrets into config.ini, ensure that this file is appropriately secured and never committed into a public repository.

The Twitch-Mastodon Bot supports the use of both AWS Secrets Manager and HashiCorp Vault. Please see the following sections for how to configure them.

## AWS Secrets Manager Integration

The script supports optional integration with AWS Secrets Manager for secure storage and retrieval of Twitch and Mastodon API keys. To use this feature, store the credentials as secrets in AWS Secrets Manager and provide the secret names in the config.ini file.

**Please note that this feature is still in testing and any issues should be reported.**

## HashiCorp Vault Integration

The script also supports optional integration with HashiCorp Vault for secure storage and retrieval of Twitch and Mastodon API keys. To use this feature, store the credentials in Vault and provide the necessary Vault information in the config.ini file.

**Please note that this feature is still in testing and any issues should be reported.**

## Future plans
    
- Add support for more streaming platforms.

## Donations and Tips

If you would like to support the development of Stream-Daemon, you can donate through the following links: [Patreon](https://patreon.com/chiefgyk3d?utm_medium=unknown&utm_source=join_link&utm_campaign=creatorshare_creator&utm_content=copyLink)
[StreamElements](https://streamelements.com/chiefgyk3d/tip)


### Cryptocurrency Tips

<table>
   <tr>
      <td align="center">
         <img src="https://cdn.jsdelivr.net/gh/simple-icons/simple-icons/icons/bitcoin.svg" width="32" height="32" alt="Bitcoin"/><br/>
         <b>Bitcoin</b><br/>
         <code>bc1qztdzcy2wyavj2tsuandu4p0tcklzttvdnzalla</code>
      </td>
      <td align="center">
         <img src="https://cdn.jsdelivr.net/gh/simple-icons/simple-icons/icons/monero.svg" width="32" height="32" alt="Monero"/><br/>
         <b>Monero</b><br/>
         <code>84Y34QubRwQYK2HNviezeH9r6aRcPvgWmKtDkN3EwiuVbp6sNLhm9ffRgs6BA9X1n9jY7wEN16ZEpiEngZbecXseUrW8SeQ</code>
      </td>
      <td align="center">
         <img src="https://cdn.jsdelivr.net/gh/simple-icons/simple-icons/icons/ethereum.svg" width="32" height="32" alt="Ethereum"/><br/>
         <b>Ethereum</b><br/>
         <code>0x554f18cfB684889c3A60219BDBE7b050C39335ED</code>
      </td>
   </tr>
</table>

## Authors


<div align="center">

Made with ❤️ by [ChiefGyk3D](https://github.com/ChiefGyk3D)

## Author & Socials

<table>
   <tr>
      <td align="center"><a href="https://social.chiefgyk3d.com/@chiefgyk3d" title="Mastodon"><img src="https://cdn.jsdelivr.net/gh/simple-icons/simple-icons/icons/mastodon.svg" width="32" height="32" alt="Mastodon"/></a></td>
      <td align="center"><a href="https://bsky.app/profile/chiefgyk3d.com" title="Bluesky"><img src="https://cdn.jsdelivr.net/gh/simple-icons/simple-icons/icons/bluesky.svg" width="32" height="32" alt="Bluesky"/></a></td>
      <td align="center"><a href="http://twitch.tv/chiefgyk3d" title="Twitch"><img src="https://cdn.jsdelivr.net/gh/simple-icons/simple-icons/icons/twitch.svg" width="32" height="32" alt="Twitch"/></a></td>
      <td align="center"><a href="https://www.youtube.com/channel/UCvFY4KyqVBuYd7JAl3NRyiQ" title="YouTube"><img src="https://cdn.jsdelivr.net/gh/simple-icons/simple-icons/icons/youtube.svg" width="32" height="32" alt="YouTube"/></a></td>
      <td align="center"><a href="https://kick.com/chiefgyk3d" title="Kick"><img src="https://cdn.jsdelivr.net/gh/simple-icons/simple-icons/icons/kick.svg" width="32" height="32" alt="Kick"/></a></td>
      <td align="center"><a href="https://www.tiktok.com/@chiefgyk3d" title="TikTok"><img src="https://cdn.jsdelivr.net/gh/simple-icons/simple-icons/icons/tiktok.svg" width="32" height="32" alt="TikTok"/></a></td>
      <td align="center"><a href="https://discord.chiefgyk3d.com" title="Discord"><img src="https://cdn.jsdelivr.net/gh/simple-icons/simple-icons/icons/discord.svg" width="32" height="32" alt="Discord"/></a></td>
      <td align="center"><a href="https://matrix-invite.chiefgyk3d.com" title="Matrix"><img src="https://cdn.jsdelivr.net/gh/simple-icons/simple-icons/icons/matrix.svg" width="32" height="32" alt="Matrix"/></a></td>
   </tr>
   <tr>
      <td align="center">Mastodon</td>
      <td align="center">Bluesky</td>
      <td align="center">Twitch</td>
      <td align="center">YouTube</td>
      <td align="center">Kick</td>
      <td align="center">TikTok</td>
      <td align="center">Discord</td>
      <td align="center">Matrix</td>
   </tr>
</table>

<sub>ChiefGyk3D is the author of Stream Daemon (formerly Twitch and Toot)</sub>

</div>