import boto3
from botocore.exceptions import ClientError

def delete_s3_path(bucket_name: str, path: str):
    """
    Apaga um arquivo ou diretório (prefixo) no bucket S3.
    
    Args:
        bucket_name (str): Nome do bucket.
        path (str): Caminho do arquivo ou diretório no bucket.
                    Exemplo:
                        - "meu_arquivo.txt"
                        - "pasta/subpasta/"
    """
    s3 = boto3.client("s3")
    
    try:
        # Verifica se o caminho termina com "/" para tratar como diretório
        if path.endswith("/"):
            # Lista todos os objetos do diretório
            paginator = s3.get_paginator("list_objects_v2")
            deleted_files = []
            for page in paginator.paginate(Bucket=bucket_name, Prefix=path):
                if "Contents" in page:
                    objects_to_delete = [{"Key": obj["Key"]} for obj in page["Contents"]]
                    if objects_to_delete:
                        s3.delete_objects(Bucket=bucket_name, Delete={"Objects": objects_to_delete})
                        deleted_files.extend(obj["Key"] for obj in objects_to_delete)

            print(f"✅ Diretório '{path}' apagado com sucesso!")
            if deleted_files:
                print(f"{len(deleted_files)} arquivos deletados.")
            else:
                print("Nenhum arquivo encontrado nesse diretório.")
        
        else:
            # Apaga arquivo individual
            s3.delete_object(Bucket=bucket_name, Key=path)
            print(f"✅ Arquivo '{path}' apagado com sucesso!")
    
    except ClientError as e:
        print(f"❌ Erro ao apagar '{path}': {e}")
