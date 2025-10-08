from __future__ import annotations
import boto3
from datetime import datetime
from typing import Dict, Any, List, Optional

def average_glue_job_runtime_seconds(
    job_name: str,
    region_name: Optional[str] = None,
    include_states: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """
    Calcula a média de tempo (em segundos) das execuções de um AWS Glue Job.

    Args:
        job_name: Nome do Glue Job.
        region_name: Região AWS (ex.: "us-east-1"). Se None, usa config padrão do ambiente.
        include_states: Lista de estados a considerar. Ex.: ["SUCCEEDED"].
                        Se None, considera execuções com CompletedOn != None (finalizadas),
                        independente do estado.

    Returns:
        {
          "job_name": str,
          "runs_count": int,               # quantidade de execuções consideradas
          "average_seconds": float | None, # média em segundos (None se sem dados)
          "details": [                     # (opcional) amostra com algumas execuções
              {"id": str, "state": str, "seconds": float},
              ...
          ]
        }
    """
    glue = boto3.client("glue", region_name=region_name) if region_name else boto3.client("glue")

    next_token: Optional[str] = None
    durations: List[float] = []
    sample_details: List[Dict[str, Any]] = []

    while True:
        params = {"JobName": job_name, "MaxResults": 100}
        if next_token:
            params["NextToken"] = next_token

        resp = glue.get_job_runs(**params)
        job_runs = resp.get("JobRuns", [])

        for jr in job_runs:
            started: Optional[datetime] = jr.get("StartedOn")
            completed: Optional[datetime] = jr.get("CompletedOn")
            state: str = jr.get("JobRunState", "UNKNOWN")
            run_id: str = jr.get("Id", "")

            # considerar apenas execuções finalizadas (possui CompletedOn)
            if completed is None or started is None:
                continue

            if include_states is not None and state not in include_states:
                continue

            seconds = (completed - started).total_seconds()
            # ignora valores negativos/estranhos
            if seconds >= 0:
                durations.append(seconds)
                # guarda apenas uma pequena amostra para inspeção
                if len(sample_details) < 10:
                    sample_details.append({"id": run_id, "state": state, "seconds": seconds})

        next_token = resp.get("NextToken")
        if not next_token:
            break

    avg_seconds: Optional[float] = None
    if durations:
        avg_seconds = sum(durations) / len(durations)

    return {
        "job_name": job_name,
        "runs_count": len(durations),
        "average_seconds": avg_seconds,
        "details": sample_details,
    }


if __name__ == "__main__":
    # Exemplo de uso:
    result = average_glue_job_runtime_seconds(
        job_name="meu-glue-job",
        region_name="us-east-1",
        include_states=["SUCCEEDED"]  # considere apenas execuções bem-sucedidas
    )
    print(result)
    if result["average_seconds"] is not None:
        print(f"Média de execução: {result['average_seconds']:.2f} s "
              f"({result['average_seconds']/60:.2f} min)")
    else:
        print("Sem execuções finalizadas elegíveis para calcular a média.")


###############################################################################################3


from __future__ import annotations
import boto3
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple

def _to_utc_aware(dt: datetime) -> datetime:
    """Garante que o datetime é timezone-aware em UTC."""
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)

def count_glue_job_runs_in_range(
    start: datetime,
    end: datetime,
    job_names: Optional[List[str]] = None,
    region_name: Optional[str] = None,
    use_completed_time: bool = False,
) -> Dict[str, int]:
    """
    Conta quantas execuções cada AWS Glue Job teve no intervalo [start, end).

    Args:
        start: Início do intervalo (incluído). Se naive, assume UTC.
        end: Fim do intervalo (excluído). Se naive, assume UTC.
        job_names: Lista de nomes de jobs. Se None, lista todos os jobs da conta/região.
        region_name: Região AWS (ex.: "us-east-1"). Se None, usa config padrão do ambiente.
        use_completed_time: Se True, filtra por CompletedOn; caso contrário, por StartedOn.

    Returns:
        Dict[str, int]: { job_name: quantidade_de_execucoes_no_intervalo }
    """
    start_utc = _to_utc_aware(start)
    end_utc = _to_utc_aware(end)

    glue = boto3.client("glue", region_name=region_name) if region_name else boto3.client("glue")

    # Pega todos os jobs se não foi fornecido
    if job_names is None:
        job_names = []
        next_token = None
        while True:
            params = {"MaxResults": 100}
            if next_token:
                params["NextToken"] = next_token
            resp = glue.get_jobs(**params)
            for job in resp.get("Jobs", []):
                name = job.get("Name")
                if name:
                    job_names.append(name)
            next_token = resp.get("NextToken")
            if not next_token:
                break

    counts: Dict[str, int] = {name: 0 for name in job_names}

    # Para cada job, pagina as execuções
    for name in job_names:
        next_token = None
        while True:
            params = {"JobName": name, "MaxResults": 100}
            if next_token:
                params["NextToken"] = next_token

            resp = glue.get_job_runs(**params)
            runs = resp.get("JobRuns", [])

            if not runs:
                break

            stop_pagination_for_this_job = False

            for r in runs:
                t: Optional[datetime] = r.get("CompletedOn") if use_completed_time else r.get("StartedOn")

                # Se não houver o timestamp escolhido (ex.: job ainda em execução e filtrando por CompletedOn), ignore
                if t is None:
                    continue

                t_utc = _to_utc_aware(t)

                # Intervalo fechado-aberto: [start_utc, end_utc)
                if start_utc <= t_utc < end_utc:
                    counts[name] += 1
                # Como a API retorna runs em ordem decrescente de tempo:
                # Se a execução já for mais antiga que o início do intervalo,
                # as próximas serão ainda mais antigas -> podemos parar a paginação deste job.
                elif t_utc < start_utc:
                    stop_pagination_for_this_job = True
                    break

            if stop_pagination_for_this_job:
                break

            next_token = resp.get("NextToken")
            if not next_token:
                break

    return counts


# -----------------------------
# Exemplo de uso: "mês de fevereiro de 2025" (UTC)
# -----------------------------
if __name__ == "__main__":
    feb_start = datetime(2025, 2, 1, 0, 0, 0, tzinfo=timezone.utc)
    mar_start = datetime(2025, 3, 1, 0, 0, 0, tzinfo=timezone.utc)

    # Contando por StartedOn (padrão)
    counts_started = count_glue_job_runs_in_range(
        start=feb_start,
        end=mar_start,
        job_names=None,           # None => lista todos os jobs
        region_name="us-east-1",
        use_completed_time=False  # False => usa StartedOn; True => usa CompletedOn
    )
    print("Execuções por job (StartedOn em fev/2025):")
    for job, qty in sorted(counts_started.items()):
        print(f"- {job}: {qty}")


