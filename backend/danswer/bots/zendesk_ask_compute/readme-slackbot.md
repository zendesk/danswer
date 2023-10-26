# How to setup
## Setup local test environment
- Provide required environment variables in the `.env` file that docker compose can use
```sh
ZENDESK_ASK_COMPUTE_BOT_SLACK_APP_TOKEN="" # App token to initiate socket connections, in the format of "xapp-*"
ZENDESK_ASK_COMPUTE_BOT_SLACK_BOT_TOKEN="" # Bot OAuth token
ZENDESK_ASK_COMPUTE_BOT_OPENAI_KEY=""
ZENDESK_ASK_COMPUTE_BOT_CONFLUENCE_API=""
ZENDESK_ASK_COMPUTE_BOT_CONFLUENCE_USER=""
ZENDESK_ASK_COMPUTE_BOT_OPENAI_ENDPOINT="" # https://ai-gateway.zende.sk/v1/chat/completions
GEN_AI_MODEL_VERSION=""
GEN_AI_API_KEY=""
GEN_AI_ENDPOINT="" # https://ai-gateway.zende.sk/v1
ZENDESK_ASK_COMPUTE_BOT_LOG_LEVEL="debug"
LOG_LEVEL="debug"
```
- Run `docker compose -f docker-compose.dev.yml -p danswer-stack up -d --build --force-recreate` to build from local 
## Slack app setup
### Create the app via manifests
```yaml
display_information:
  name: DanswerBot
  description: I help answer questions!
features:
  bot_user:
    display_name: DanswerBot
    always_online: true
oauth_config:
  scopes:
    bot:
      - channels:history
      - channels:read
      - groups:history
      - groups:read
      - channels:join
      - app_mentions:read
      - chat:write
      - im:history
      - reactions:write
      - users:read
settings:
  event_subscriptions:
    bot_events:
      - app_mention
      - message.channels
      - message.groups
  interactivity:
    is_enabled: true
  org_deploy_enabled: false
  socket_mode_enabled: true
  token_rotation_enabled: false
```
### Get an app level token for socket connection
### Install to the workspace and get the Bot User OAuth Token
### Restart the background container
`docker compose -f docker-compose.dev.yml -p danswer-stack up api_server background -d --build --force-recreate`
## Invite the app to the channel
