from __future__ import annotations

import logging
import os

import boto3

from base import SQSClientProtocol, SQSMessage
from consumer import SQSConsumerConfig, SQSMessageConsumer

logger = logging.getLogger(__name__)


class SatelliteIngestionProcessor:
    """
    Processador de negócio para ingestão de sensoriamento remoto.

    Implemente `process` com a lógica de domínio:
    - leitura do payload (geometry, date_range, etc.)
    - processamento das imagens de satélite
    - escrita no S3 ou banco de dados
    """

    def process(self, message: SQSMessage) -> None:
        logger.info(
            "Processando mensagem %s (tentativa #%s)",
            message.message_id,
            message.approximate_receive_count,
        )
        # payload = message.body
        # geometry = payload["geometry"]
        # date_range = payload["date_range"]
        # processar(geometry, date_range)


def build_config() -> SQSConsumerConfig:
    return SQSConsumerConfig(
        queue_url=os.environ["SQS_QUEUE_URL"],
        max_messages=int(os.getenv("SQS_MAX_MESSAGES", "10")),
        wait_time_seconds=int(os.getenv("SQS_WAIT_TIME_SECONDS", "10")),
        visibility_timeout=int(os.getenv("SQS_VISIBILITY_TIMEOUT", "300")),
        idle_sleep_seconds=float(os.getenv("SQS_IDLE_SLEEP_SECONDS", "2.0")),
    )


def main() -> None:
    config = build_config()
    processor = SatelliteIngestionProcessor()
    client_sqs: SQSClientProtocol = boto3.client(
        service_name="sqs",
        region_name=os.getenv("AWS_REGION", "sa-east-1"),
    )

    with SQSMessageConsumer(client_sqs, config) as consumer:
        for msg in consumer:
            try:
                processor.process(msg)
                if not consumer.ack(msg):
                    logger.warning(
                        "ACK falhou para mensagem %s — será reprocessada.",
                        msg.message_id,
                    )
            except Exception:
                logger.exception(
                    "Erro ao processar mensagem %s — voltará para a fila (tentativa #%s).",
                    msg.message_id,
                    msg.approximate_receive_count,
                )


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )
    main()
