from twitchAPI.twitch import Twitch
from mastodon import Mastodon
from atproto import Client
import time
import configparser
import random
import hvac
import boto3
import os
from dopplersdk import DopplerSDK

# Load the configuration file
config = configparser.ConfigParser()
config.read('/app/config/config.ini')

def get_secret(secret_name, source='aws'):
    if source == 'aws':
        # Create a Secrets Manager client
        session = boto3.session.Session()
        client = session.client(service_name='secretsmanager')

        get_secret_value_response = client.get_secret_value(SecretId=secret_name)
        secret = get_secret_value_response['SecretString']

    elif source == 'vault':
        vault_url = os.getenv('SECRETS_VAULT_URL', 'https://your-vault-server.com')
        vault_token = os.getenv('SECRETS_VAULT_TOKEN', 'your-vault-token')
        client = hvac.Client(url=vault_url, token=vault_token)
        secret = client.read(secret_name)['data']['data']
    
    elif source == 'doppler':
        # Doppler - uses DOPPLER_TOKEN from environment
        doppler_token = os.getenv('DOPPLER_TOKEN')
        if not doppler_token:
            raise ValueError("DOPPLER_TOKEN environment variable is required for Doppler")
        doppler = DopplerSDK()
        doppler.set_access_token(doppler_token)
        # secret_name should be the secret key in Doppler
        response = doppler.secrets.get(secret=secret_name)
        secret = response.value

    return secret

# Twitch API setup
twitch_client_id = os.getenv('TWITCH_CLIENT_ID')
twitch_client_secret = os.getenv('TWITCH_CLIENT_SECRET')
twitch_user_login = os.getenv('TWITCH_USER_LOGIN')

# Mastodon API setup
mastodon_client_id = os.getenv('MASTODON_CLIENT_ID')
mastodon_client_secret = os.getenv('MASTODON_CLIENT_SECRET')
mastodon_access_token = os.getenv('MASTODON_ACCESS_TOKEN')
mastodon_api_base_url = os.getenv('MASTODON_API_BASE_URL')
messages_file = os.getenv('MASTODON_MESSAGES_FILE', 'messages.txt')
end_messages_file = os.getenv('MASTODON_END_MESSAGES_FILE', 'end_messages.txt')
post_end_stream_message = os.getenv('MASTODON_POST_END_STREAM_MESSAGE', 'True') == 'True'

# Bluesky API setup
bluesky_handle = os.getenv('BLUESKY_HANDLE')
bluesky_app_password = os.getenv('BLUESKY_APP_PASSWORD')
bluesky_enable_posting = os.getenv('BLUESKY_ENABLE_POSTING', 'False') == 'True'

# Secret Manager setup
secret_manager = os.getenv('SECRET_MANAGER')
secrets_aws_twitch_secret_name = os.getenv('SECRETS_AWS_TWITCH_SECRET_NAME')
secrets_aws_mastodon_secret_name = os.getenv('SECRETS_AWS_MASTODON_SECRET_NAME')
secrets_aws_bluesky_secret_name = os.getenv('SECRETS_AWS_BLUESKY_SECRET_NAME')
secrets_vault_url = os.getenv('SECRETS_VAULT_URL')
secrets_vault_token = os.getenv('SECRETS_VAULT_TOKEN')
secrets_vault_twitch_secret_path = os.getenv('SECRETS_VAULT_TWITCH_SECRET_PATH')
secrets_vault_mastodon_secret_path = os.getenv('SECRETS_VAULT_MASTODON_SECRET_PATH')
secrets_vault_bluesky_secret_path = os.getenv('SECRETS_VAULT_BLUESKY_SECRET_PATH')

# Settings
post_interval = int(os.getenv('SETTINGS_POST_INTERVAL', '1'))
check_interval = int(os.getenv('SETTINGS_CHECK_INTERVAL', '5'))

# Load secrets from secret manager if configured
if secret_manager:
    if secret_manager.lower() == 'aws':
        twitch_secret = get_secret(secrets_aws_twitch_secret_name, source='aws')
        mastodon_secret = get_secret(secrets_aws_mastodon_secret_name, source='aws')
        bluesky_secret = get_secret(secrets_aws_bluesky_secret_name, source='aws')

        # Now replace the client id and secret from config file with the secrets from Secret Manager
        twitch_client_id = twitch_secret['client_id']
        twitch_client_secret = twitch_secret['client_secret']
        mastodon_client_id = mastodon_secret['client_id']
        mastodon_client_secret = mastodon_secret['client_secret']
        mastodon_access_token = mastodon_secret['access_token']
        bluesky_handle = bluesky_secret['handle']
        bluesky_app_password = bluesky_secret['app_password']

    elif secret_manager.lower() == 'vault':
        twitch_secret = get_secret(secrets_vault_twitch_secret_path, source='vault')
        mastodon_secret = get_secret(secrets_vault_mastodon_secret_path, source='vault')
        bluesky_secret = get_secret(secrets_vault_bluesky_secret_path, source='vault')

        # Now replace the client id and secret from config file with the secrets from Secret Manager
        twitch_client_id = twitch_secret['client_id']
        twitch_client_secret = twitch_secret['client_secret']
        mastodon_client_id = mastodon_secret['client_id']
        mastodon_client_secret = mastodon_secret['client_secret']
        mastodon_access_token = mastodon_secret['access_token']
        bluesky_handle = bluesky_secret['handle']
        bluesky_app_password = bluesky_secret['app_password']
    
    elif secret_manager.lower() == 'doppler':
        # Doppler - fetch individual secrets by key name
        twitch_client_id = get_secret('TWITCH_CLIENT_ID', source='doppler')
        twitch_client_secret = get_secret('TWITCH_CLIENT_SECRET', source='doppler')
        twitch_user_login = get_secret('TWITCH_USER_LOGIN', source='doppler')
        mastodon_client_id = get_secret('MASTODON_CLIENT_ID', source='doppler')
        mastodon_client_secret = get_secret('MASTODON_CLIENT_SECRET', source='doppler')
        mastodon_access_token = get_secret('MASTODON_ACCESS_TOKEN', source='doppler')
        mastodon_api_base_url = get_secret('MASTODON_API_BASE_URL', source='doppler')
        bluesky_handle = get_secret('BLUESKY_HANDLE', source='doppler')
        bluesky_app_password = get_secret('BLUESKY_APP_PASSWORD', source='doppler')

twitch = Twitch(twitch_client_id, twitch_client_secret)
twitch.authenticate_app([])
print("Successfully authenticated with Twitch API")

mastodon = Mastodon(
    client_id=mastodon_client_id,
    client_secret=mastodon_client_secret,
    access_token=mastodon_access_token,
    api_base_url=mastodon_api_base_url
)

print("Successfully authenticated with Mastodon API")

# Initialize the Bluesky client
bluesky_client = None
if bluesky_enable_posting and bluesky_handle and bluesky_app_password:
    bluesky_client = Client()
    bluesky_client.login(bluesky_handle, bluesky_app_password)
    print("Successfully authenticated with Bluesky API")

# Load the messages from the file
with open(messages_file, 'r') as file:
    messages = file.read().splitlines()

# Load the end of stream messages from the file
with open(end_messages_file, 'r') as file:
    end_messages = file.read().splitlines()

def is_user_live(user_login):
    user_info = twitch.get_users(logins=[user_login])
    user_id = user_info['data'][0]['id']
    streams = twitch.get_streams(user_id=user_id)
    live_streams = [stream for stream in streams['data'] if stream['type'] == 'live']
    return live_streams[0]['title'] if live_streams else None

def post_to_bluesky(message):
    if bluesky_enable_posting and bluesky_client:
        bluesky_client.send_post(text=message)
        print(f"Posted to Bluesky: {message}")

def post_message(message):
    mastodon.toot(message)
    print(f"Posted to Mastodon: {message}")

was_live = False

while True:
    print("Checking if user is live...")
    stream_title = is_user_live(twitch_user_login)
    
    if stream_title is not None:
        print(f"User is live, playing: {stream_title}")
        if not was_live:
            message = random.choice(messages).format(stream_title=stream_title, twitch_user_login=twitch_user_login)
            post_message(message)
            post_to_bluesky(message)
            was_live = True
        print(f"Waiting for {post_interval} hours before checking again...")
        time.sleep(post_interval * 60 * 60)  # Wait for specified hours before checking again
    else:
        if was_live and post_end_stream_message:  # If the stream was live in the last check, post the end-of-stream message
            message = random.choice(end_messages).format(twitch_user_login=twitch_user_login)
            post_message(message)
            post_to_bluesky(message)
            was_live = False
        print(f"User is not live, checking again in {check_interval} minutes...")
        time.sleep(check_interval * 60)  # Wait for specified minutes before checking again
