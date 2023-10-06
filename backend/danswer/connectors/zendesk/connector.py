import time
from collections.abc import Callable
from typing import Any

from danswer.configs.app_configs import INDEX_BATCH_SIZE
from danswer.configs.constants import DocumentSource
from danswer.connectors.interfaces import GenerateDocumentsOutput
from danswer.connectors.interfaces import LoadConnector
from danswer.connectors.interfaces import PollConnector
from danswer.connectors.interfaces import SecondsSinceUnixEpoch
from danswer.connectors.models import ConnectorMissingCredentialError
from danswer.connectors.models import Document
from danswer.connectors.models import Section
from danswer.connectors.zendesk.client import ZendeskApiClient
from danswer.utils.logger import setup_logger
from danswer.utils.text_processing import parse_html_page_basic

logger = setup_logger()


class ZendeskConnector(LoadConnector, PollConnector):

    def __init__(
            self,
            batch_size: int = INDEX_BATCH_SIZE,
    ) -> None:
        self.batch_size = batch_size
        self.zendesk_client: ZendeskApiClient | None = None

    def load_credentials(self, credentials: dict[str, Any]) -> dict[str, Any] | None:
        self.zendesk_client = ZendeskApiClient(
            base_url=credentials["zendesk_base_url"],
            username=credentials["zendesk_username"],
            password=credentials["zendesk_password"],
        )
        return None

    @staticmethod
    def _get_incremental_export(
            zendesk_client: ZendeskApiClient,
            endpoint: str,
            key: str,
            transformer: Callable[[dict], Document],
            start: SecondsSinceUnixEpoch,
    ) -> tuple[list[Document], SecondsSinceUnixEpoch]:
        doc_batch: list[Document] = []
        params = {
            "start_time": "{:.0f}".format(start)
        }

        batch = zendesk_client.get(endpoint, params=params)
        logger.info(
            "Retrieved {} from incremental {} export, start_time={}, end_time={}".format(batch.get("count", 0), key,
                                                                                         start,
                                                                                         batch.get("end_time", 0)))
        items = batch.get(key)
        if not items:
            raise RuntimeError("No {} key found in incremental export response".format(key))
        for item in items:
            if item.get("draft", False) or len((item.get("body", "") or "").strip()) == 0:
                continue
            doc_batch.append(transformer(item))

        return doc_batch, SecondsSinceUnixEpoch(batch["end_time"])

    @staticmethod
    def _article_to_document(
            article: dict[str, Any],
    ) -> Document:
        text = article.get("title", "") + "\n" + parse_html_page_basic(article.get("body", ""))
        link = str(article.get("html_url"))
        return Document(
            id="article:" + str(article.get("id")),
            sections=[Section(link=link, text=text)],
            source=DocumentSource.ZENDESK,
            semantic_identifier="Zendesk Help Centre: {}".format(article.get("title")),
            metadata={"type": "article", "updated_at": str(article.get("updated_at"))},
        )

    def load_from_state(self) -> GenerateDocumentsOutput:
        if self.zendesk_client is None:
            raise ConnectorMissingCredentialError("Zendesk")

        return self.poll_source(None, None)

    def poll_source(
            self, start: SecondsSinceUnixEpoch | None, end: SecondsSinceUnixEpoch | None
    ) -> GenerateDocumentsOutput:
        if self.zendesk_client is None:
            raise ConnectorMissingCredentialError("Zendesk")
        if start is None:
            start = SecondsSinceUnixEpoch(0)
        while True:
            doc_batch, end_time = self._get_incremental_export(
                zendesk_client=self.zendesk_client,
                endpoint="/api/v2/help_center/incremental/articles",
                key="articles",
                transformer=self._article_to_document,
                start=start,
            )

            if doc_batch:
                yield doc_batch

            if end_time <= start:
                break
            else:
                start = end_time
                time.sleep(0.2)
