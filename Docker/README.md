# Stream Daemon - Docker Deployment

Run Stream Daemon in a Docker container for easy deployment, scalability, and consistency across environments.

## 🐳 Quick Start

```bash
cd Docker
docker-compose up -d
```

That's it! Stream Daemon is now running in the background.

## 📋 Prerequisites

- Docker installed ([Get Docker](https://docs.docker.com/get-docker/))
- Docker Compose installed ([Get Docker Compose](https://docs.docker.com/compose/install/))
- Stream Daemon configured (`.env` file or secrets manager)

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

2. **Edit docker-compose.yml:**
   ```yaml
   version: '3.8'
   services:
     stream-daemon:
       build: .
       restart: unless-stopped
       environment:
         # Secrets Manager
         SECRETS_SECRET_MANAGER: doppler
         DOPPLER_TOKEN: ${DOPPLER_TOKEN}
         
         # Platform Configuration
         TWITCH_ENABLE: 'True'
         TWITCH_USERNAME: your_username
         # ... other config
       volumes:
         - ./messages.txt:/app/messages.txt
         - ./end_messages.txt:/app/end_messages.txt
   ```

3. **Create .env file** (for docker-compose env vars):
   ```bash
   DOPPLER_TOKEN=dp.st.your_token_here
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
     --env-file ../.env \
     -v $(pwd)/messages.txt:/app/messages.txt \
     -v $(pwd)/end_messages.txt:/app/end_messages.txt \
     stream-daemon
   ```

3. **View logs:**
   ```bash
   docker logs -f stream-daemon
   ```

### Method 3: Docker with Doppler CLI

**Automatically inject secrets without storing DOPPLER_TOKEN:**

```bash
doppler run -- docker-compose up -d
```

Doppler CLI automatically provides all secrets to the container.

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
    
- Dockerize the script for easy deployment and scaling.
- Add support for more streaming platforms.

## Donations and Tips

If you would like to support the development of Twitch-and-toot, you can donate through the following links: [Donate](https://links.chiefgyk3d.com)

You can also tip the author with the following cryptocurrency addresses:

- Bitcoin: bc1q5grpa7ramcct4kjmwexfrh74dvjuw9wczn4w2f
- Monero: 85YxVz8Xd7sW1xSiyzUC5PNqSjYLYk4W8FMERVkvznR38jGTBEViWQSLCnzRYZjmxgUkUKGhxTt2JSFNpJuAqghQLhHgPS5
- PIVX: DS1CuBQkiidwwPhkfVfQAGUw4RTWPnBXVM
- Ethereum: 0x2a460d48ab404f191b14e9e0df05ee829cbf3733

## Authors

- ChiefGyk3D is the author of Twitch-and-toot
- [ChiefGyk3D's Mastodon Account](https://social.chiefgyk3d.com/@chiefgyk3d)
- ChatGPT, an AI developed by OpenAI, helped build about 80% of the Python version of Twitch-and-toot.
