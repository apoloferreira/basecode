from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Literal, TypeAlias

AthenaReadMode: TypeAlias = Literal["ctas", "unload", "regular"]
ChunkSize: TypeAlias = int | Literal[True]
ThreadSetting: TypeAlias = bool | int


def _required_env(name: str) -> str:
    value = os.getenv(name, "").strip()
    if not value:
        raise ValueError(f"A variavel de ambiente {name} e obrigatoria")
    return value


def _parse_bool(value: str, *, name: str) -> bool:
    normalized = value.strip().lower()
    if normalized in {"1", "true", "yes", "sim"}:
        return True
    if normalized in {"0", "false", "no", "nao", "não"}:
        return False
    raise ValueError(f"{name} deve ser true ou false; recebido: {value!r}")


def _parse_chunk_size(value: str) -> ChunkSize:
    if value.strip().lower() == "true":
        return True
    try:
        chunk_size = int(value)
    except ValueError as exc:
        raise ValueError("ATHENA_CHUNK_SIZE deve ser true ou um inteiro positivo") from exc
    if chunk_size <= 0:
        raise ValueError("ATHENA_CHUNK_SIZE deve ser maior que zero")
    return chunk_size


def _parse_threads(value: str) -> ThreadSetting:
    normalized = value.strip().lower()
    if normalized in {"true", "false"}:
        return _parse_bool(normalized, name="ATHENA_USE_THREADS")
    try:
        threads = int(value)
    except ValueError as exc:
        raise ValueError("ATHENA_USE_THREADS deve ser true, false ou um inteiro positivo") from exc
    if threads <= 0:
        raise ValueError("ATHENA_USE_THREADS deve ser maior que zero")
    return threads


@dataclass(frozen=True, slots=True)
class AthenaSettings:
    database: str
    workgroup: str
    s3_output: str
    chunk_size: ChunkSize = True
    read_mode: AthenaReadMode = "ctas"
    keep_files: bool = False
    use_threads: ThreadSetting = True
    polling_delay_seconds: float = 1.0
    encryption: str | None = None
    kms_key: str | None = None

    def __post_init__(self) -> None:
        if self.chunk_size is not True and (
            isinstance(self.chunk_size, bool) or self.chunk_size <= 0
        ):
            raise ValueError("chunk_size deve ser True ou um inteiro positivo")
        if self.read_mode not in {"ctas", "unload", "regular"}:
            raise ValueError(f"Modo de leitura invalido: {self.read_mode!r}")
        if not self.s3_output.startswith("s3://"):
            raise ValueError("s3_output deve ser uma URI S3")
        if self.polling_delay_seconds <= 0:
            raise ValueError("polling_delay_seconds deve ser maior que zero")
        if self.encryption not in {None, "SSE_S3", "SSE_KMS"}:
            raise ValueError("encryption deve ser None, SSE_S3 ou SSE_KMS")
        if self.encryption == "SSE_KMS" and not self.kms_key:
            raise ValueError("kms_key e obrigatoria quando encryption=SSE_KMS")

    @classmethod
    def from_env(cls) -> AthenaSettings:
        mode = os.getenv("ATHENA_READ_MODE", "ctas").strip().lower()
        if mode not in {"ctas", "unload", "regular"}:
            raise ValueError("ATHENA_READ_MODE deve ser ctas, unload ou regular")

        encryption = os.getenv("ATHENA_ENCRYPTION", "").strip() or None
        kms_key = os.getenv("ATHENA_KMS_KEY", "").strip() or None

        return cls(
            database=_required_env("ATHENA_DATABASE"),
            workgroup=os.getenv("ATHENA_WORKGROUP", "primary").strip() or "primary",
            s3_output=_required_env("ATHENA_S3_OUTPUT"),
            chunk_size=_parse_chunk_size(os.getenv("ATHENA_CHUNK_SIZE", "true")),
            read_mode=mode,  # type: ignore[arg-type]
            keep_files=_parse_bool(
                os.getenv("ATHENA_KEEP_FILES", "false"), name="ATHENA_KEEP_FILES"
            ),
            use_threads=_parse_threads(os.getenv("ATHENA_USE_THREADS", "true")),
            polling_delay_seconds=float(os.getenv("ATHENA_POLL_DELAY_SECONDS", "1.0")),
            encryption=encryption,
            kms_key=kms_key,
        )

    def approach_flags(self) -> tuple[bool, bool]:
        """Retorna ctas_approach e unload_approach, nessa ordem."""
        return self.read_mode == "ctas", self.read_mode == "unload"
