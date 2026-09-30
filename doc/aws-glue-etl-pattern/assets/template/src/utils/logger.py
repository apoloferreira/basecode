"""Logger padrão dos jobs. Saída em stdout, que o Glue envia ao CloudWatch."""
from __future__ import annotations

import logging
import sys

_FORMAT = "%(asctime)s | %(levelname)s | %(name)s | %(message)s"


def get_logger(name: str, level: int | str = logging.INFO) -> logging.Logger:
    """Retorna um logger configurado uma única vez por nome (chamadas repetidas não duplicam handlers)."""
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(logging.Formatter(_FORMAT))
        logger.addHandler(handler)
        logger.propagate = False
    logger.setLevel(level)
    return logger
