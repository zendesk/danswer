import json

from slack_sdk.models.blocks import ActionsBlock
from slack_sdk.models.blocks import Block
from slack_sdk.models.blocks import ConfirmObject
from slack_sdk.models.blocks import DividerBlock
from slack_sdk.models.blocks import InputBlock
from slack_sdk.models.blocks import Option
from slack_sdk.models.blocks import PlainTextInputElement
from slack_sdk.models.blocks import PlainTextObject
from slack_sdk.models.blocks import SectionBlock
from slack_sdk.models.blocks import TextObject
from slack_sdk.models.blocks.block_elements import ButtonElement
from slack_sdk.models.blocks.block_elements import NumberInputElement
from slack_sdk.models.blocks.block_elements import StaticSelectElement

import danswer.bots.ask_compute.constants as constants
from danswer.bots.ask_compute.logger import setup_logger
logger = setup_logger("ask_compute_bot.block_builder", constants.LOG_LEVEL)


def convert_blocks_to_dict(blocks: list[Block]) -> list[dict]:
    """
    Utility function to convert an arry of Block objects to JSON-compatible, Slack-API-valid dictionaries
    """
    return [block.to_dict() for block in blocks]

def build_modal_config_blocks(block_data: dict) -> list[dict]:
    return convert_blocks_to_dict([
        SectionBlock(
            text = TextObject(type = "mrkdwn", text = f"*Hi <@{block_data.get('user', {}).get('id', None)}>! Please configure:*")
        ),
        DividerBlock(),
        SectionBlock(
            text = TextObject(type = "mrkdwn", text = ":robot_face: *GPT Model*\nChoose from supported gpt models"),
            block_id = "select_model_version",
            accessory = StaticSelectElement(
                action_id = "model_version",
                placeholder = TextObject(type = "plain_text", text = "Choose model"),
                options = [
                    Option(text = TextObject(type = "plain_text", text = "GPT-4"), value = "gpt-4"),
                    Option(text = TextObject(type = "plain_text", text = "GPT-4-32K"), value = "gpt-4-32k"),
                    Option(text = TextObject(type = "plain_text", text = "GPT-3.5"), value = "gpt-3.5-turbo")
                ],
                initial_option = Option(text = TextObject(type = "plain_text", text = "GPT-4"), value = "gpt-4")
            )
        ),
        InputBlock(
            block_id = "input_model_temperature",
            label = TextObject(type = "plain_text", text = ":robot_face: Model temperature"),
            hint = TextObject(type = "plain_text", text = "Model sampling temperature, between 0.0 and 1.0.\nHigher values make the output more random, while lower values give more deterministic result."),
            element = NumberInputElement(
                action_id = "model_temperature",
                is_decimal_allowed = True,
                initial_value = 0.5,
                min_value = 0.0,
                max_value = 1.0
            )
        ),
        SectionBlock(
            text = TextObject(type = "mrkdwn", text = ":man-getting-massage: *Place holder*\n  TBD"),
            accessory = StaticSelectElement(
                placeholder = TextObject(type = "plain_text", text = "Choose an option"),
                options = [Option(value = "option-1", text = TextObject(type = "plain_text", text = "Option 1"))]
            )
        )
    ])

def build_loading_blocks(text) -> list[dict]:
    return convert_blocks_to_dict([
        SectionBlock(text = TextObject(type = "mrkdwn", text = f":spinner: {text}"))
    ])

def build_summary_review_blocks(block_data: dict) -> list[dict]:
    if not block_data.get("is_issue", False):
        return convert_blocks_to_dict([
            SectionBlock(text = TextObject(type = "mrkdwn", text = "The thread does not include an issue or a question.")),
        ])
    section_blocks = [SectionBlock(text = TextObject(type = "mrkdwn", text = f"*{section.replace('_', ' ').capitalize()}*\n{block_data.get(section, None)}")) for section in constants.SUMMARY_SECTIONS]
    blocks = convert_blocks_to_dict([
        SectionBlock(text = TextObject(type = "mrkdwn", text = "Please review generated summary before submitting to a knowledge base.")),
        DividerBlock()
    ] + section_blocks + [
        ActionsBlock(
            block_id = "summary-review-actions",
            elements = [
                ButtonElement(
                    action_id = "edit-summary",
                    text = TextObject(type = "plain_text", text = "Edit"),
                    style = "primary",
                    value = "clicked"
                ),
                ButtonElement(
                    action_id = "regenerate-summary",
                    text = TextObject(type = "plain_text", text = "Regenerate"),
                    style = "danger",
                    value = "clicked",
                    confirm = ConfirmObject(
                        title = "Are you sure?",
                        text = "Press yes will regenerate the summary with OpenAI."
                    )
                )
            ]
        )
    ])
    logger.debug("Built blocks payload %s", json.dumps(blocks))
    return blocks

def build_summary_edit_blocks(block_data: dict) -> list[dict]:
    blocks = convert_blocks_to_dict([
        InputBlock(
            block_id = section.lower(),
            label = PlainTextObject(text = section.replace('_', ' ').capitalize()),
            element = PlainTextInputElement(
                multiline = True,
                action_id = "input_value",
                initial_value = block_data.get(section, None)
            )
        ) for section in constants.SUMMARY_SECTIONS
    ])
    logger.debug("Built blocks payload %s", json.dumps(blocks))
    return blocks

def build_confluence_api_response_blocks(block_data: dict) -> list[dict]:
    blocks = []
    response = json.loads(block_data.text)
    if block_data.status_code == 200:
        blocks += [
            SectionBlock(type = "mrkdwn", text = "✅ *Summary uploaded to Confluence.*"),
            SectionBlock(type = "mrkdwn", text = f"Link to the page: <{constants.CONFLUENCE_BASE_URL}{response.get('_links').get('webui')}>")
        ]
    else:
        blocks += [
            SectionBlock(type = "mrkdwn", text = "❌ *Failed to upload to Confluence.*"),
            SectionBlock(type = "mrkdwn", text = f"```{json.dumps(response, sort_keys=True, indent=4, separators=(',', ': '))}```")
        ]
    return convert_blocks_to_dict(blocks)

def build_final_message_blocks(block_data: dict) -> list[dict]:
    """
    Build the final message to post to the thread to confirm it has been summarised
    """
    return [
        SectionBlock(type = "mrkdwn", text = " "),
        SectionBlock(type = "mrkdwn", text = "🎉"),
        SectionBlock(type = "mrkdwn", text = "*The content of this thread has been compiled into a technical summary and uploaded to our knowledge base.*"),
        SectionBlock(type = "mrkdwn", text = f"Link to the technical summary: <{block_data.get('link')}|{block_data.get('title')}>"),
    ]
