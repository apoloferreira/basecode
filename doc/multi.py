




import os
import torch


def gpu_worker(
    gpu_index: int,
    device: str,
    worker_fn,
    *args,
    **kwargs,
):
    """
    Processo isolado por GPU.
    """

    # Faz o processo enxergar APENAS essa GPU
    os.environ["CUDA_VISIBLE_DEVICES"] = str(gpu_index)

    # Reimport torch dentro do processo (boa prática)
    import torch

    torch.cuda.set_device(0)
    device = torch.device("cuda:0")

    print(f"[PID {os.getpid()}] Usando GPU física {gpu_index} -> {device}")

    return worker_fn(device, *args, **kwargs)



def run_inference(device, data_chunk):
    import torch

    print(f"Rodando inferência em {device} com {len(data_chunk)} itens")

    # Exemplo fake
    x = torch.randn(1024, 1024, device=device)
    y = x @ x.T

    torch.cuda.synchronize()


import multiprocessing as mp


def run_on_all_gpus(
    worker_fn,
    worker_args_per_gpu,
):
    """
    worker_args_per_gpu:
        dict[gpu_index] -> tuple(args)
    """

    mp.set_start_method("spawn", force=True)

    gpus = get_available_gpus()

    if not gpus:
        raise RuntimeError("Nenhuma GPU disponível")

    processes = []

    for gpu_index, device in gpus.items():
        args = worker_args_per_gpu.get(gpu_index, ())

        p = mp.Process(
            target=gpu_worker,
            args=(gpu_index, device, worker_fn, *args),
        )
        p.start()
        processes.append(p)

    for p in processes:
        p.join()


if __name__ == "__main__":
    gpus = get_available_gpus()

    # Exemplo: dividir dados por GPU
    data = list(range(100))
    chunks = {i: (data[i::len(gpus)],) for i in gpus}

    run_on_all_gpus(
        worker_fn=run_inference,
        worker_args_per_gpu=chunks,
    )




