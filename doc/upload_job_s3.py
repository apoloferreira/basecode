import argparse
import os
import boto3
from fnmatch import fnmatch
from pathlib import Path
from typing import Iterable, Tuple


client_s3 = boto3.client("s3", region_name="us-east-1") 


def iter_local_files(base_dir: Path, follow_symlinks: bool = False) -> Iterable[Path]:
    for root, _, files in os.walk(base_dir, followlinks=follow_symlinks):
        root_path = Path(root)
        for fname in files:
            fpath = root_path / fname
            if fpath.is_file() or (follow_symlinks and fpath.is_symlink()):
                yield fpath

def should_skip(path: Path, base_dir: Path, include: list[str], exclude: list[str]) -> bool:
    rel = path.relative_to(base_dir).as_posix()
    # Exclude tem prioridade
    for pat in exclude:
        if fnmatch(rel, pat):
            return True
    # Se include estiver vazio, inclui tudo (que não foi excluído)
    if not include:
        return False
    # Se include tiver padrões, só inclui se algum bater
    for pat in include:
        if fnmatch(rel, pat):
            return False
    return True

def build_s3_key(local_file: Path, base_dir: Path, s3_prefix: str) -> str:
    rel = local_file.relative_to(base_dir).as_posix()
    prefix = s3_prefix.strip("/")
    return f"{prefix}/{rel}" if prefix else rel

def upload_one_file(local_file: Path, bucket: str, key: str) -> None:
    client_s3.upload_file(
        Filename=str(local_file),
        Bucket=bucket,
        Key=key
    )

def upload_directory(
    bucket: str,
    s3_prefix: str,
    local_dir: str,
    follow_symlinks: bool = False,
) -> Tuple[int, int]:
    base_dir = Path(local_dir).expanduser().resolve()
    if not base_dir.exists() or not base_dir.is_dir():
        raise ValueError(f"Diretório local inválido: {base_dir}")
    scanned = 0
    uploaded = 0
    for fpath in iter_local_files(base_dir, follow_symlinks=follow_symlinks):
        scanned += 1
        key = build_s3_key(fpath, base_dir, s3_prefix)
        upload_one_file(local_file=fpath, bucket=bucket, key=key)
        uploaded += 1
    return scanned, uploaded

def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser("Upload recursivo (procedural) de diretório para S3")
    p.add_argument("--bucket", default="data-us-east-1-891377318910")
    p.add_argument("--prefix", default="mvp_sensoriamento/job/job-spark-mvp-sensoriamento-ingestao")
    p.add_argument("--local-dir", default="app_01")
    return p.parse_args()

def main() -> None:
    args = parse_args()
    scanned, uploaded = upload_directory(
        bucket=args.bucket,
        s3_prefix=args.prefix,
        local_dir=args.local_dir,
    )
    print(f"Scanned: {scanned}")
    print(f"Uploaded: {uploaded}")


if __name__ == "__main__":
    main()
