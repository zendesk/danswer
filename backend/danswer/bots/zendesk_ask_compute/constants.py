import os


def fetch_env_variable(var_name: str) -> str:
    value = os.environ.get(var_name)
    if value is None:
        if var_name == "ZENDESK_ASK_COMPUTE_BOT_LOG_LEVEL":
            return "info"
        raise ValueError(f"{var_name} environment variable is required")
    return value


SLACK_BOT_TOKEN = fetch_env_variable("ZENDESK_ASK_COMPUTE_BOT_SLACK_BOT_TOKEN")
SLACK_APP_TOKEN = fetch_env_variable("ZENDESK_ASK_COMPUTE_BOT_SLACK_APP_TOKEN")
OPENAI_ENDPOINT = fetch_env_variable("ZENDESK_ASK_COMPUTE_BOT_OPENAI_ENDPOINT")
OPENAI_KEY = fetch_env_variable("ZENDESK_ASK_COMPUTE_BOT_OPENAI_KEY")
CONFLUENCE_API = fetch_env_variable("ZENDESK_ASK_COMPUTE_BOT_CONFLUENCE_API")
CONFLUENCE_USER = fetch_env_variable("ZENDESK_ASK_COMPUTE_BOT_CONFLUENCE_USER")

LOG_LEVEL = fetch_env_variable("ZENDESK_ASK_COMPUTE_BOT_LOG_LEVEL")

# Value checks

if SLACK_BOT_TOKEN is None:
    raise ValueError(
        "ZENDESK_ASK_COMPUTE_BOT_SLACK_BOT_TOKEN environment variable is required"
    )
if SLACK_APP_TOKEN is None:
    raise ValueError(
        "ZENDESK_ASK_COMPUTE_BOT_SLACK_APP_TOKEN environment variable is required"
    )
if OPENAI_ENDPOINT is None:
    raise ValueError(
        "ZENDESK_ASK_COMPUTE_BOT_OPENAI_ENDPOINT environment variable is required"
    )
if OPENAI_KEY is None:
    raise ValueError(
        "ZENDESK_ASK_COMPUTE_BOT_OPENAI_KEY environment variable is required"
    )
if CONFLUENCE_API is None:
    raise ValueError(
        "ZENDESK_ASK_COMPUTE_BOT_CONFLUENCE_API environment variable is required"
    )
if CONFLUENCE_USER is None:
    raise ValueError(
        "ZENDESK_ASK_COMPUTE_BOT_CONFLUENCE_USER environment variable is required"
    )

SUMMARY_SECTIONS = [
    "title",
    "description",
    "discussion_summary",
    "identified_solutions",
    "takeways",
    "references",
]
# CONFLUENCE_SPACE_ID="127696897" # PaaS
# CONFLUENCE_PARENT_PAGE_ID="5919277243" # Ask-compute Knowledge Base
CONFLUENCE_SPACE_ID = "5871600340"  # TODO: dev only, yuming's personal space
CONFLUENCE_PARENT_PAGE_ID = "5920000102"  # TODO: dev only
CONFLUENCE_BASE_URL = "https://zendesk.atlassian.net/wiki"

MODULE_NAME = "zendesk_ask_compute_bot"
