from __future__ import annotations

import json
import logging
import random
import signal
import time
from collections.abc import Iterable, Iterator
from contextlib import AbstractContextManager
from dataclasses import dataclass
from threading import Event
from types import TracebackType
from typing import Any, Generator, Optional

from base import SQSClientProtocol, SQSMessage
from exceptions import SQSConfigurationError

logger = logging.getLogger(__name__)

_SQS_MAX_BATCH_SIZE = 10
_SQS_MAX_WAIT_SECONDS = 20
_SQS_MAX_VISIBILITY_TIMEOUT = 43200


@dataclass
class SQSConsumerConfig:
    queue_url: str
    max_messages: int = 10
    wait_time_seconds: int = 10
    visibility_timeout: Optional[int] = None
    idle_sleep_seconds: float = 2.0
    max_backoff_seconds: float = 300.0
    stop_after_idle_loops: Optional[int] = None  # para testes; em prod costuma ser None

    def __post_init__(self) -> None:
        """Valida todos os parâmetros."""
        self._validate()

    def _validate(self) -> None:
        """Valida a configuração inteira."""
        # Queue URL
        if not self.queue_url or not isinstance(self.queue_url, str):
            raise SQSConfigurationError(
                message="queue_url não pode estar vazio",
                error_code="QUEUE_URL_EMPTY",
            )
        if not self.queue_url.startswith("https://sqs."):
            raise SQSConfigurationError(
                message=f"queue_url inválida: {self.queue_url}",
                error_code="QUEUE_URL_INVALID",
            )

        # Max messages (batch size)
        if not 1 <= self.max_messages <= _SQS_MAX_BATCH_SIZE:
            raise SQSConfigurationError(
                message=f"max_messages deve estar entre 1->{_SQS_MAX_BATCH_SIZE}, recebido: {self.max_messages}",
                error_code="MAX_MESSAGES_OUT_OF_RANGE",
            )

        # Wait time
        if not 0 <= self.wait_time_seconds <= _SQS_MAX_WAIT_SECONDS:
            raise SQSConfigurationError(
                message=f"wait_time_seconds deve estar entre 0->{_SQS_MAX_WAIT_SECONDS}, recebido: {self.wait_time_seconds}",
                error_code="WAIT_TIME_OUT_OF_RANGE",
            )

        # Visibility timeout (SQS limits: 0 to 43200 seconds / 12 hours)
        if self.visibility_timeout is not None and not 1 <= self.visibility_timeout <= _SQS_MAX_VISIBILITY_TIMEOUT:
            raise SQSConfigurationError(
                message=f"visibility_timeout deve estar entre 1->{_SQS_MAX_VISIBILITY_TIMEOUT}, recebido: {self.visibility_timeout}",
                error_code="VISIBILITY_TIMEOUT_OUT_OF_RANGE",
            )

        # Idle sleep
        if self.idle_sleep_seconds <= 0:
            raise SQSConfigurationError(
                message=f"idle_sleep_seconds deve ser > 0, recebido: {self.idle_sleep_seconds}",
                error_code="IDLE_SLEEP_INVALID",
            )


class SQSMessageConsumer(AbstractContextManager, Iterable[SQSMessage]):
    """
    Consumidor iterativo de mensagens SQS com graceful shutdown.

    Uso típico:

        with SQSMessageConsumer(sqs_client, config) as consumer:
            for message in consumer:
                process(message)
                consumer.ack(message)

    Reage a SIGTERM e SIGINT encerrando o loop de forma limpa.
    """

    def __init__(self, sqs_client: SQSClientProtocol, config: SQSConsumerConfig) -> None:
        self._sqs_client = sqs_client
        self._config = config
        self._shutdown = Event()
        self._poll_failures = 0
        self._idle_loops = 0

    def _handle_signal(self, signum: int, frame: Any) -> None:
        logger.info("Sinal %d recebido — iniciando shutdown graceful.", signum)
        self._shutdown.set()

    def __enter__(self) -> SQSMessageConsumer:
        logger.info("Iniciando SQSMessageConsumer: %s", self._config.queue_url)
        self._shutdown.clear()
        self._poll_failures = 0
        self._idle_loops = 0
        signal.signal(signal.SIGTERM, self._handle_signal)
        signal.signal(signal.SIGINT, self._handle_signal)
        return self

    def __exit__(
        self,
        exc_type: Optional[type[BaseException]],
        exc: Optional[BaseException],
        tb: Optional[TracebackType],
    ) -> bool:
        logger.info("Finalizando SQSMessageConsumer: %s", self._config.queue_url)
        self._shutdown.set()
        return False  # não suprime exceções

    def __iter__(self) -> Iterator[SQSMessage]:
        return self._message_generator()

    def close(self) -> None:
        """Encerra o loop de polling a partir de qualquer ponto do código."""
        logger.info("Sinalizando fechamento do consumidor SQS.")
        self._shutdown.set()

    def ack(self, message: SQSMessage) -> bool:
        """Deleta a mensagem da fila. Retorna True em sucesso, False em falha."""
        try:
            self._sqs_client.delete_message(
                QueueUrl=self._config.queue_url,
                ReceiptHandle=message.receipt_handle,
            )
            logger.debug("Mensagem %s removida da fila.", message.message_id)
            return True
        except Exception:
            logger.exception("Falha ao deletar mensagem %s.", message.message_id)
            return False

    def _message_generator(self) -> Generator[SQSMessage, None, None]:
        while not self._shutdown.is_set():
            messages = self._poll_batch()

            if not messages:
                self._idle_loops += 1
                if (
                    self._config.stop_after_idle_loops is not None
                    and self._idle_loops >= self._config.stop_after_idle_loops
                ):
                    logger.info(
                        "Limite de loops ociosos atingido (%s). Encerrando.",
                        self._config.stop_after_idle_loops,
                    )
                    break

                logger.debug(
                    "Sem mensagens. Loop ocioso #%s. Aguardando %.2fs...",
                    self._idle_loops,
                    self._config.idle_sleep_seconds,
                )
                time.sleep(self._config.idle_sleep_seconds)
                continue

            self._idle_loops = 0

            for raw_msg in messages:
                if self._shutdown.is_set():
                    break
                try:
                    yield self._parse_raw_message(raw_msg)
                except Exception:
                    logger.exception("Erro ao parsear mensagem bruta: %r. Ignorando.", raw_msg)
                    # Não re-raise: uma mensagem inválida não deve encerrar o consumer.
                    # A mensagem voltará à fila após o visibility_timeout expirar
                    # ou irá para a DLQ se configurada no SQS.

    def _poll_batch(self) -> list[dict[str, Any]]:
        kwargs: dict[str, Any] = dict(
            QueueUrl=self._config.queue_url,
            MaxNumberOfMessages=self._config.max_messages,
            WaitTimeSeconds=self._config.wait_time_seconds,
            AttributeNames=["All"],
        )
        # Só sobrescreve o VisibilityTimeout da fila se explicitamente configurado.
        # Passar 0 tornaria a mensagem imediatamente visível para outros consumidores.
        if self._config.visibility_timeout is not None:
            kwargs["VisibilityTimeout"] = self._config.visibility_timeout

        try:
            response = self._sqs_client.receive_message(**kwargs)
            self._poll_failures = 0
            return response.get("Messages", []) or []
        except Exception:
            logger.exception("Erro ao consultar a fila SQS.")
            self._backoff()
            return []

    def _backoff(self) -> None:
        """Espera exponencial com jitter para evitar retry storm em falhas consecutivas."""
        self._poll_failures += 1
        delay = min(2.0 ** self._poll_failures, self._config.max_backoff_seconds)
        jitter = random.uniform(0, delay * 0.1)
        logger.debug(
            "Backoff: aguardando %.2fs (falha #%s).", delay + jitter, self._poll_failures
        )
        time.sleep(delay + jitter)

    def _parse_raw_message(self, raw: dict[str, Any]) -> SQSMessage:
        message_id = raw.get("MessageId", "")
        receipt_handle = raw.get("ReceiptHandle", "")

        if not message_id or not receipt_handle:
            raise ValueError(f"Mensagem SQS sem MessageId ou ReceiptHandle: {raw!r}")

        body_raw = raw.get("Body", "")
        try:
            body: Any = json.loads(body_raw)
        except json.JSONDecodeError:
            body = body_raw

        return SQSMessage(
            message_id=message_id,
            receipt_handle=receipt_handle,
            body_raw=body_raw,
            body=body,
            attributes=raw.get("Attributes", {}) or {},
        )
