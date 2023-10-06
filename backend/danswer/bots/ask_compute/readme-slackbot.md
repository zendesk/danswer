# Setup local test environment
- Overwrite the openapi endpoint to GEN_AI_ENDPOINT=https://ai-gateway.zende.sk/v1, GEN_AI_API_KEY=, GEN_AI_MODEL_VERSION=gpt-4-32k
- Run `docker compose -f docker-compose.dev.yml -p danswer-stack up -d --build --force-recreate` to build from local 
# Slack app setup
## Create the app via manifests
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
      - channels:join
      - app_mentions:read
      - chat:write
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
## Get an app level token for socket connection
## Install to the workspace and get the Bot User OAuth Token
## Restart the background container
`docker compose -f docker-compose.dev.yml -p danswer-stack up api_server background -d --build --force-recreate`
# Invite the app to the channel
`TODO: find out why I cannot add the bot in integration`
