import json
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

import danswer.bots.ask_compute.constants as constants
import danswer.bots.ask_compute.block_builder as block_builder
import danswer.bots.ask_compute.confluence_helper as confluence_helper
from danswer.bots.ask_compute.gpt_helper import get_thread_summary

from danswer.bots.slack.constants import DISLIKE_BLOCK_ACTION_ID
from danswer.bots.slack.constants import LIKE_BLOCK_ACTION_ID
from danswer.bots.slack.handlers.handle_feedback import handle_slack_feedback
from danswer.bots.slack.handlers.handle_message import handle_message

from danswer.bots.ask_compute.logger import setup_logger
logger = setup_logger("ask_compute_bot", constants.LOG_LEVEL)

app = App(token=constants.SLACK_BOT_TOKEN, logger=logger)

def get_thread_messages(client: WebClient, view_metadata: dict, include_bot_msg: bool = False) -> list:
    """
    Get all messages from a message thread.

    Args:
        client (WebClient): Slack WebClient that communicates with Slack API
        view_metadata (dict): view metadata dictionary
        include_bot_msg (Bool): whether to include bot message or not, default to True

    Returns:
        list: List of messages
    """
    messages = []
    
    # Check if 'thread_ts' exists in metadata and if not, fetch the standalone message
    # TODO: logic to handle attachments here
    if not view_metadata.get("thread_ts"):
        try:
            # Fetch single message details
            response = client.conversations_history(
                channel=view_metadata["channel_id"],
                latest=view_metadata["ts"],
                inclusive=True,
                limit=1
            )
            messages = response["messages"]
        except SlackApiError as e:
            logger.error(f"Error fetching conversation history: {e}")
    else:
        # message is within a thread, fetch all reply messages in the thread
        try:
            response = client.conversations_replies(
                channel=view_metadata["channel_id"],
                ts=view_metadata["thread_ts"]
            )
            messages = response["messages"]
        except SlackApiError as e:
            logger.error(f"Error fetching thread: {e}")

    # Filter out bot messages if needed
    messages = messages if include_bot_msg else [msg for msg in messages if 'bot_id' not in msg and 'app_id' not in msg]

    return messages

def get_user_info(client: WebClient, user_id: str) -> dict:
    try:
        response = client.users_info(user = user_id)
        user = response['user']
        return user
    except SlackApiError as e:
        logger.error(f"Error fetching user info: {e.response['error']}")
        return None

def get_permalink(client: WebClient, channel_id: str, message_ts:str) -> str:
    """
    Get the permalink of a Slack message.
    """

    try:
        response = client.chat_getPermalink(channel=channel_id, message_ts=message_ts)
        return response["permalink"]
    except SlackApiError as e:
        logger.error(f"Error getting permalink: {e.response['error']}")
        return None

@app.shortcut("summarise-thread")
def open_summarise_thread_modal(ack, body, client, logger):
    # Acknowledge the shortcut request
    ack()

    # Store message metadata to pass down
    view_metadata = {
        "channel_id": body.get('channel', {}).get('id'),
        "ts": body.get('message', {}).get('ts'),
        "thread_ts": body.get('message', {}).get('thread_ts')
    }

    try:
        client.views_open(
                trigger_id=body["trigger_id"],
                view={
                    "type": "modal",
                    "callback_id": "summarise-thread-config",
                    "private_metadata": json.dumps(view_metadata),
                    "title": {
                        "type": "plain_text",
                        "text": "Summarise the thread"
                    },
                    "submit": {
                        "type": "plain_text",
                        "text": "Summarise"
                    },
                    "close": {
                        "type": "plain_text",
                        "text": "Cancel"
                    },
                    "blocks": block_builder.build_modal_config_blocks(body)
                }
            )
    except SlackApiError as e:
        logger.error(f"Slack API error: {str(e)}")
    except Exception as e:
        logger.error(f"Error opening modal: {e}")

@app.view("summarise-thread-config")
def open_summary_review_modal(ack, body, client, view, logger):
    # Retrieve metadata for the original message
    view_metadata = json.loads(view.get("private_metadata"))
    # Retrieve and validate user input
    user_input = view["state"]["values"]
    model_version = user_input["select_model_version"]["model_version"]["selected_option"]["value"]
    model_temperature = user_input["input_model_temperature"]["model_temperature"]["value"]
    # Store these inputs to view_metadata
    view_metadata["model_version"] = model_version
    view_metadata["model_temperature"] = model_temperature

    # TODO: add validation logic here
    # errors = {}
    # if type(model_temperature) != "number":
    #     errors["input_c"] = "The value must be longer than 5 characters"
    # if len(errors) > 0:
    #     ack(response_action="errors", errors=errors)
    #     return

    # Acknowledge the view_submission event with an interim view
    ack(response_action="update", view={
                    "type": "modal",
                    "close": {
                        "type": "plain_text",
                        "text": "Cancel",
                        "emoji": True
                    },
                    "title": {
                        "type": "plain_text",
                        "text": "AI Generated Summary",
                        "emoji": True
                    },
                    "blocks": block_builder.build_loading_blocks("Generating summary of the thread via OpenAI...")
                })

    # Send results to OpenAI for summary
    # Grab messages of the thread
    messages = get_thread_messages(client, view_metadata, False)
    res = get_thread_summary(messages, model_version, model_temperature)
    gpt_response = json.loads(res.get("choices", [{}])[0].get("message", {}).get("function_call", {}).get("arguments", {}))
    view_metadata["thread_summary"] = gpt_response

    client.views_update(
        view_id = view["id"],
        view = {
            "type": "modal",
            "private_metadata": json.dumps(view_metadata),
            "callback_id": "summary-submitted",
            "submit": {
                "type": "plain_text",
                "text": "Submit",
                "emoji": True
            },
            "close": {
                "type": "plain_text",
                "text": "Cancel",
                "emoji": True
            },
            "title": {
                "type": "plain_text",
                "text": "AI Generated Summary",
                "emoji": True
            },
            "blocks": block_builder.build_summary_review_blocks(gpt_response)
        }
    )

@app.action("regenerate-summary")
def regenerate_summary(ack, body, client, logger):
    ack()
    # Get view metadata
    view_metadata = json.loads(body.get("view", {}).get("private_metadata", ""))
    model_version = view_metadata.get("model_version") # TODO: Default version
    model_temperature = view_metadata.get("model_temperature") # TODO: Default temperature

    # Regenerate summary, insert an interim view
    client.views_update(
        view_id = body.get("view", {}).get("id", None),
        view = {
            "type": "modal",
            "close": {
                "type": "plain_text",
                "text": "Cancel",
                "emoji": True
            },
            "title": {
                "type": "plain_text",
                "text": "AI Generated Summary",
                "emoji": True
            },
            "blocks": block_builder.build_loading_blocks("Generating summary of the thread via OpenAI...")
        }
    )
    # Send results to OpenAI for summary
    # Grab messages of the thread
    messages = get_thread_messages(client, view_metadata, False)
    res = get_thread_summary(messages, model_version, model_temperature)
    gpt_response = json.loads(res.get("choices", [{}])[0].get("message", {}).get("function_call", {}).get("arguments", {}))
    view_metadata["thread_summary"] = gpt_response

    client.views_update(
        view_id = body.get("view", {}).get("id", None),
        view = {
            "type": "modal",
            "private_metadata": json.dumps(view_metadata),
            "submit": {
                "type": "plain_text",
                "text": "Submit",
                "emoji": True
            },
            "close": {
                "type": "plain_text",
                "text": "Cancel",
                "emoji": True
            },
            "title": {
                "type": "plain_text",
                "text": "AI Generated Summary",
                "emoji": True
            },
            "blocks": block_builder.build_summary_review_blocks(gpt_response)
        }
    )

@app.action("edit-summary")
def edit_summary(ack, body, client):
    ack()
    # Get view metadata
    view_metadata = json.loads(body.get("view", {}).get("private_metadata", ""))
    thread_summary = view_metadata["thread_summary"]

    # TODO: try views_push
    client.views_update(
        view_id = body.get("view", {}).get("id", None),
        view = {
            "type": "modal",
            "private_metadata": json.dumps(view_metadata),
            "callback_id": "summary-edited",
            "submit": {
                "type": "plain_text",
                "text": "Save",
                "emoji": True
            },
            "title": {
                "type": "plain_text",
                "text": "Edit Generated Summary",
                "emoji": True
            },
            "blocks": block_builder.build_summary_edit_blocks(thread_summary)
        }
    )

@app.view("summary-edited")
def update_summary_review_modal(ack, body, client, view, logger):

    view_metadata = json.loads(view.get("private_metadata"))
    # Retrieve updated summary sections
    user_input = view.get("state").get("values")
    updated_thread_summary = {
        "is_issue": view_metadata.get("thread_summary").get("is_issue")
    }
    for section in constants.SUMMARY_SECTIONS:
        updated_thread_summary[section] = user_input.get(section).get("input_value").get("value")
    view_metadata["thread_summary"] = updated_thread_summary

    ack(response_action = "update", view = {
        "type": "modal",
        "callback_id": "summary-submitted",
        "private_metadata": json.dumps(view_metadata),
        "submit": {
            "type": "plain_text",
            "text": "Submit",
            "emoji": True
        },
        "close": {
            "type": "plain_text",
            "text": "Cancel",
            "emoji": True
        },
        "title": {
            "type": "plain_text",
            "text": "AI Generated Summary",
            "emoji": True
        },
        "blocks": block_builder.build_summary_review_blocks(updated_thread_summary)
    })

@app.view("summary-submitted")
def upload_file_modal(ack, body, client, view, logger):

    view_metadata = json.loads(view.get("private_metadata"))
    thread_summary = view_metadata.get("thread_summary", {})

    ack(response_action = "update", view = {
        "type": "modal",
        "close": {
            "type": "plain_text",
            "text": "Cancel",
            "emoji": True
        },
        "title": {
            "type": "plain_text",
            "text": "Upload",
            "emoji": True
        },
        "blocks": block_builder.build_loading_blocks("Uploading content to confluence...")
    })

    # Grab messages of the thread to include in the document
    messages = get_thread_messages(client, view_metadata, False)
    users = [ get_user_info(client, user_id) for user_id in messages[0].get("reply_users", [])]
    message_link = get_permalink(client, view_metadata.get("channel_id"), messages[0].get("ts"))
    markdown_content = confluence_helper.convert_summary_to_markdown(thread_summary, messages, users, message_link)
    title = thread_summary.get("title")
    # Get info of users that participated in the discussion
    response = confluence_helper.upload_to_confluence(markdown_content, title, constants.CONFLUENCE_SPACE_ID, constants.CONFLUENCE_PARENT_PAGE_ID)
    response_text = json.loads(response.text)
    # Update response to the modal
    # TODO: provide option to retry if upload failed
    client.views_update(
        view_id = body.get("view", {}).get("id", None),
        view = {
            "type": "modal",
            "close": {
                "type": "plain_text",
                "text": "Cancel",
                "emoji": True
            },
            "title": {
                "type": "plain_text",
                "text": "Upload",
                "emoji": True
            },
            "blocks": block_builder.build_confluence_api_response_blocks(response)
        }
    )
    # Leave a message in the original thread to mark the thread as summarised
    client.chat_postMessage(
        channel = view_metadata.get("channel_id"),
        thread_ts = messages[0].get("thread_ts"),
        blocks = block_builder.build_final_message_blocks({"title": title, "link": f"{constants.CONFLUENCE_BASE_URL}{response_text.get('_links').get('webui')}"})
    )
    client.reactions_add(
            channel = view_metadata.get("channel_id"),
            timestamp = messages[0].get("ts"),
            name = "books"
    )

@app.event("app_mention")
def handle_app_mentions(body, say, logger):
    logger.info(body)

    # Get the text (content of the question), channel id and ts (timestamp) from the message event
    text = body["event"]["text"]
    channel_id = body["event"]["channel"]
    ts = body["event"]["ts"]

    # Get the bot user id to remove from the text
    bot_user_id = "A05TPVAGZ5H" # TODO: Get bot_id from body
    mention = f"<@{bot_user_id}>"

    # Remove the mention from the text
    question = text.replace(mention, "").strip()

    # If the question is empty, ignore it
    if not question:
        say(
            text = f"Please provide a question so I can answer.",
            channel = channel_id,
            thread_ts = ts
        )
    handle_message(
        msg = question,
        channel = channel_id,
        message_ts_to_respond_to = ts,
        client = app.client,
        logger = logger,
        should_respond_with_error_msgs = True
    )

@app.action(LIKE_BLOCK_ACTION_ID)
def handle_like_button(ack, body, client):
    ack()

    action_id = LIKE_BLOCK_ACTION_ID
    block_id = body.get("actions")[0].get("block_id")
    user_id = body.get("user").get("id")
    channel_id = body.get("channel").get("id")
    thread_ts = body.get("message").get("thread_ts")

    handle_slack_feedback(
        block_id = block_id,
        feedback_type = action_id,
        client = client,
        user_id_to_post_confirmation = user_id,
        channel_id_to_post_confirmation = channel_id,
        thread_ts_to_post_confirmation = thread_ts,
    )

@app.action(DISLIKE_BLOCK_ACTION_ID)
def handle_dislike_button(ack, body, client):
    ack()

    action_id = DISLIKE_BLOCK_ACTION_ID
    block_id = body.get("actions")[0].get("block_id")
    user_id = body.get("user").get("id")
    channel_id = body.get("channel").get("id")
    thread_ts = body.get("message").get("thread_ts")

    handle_slack_feedback(
        block_id = block_id,
        feedback_type = action_id,
        client = client,
        user_id_to_post_confirmation = user_id,
        channel_id_to_post_confirmation = channel_id,
        thread_ts_to_post_confirmation = thread_ts,
    )



if __name__ == "__main__":
    handler = SocketModeHandler(app, constants.SLACK_APP_TOKEN)
    handler.start()
