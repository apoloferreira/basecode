"""Entry point: composição das dependências (Composition Root).

É o único lugar onde as classes concretas se encontram — ideal para
rodar em AWS Batch / container, com exit code refletindo o resultado.
"""

from __future__ import annotations

import logging
import sys

import boto3

from app.extract.athena_reader import AthenaChunkReader
from app.pipeline import ChunkPipeline
from app.process.chunk_processor import MyBusinessProcessor
from app.settings import AthenaSettings

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s | %(message)s",
)

SQL = """
SELECT *
FROM minha_tabela
WHERE data_particao = :data_ref
"""


def main() -> int:
    settings = AthenaSettings.from_env()
    session = boto3.Session()

    pipeline = ChunkPipeline(
        reader=AthenaChunkReader(settings, boto3_session=session),
        processor=MyBusinessProcessor(),
        fail_fast=True,
    )

    report = pipeline.run(SQL, params={"data_ref": "2026-07-19"})
    return 0 if report.success else 1


if __name__ == "__main__":
    sys.exit(main())
