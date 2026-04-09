from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any, Optional, Protocol

logger = logging.getLogger(__name__)


class SQSClientProtocol(Protocol):
    """Protocolo mínimo esperado de um cliente SQS (ex: boto3 client)."""

    def receive_message(
        self,
        QueueUrl: str,
        MaxNumberOfMessages: int = 1,
        WaitTimeSeconds: int = 0,
        VisibilityTimeout: Optional[int] = None,
        AttributeNames: Optional[list[str]] = None,
        MessageAttributeNames: Optional[list[str]] = None,
    ) -> dict[str, Any]: ...

    def delete_message(
        self,
        QueueUrl: str,
        ReceiptHandle: str,
    ) -> dict[str, Any]: ...


@dataclass
class SQSMessage:
    """Representa uma mensagem genérica da SQS já parseada."""
    message_id: str
    receipt_handle: str
    body_raw: str
    body: Any
    attributes: dict[str, Any]

    @property
    def approximate_receive_count(self) -> int:
        """Número de vezes que a mensagem foi entregue (útil para lógica de retry/DLQ)."""
        try:
            return int(self.attributes.get("ApproximateReceiveCount", 0))
        except (ValueError, TypeError):
            return 0
