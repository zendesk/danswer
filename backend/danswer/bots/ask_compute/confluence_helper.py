import requests
from requests.auth import HTTPBasicAuth
import json
import markdown
from tenacity import retry, wait_random_exponential, stop_after_attempt
import re

import danswer.bots.ask_compute.constants as constants
from danswer.bots.ask_compute.logger import setup_logger
logger = setup_logger("ask_compute_bot.confluence_helper", constants.LOG_LEVEL)

@retry(wait=wait_random_exponential(multiplier=1, max=40), stop=stop_after_attempt(3))
def upload_to_confluence(markdown_content, title, CONFLUENCE_SPACE_ID, CONFLUENCE_PARENT_PAGE_ID):
    """
    Uploads the given markdown content to Confluence.

    Parameters:
    - markdown_content (str): The markdown content to be uploaded.
    - title (str, optional): The title of the Confluence page.
    - CONFLUENCE_SPACE_ID (str, optional): The space ID where the page will be created.
    - CONFLUENCE_PARENT_PAGE_ID (str, optional): The parent ID of the page.

    Returns:
    - dict: The response from the Confluence API.
    """

    url = "https://zendesk.atlassian.net/wiki/api/v2/pages"
    auth = HTTPBasicAuth(constants.CONFLUENCE_USER, constants.CONFLUENCE_API)
    headers = {
      "Accept": "application/json",
      "Content-Type": "application/json"
    }

    html_content = markdown.markdown(markdown_content, extensions = ["tables"])

    payload = json.dumps({
      "spaceId": CONFLUENCE_SPACE_ID,
      "status": "current",
      "title": title,
      "parentId": CONFLUENCE_PARENT_PAGE_ID,
      "body": {
        "representation": "storage",
        "value": html_content
      }
    })

    logger.debug("Uploading the page to Confluence...")

    response = requests.request(
       "POST",
       url,
       data=payload,
       headers=headers,
       auth=auth
    )

    # Check the response
    if response.status_code == 200:
        logger.debug('Page created successfully.')
        logger.debug("Response from confluence: %s", json.dumps(json.loads(response.text), sort_keys=True, indent=4, separators=(",", ": ")))
    else:
        logger.error(f'Failed to create page. Status code: {response.status_code}.')
        logger.debug("Response from confluence: %s", json.dumps(json.loads(response.text), sort_keys=True, indent=4, separators=(",", ": ")))

    return response

def convert_summary_to_markdown(thread_summary: dict, messages: list, users: list, message_link: str) -> str:
    """
    Convert thread_summary to markdown
    """
    markdown_content = ""
    for section in constants.SUMMARY_SECTIONS:
        if section == "title":
            continue
        markdown_content += f"# {section.replace('_', ' ').capitalize()}  \n{thread_summary.get(section, 'NA')}  \n"

    # Attach the permalink of the original message
    markdown_content += f"#Link to the thread\n- [Click to go to the thread]({message_link})  \n"

    # Attach original thread messages to the doc
    markdown_content += "#Original thread messages\n"
    for msg in messages:
        markdown_content += f"<@{msg.get('user')}>:  \n{blockquote_string(msg.get('text'))}  \n  \n"

    # Update user_id to user_name
    id_name_mapping = {user.get("id"): user.get("name") for user in users}
    markdown_content = replace_user_ids_with_names(markdown_content, id_name_mapping)

    return markdown_content

def blockquote_string(s: str) -> str:
    """Blockquote each line of the given string."""
    return '\n'.join([f"> {line}" for line in s.split('\n')])


def replace_user_ids_with_names(s, mapping):
    '''
    Function to replace user id with user names
    '''
    # Regular expression pattern to match <@USER_ID>
    pattern = r'<@(\w+)>'
    
    # Replacement function
    def repl(match):
        user_id = match.group(1)
        return f"**<@{mapping.get(user_id, match.group(0))}>**"  # Use the original string if user_id not found in mapping
    
    return re.sub(pattern, repl, s)
