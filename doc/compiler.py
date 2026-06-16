import tarfile
from pathlib import Path
from typing import Iterable, Optional, Union


def create_sagemaker_model_tar(
    source_dir: Union[str, Path],
    output_path: Union[str, Path] = "model.tar.gz",
    exclude_patterns: Optional[Iterable[str]] = None,
) -> Path:
    """
    Cria um arquivo .tar.gz compatível com SageMaker Model a partir
    de um diretório local.

    O conteúdo do diretório é colocado na raiz do tar.gz.

    Exemplo:
        source_dir/
        ├── inference.py
        ├── model.onnx
        ├── config.yaml
        └── modules/
            └── utils.py

        Resultado ao extrair:
        /opt/ml/model/
        ├── inference.py
        ├── model.onnx
        ├── config.yaml
        └── modules/
            └── utils.py
    """

    source_dir = Path(source_dir).resolve()
    output_path = Path(output_path).resolve()

    if not source_dir.exists():
        raise FileNotFoundError(f"Diretório não encontrado: {source_dir}")

    if not source_dir.is_dir():
        raise NotADirectoryError(f"O caminho informado não é um diretório: {source_dir}")

    exclude_patterns = set(exclude_patterns or [])

    default_excludes = {
        "__pycache__",
        ".pytest_cache",
        ".mypy_cache",
        ".ruff_cache",
        ".git",
        ".ipynb_checkpoints",
    }

    exclude_patterns.update(default_excludes)

    def should_exclude(path: Path) -> bool:
        parts = set(path.parts)

        if parts.intersection(exclude_patterns):
            return True

        # Evita incluir o próprio arquivo .tar.gz caso ele esteja dentro do source_dir
        if path.resolve() == output_path:
            return True

        return False

    output_path.parent.mkdir(parents=True, exist_ok=True)

    with tarfile.open(output_path, mode="w:gz") as tar:
        for file_path in sorted(source_dir.rglob("*")):
            if should_exclude(file_path):
                continue

            if file_path.is_file() or file_path.is_symlink():
                arcname = file_path.relative_to(source_dir)

                tar.add(
                    file_path,
                    arcname=arcname,
                    recursive=False,
                )

    return output_path


if __name__ == "__main__":
    artifact_path = create_sagemaker_model_tar(
        source_dir="./model_artifacts",
        output_path="./model.tar.gz",
    )

    print(f"Arquivo criado em: {artifact_path}")
