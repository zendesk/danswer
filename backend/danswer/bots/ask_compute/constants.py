import os

SLACK_BOT_TOKEN=os.environ.get("ASK_COMPUTE_BOT_SLACK_BOT_TOKEN")
OPENAI_KEY = os.environ.get("ASK_COMPUTE_BOT_OPENAI_KEY")
OPENAI_ENDPOINT = "https://ai-gateway.zende.sk/v1/chat/completions"
SLACK_APP_TOKEN = os.environ.get("ASK_COMPUTE_BOT_SLACK_APP_TOKEN")
CONFLUENCE_API = os.environ.get("ASK_COMPUTE_BOT_CONFLUENCE_API")
CONFLUENCE_USER = os.environ.get("ASK_COMPUTE_BOT_CONFLUENCE_USER")

LOG_LEVEL = os.environ.get("ASK_COMPUTE_BOT_LOG_LEVEL", "info")

SUMMARY_SECTIONS = ["title", "description", "discussion_summary", "identified_solutions", "takeways", "references"]
# CONFLUENCE_SPACE_ID="127696897" # PaaS
# CONFLUENCE_PARENT_PAGE_ID="5919277243" # Ask-compute Knowledge Base
CONFLUENCE_SPACE_ID="5871600340" # TODO: dev only, yuming's personal space
CONFLUENCE_PARENT_PAGE_ID="5920000102" # TODO: dev only
CONFLUENCE_BASE_URL="https://zendesk.atlassian.net/wiki"
