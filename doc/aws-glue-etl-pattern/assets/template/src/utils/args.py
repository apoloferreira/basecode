"""Leitura dos parâmetros do job (--chave valor) passados pelo Glue."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

from awsglue.utils import getResolvedOptions


@dataclass(frozen=True)
class JobArg:
    """Declaração de um parâmetro do job.

    Args:
        name: nome do parâmetro, sem o prefixo ``--``.
        required: se True, o parâmetro precisa ter valor ao final da resolução
            (informado na execução ou vindo de ``default``).
        default: valor usado quando o parâmetro não é informado na execução.
    """

    name: str
    required: bool = True
    default: str | None = None

    def __post_init__(self) -> None:
        if self.name != self.name.upper():
            raise ValueError(f"Nome de parâmetro deve estar em maiúsculas: {self.name!r}")


def _is_present(name: str, argv: Sequence[str]) -> bool:
    flag = f"--{name}"
    return any(arg == flag or arg.startswith(f"{flag}=") for arg in argv)


def get_job_args(argv: Sequence[str], job_args: Sequence[JobArg]) -> dict[str, str | None]:
    """Resolve os parâmetros do job, aplicando valores padrão e validando os obrigatórios.

    Retorna um dicionário com ``JOB_NAME`` e todos os parâmetros declarados. Parâmetros
    opcionais sem valor e sem padrão aparecem como ``None``.

    Raises:
        ValueError: se algum parâmetro obrigatório ficar sem valor.
    """
    present = [arg.name for arg in job_args if _is_present(arg.name, argv)]
    resolved = getResolvedOptions(list(argv), list(dict.fromkeys(["JOB_NAME", *present])))

    values: dict[str, str | None] = {"JOB_NAME": resolved["JOB_NAME"]}
    for arg in job_args:
        values[arg.name] = resolved.get(arg.name, arg.default)

    missing = [arg.name for arg in job_args if arg.required and not values[arg.name]]
    if missing:
        raise ValueError(f"Parâmetros obrigatórios sem valor: {', '.join(missing)}")
    return values
