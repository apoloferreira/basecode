import json
import boto3
import pyarrow as pa
import pyarrow.parquet as pq
import pyarrow.compute as pc
from io import BytesIO
from typing import Dict, Any, Optional

# from schema_config import PARQUET_SCHEMA
# from utils import MAP_TYPES


MAP_TYPES = {
    "int32": pa.int32(),
    "int64": pa.int64(),
    "float32": pa.float32(),
    "float64": pa.float64(),
    "string": pa.string(),
    "date32": pa.date32(),
    "date64": pa.date64(),
    "timestamp[s]": pa.timestamp('s'),
    "timestamp[ms]": pa.timestamp('ms'),
    "timestamp[us]": pa.timestamp('us'),
    "timestamp[ns]": pa.timestamp('ns'),
    "bool": pa.bool_(),
    "decimal128": pa.decimal128(18, 4)
}

PARQUET_SCHEMA = {
    "id": "int64",
    "name": "string",
    "value": "float64",
    "created_at": "timestamp[ms]",
    "is_active": "bool"
}


def read_parquet_from_s3(bucket: str, key: str, s3_client: Any) -> pa.Table:
    """
    Lê um arquivo Parquet do S3 e retorna uma PyArrow Table.
    
    Args:
        bucket: Nome do bucket S3
        key: Caminho do arquivo no bucket
        s3_client: Cliente boto3 S3
        
    Returns:
        PyArrow Table com os dados do Parquet
    """
    response = s3_client.get_object(Bucket=bucket, Key=key)
    parquet_data = response['Body'].read()
    
    # Usar BytesIO para ler o Parquet da memória
    buffer = BytesIO(parquet_data)
    table = pq.read_table(buffer)
    
    return table


def convert_column_types(table: pa.Table, schema_dict: Dict[str, str]) -> pa.Table:
    """
    Converte os tipos das colunas conforme o schema definido.
    
    Args:
        table: PyArrow Table com os dados originais
        schema_dict: Dicionário com o schema desejado {nome_coluna: tipo}
        
    Returns:
        PyArrow Table com os tipos convertidos
    """
    # Criar lista para armazenar as colunas convertidas
    new_columns = []
    new_column_names = []
    
    for column_name in table.column_names:
        column = table.column(column_name)
        
        if column_name in schema_dict:
            target_type = schema_dict[column_name]
            try:
                mapped_type = MAP_TYPES[target_type]
                new_column = pc.cast(column, mapped_type)                    
            except Exception as e:
                print(f"Erro ao converter coluna {column_name} para {target_type}: {str(e)}")
                new_column = column
        else:
            # Se a coluna não estiver no schema, manter como está
            new_column = column
        
        new_columns.append(new_column)
        new_column_names.append(column_name)
    
    # Criar nova tabela com as colunas convertidas
    return pa.Table.from_arrays(new_columns, names=new_column_names)


def write_parquet_to_s3(
    table: pa.Table,
    bucket: str,
    key: str,
    s3_client: Any,
    compression: str = 'snappy'
) -> None:
    """
    Escreve uma PyArrow Table como Parquet no S3.
    
    Args:
        table: PyArrow Table com os dados
        bucket: Nome do bucket S3 de destino
        key: Caminho do arquivo no bucket de destino
        s3_client: Cliente boto3 S3
        compression: Tipo de compressão (padrão: snappy)
    """
    # Escrever o Parquet em memória
    buffer = BytesIO()
    pq.write_table(table, buffer)  # compression=compression
    
    # Voltar ao início do buffer
    buffer.seek(0)
    
    # Upload para o S3
    s3_client.put_object(
        Bucket=bucket,
        Key=key,
        Body=buffer.getvalue()
    )


def process_parquet_conversion(
    source_bucket: str,
    source_key: str,
    target_bucket: str,
    target_key: str,
    schema_dict: Dict[str, str],
    s3_client: Optional[Any] = None
) -> Dict[str, Any]:
    """
    Função principal que orquestra todo o processo de conversão.
    
    Args:
        source_bucket: Bucket S3 de origem
        source_key: Caminho do arquivo de origem
        target_bucket: Bucket S3 de destino
        target_key: Caminho do arquivo de destino
        schema_dict: Dicionário com o schema de conversão
        s3_client: Cliente S3 (opcional, será criado se não fornecido)
        
    Returns:
        Dicionário com informações sobre o processamento
    """
    # Criar cliente S3 se não fornecido
    if s3_client is None:
        s3_client = boto3.client('s3')
    
    try:
        # 1. Ler o Parquet do S3
        print(f"Lendo arquivo: s3://{source_bucket}/{source_key}")
        table = read_parquet_from_s3(source_bucket, source_key, s3_client)
        original_rows = len(table)
        original_columns = len(table.column_names)
        
        # 2. Converter tipos conforme schema
        print("Convertendo tipos das colunas...")
        converted_table = convert_column_types(table, schema_dict)
        
        # 3. Escrever o resultado no S3
        print(f"Escrevendo arquivo: s3://{target_bucket}/{target_key}")
        write_parquet_to_s3(converted_table, target_bucket, target_key, s3_client)
        
        return {
            'status': 'success',
            'source': f's3://{source_bucket}/{source_key}',
            'target': f's3://{target_bucket}/{target_key}',
            'rows_processed': original_rows,
            'columns_processed': original_columns,
            'message': 'Conversão concluída com sucesso'
        }
        
    except Exception as e:
        return {
            'status': 'error',
            'source': f's3://{source_bucket}/{source_key}',
            'target': f's3://{target_bucket}/{target_key}',
            'error': str(e),
            'message': 'Erro durante a conversão'
        }


def lambda_handler(event, context):
    try:
        # Extrair parâmetros do event
        source_bucket = event['source_bucket']
        source_key = event['source_key']
        target_bucket = event['target_bucket']
        target_key = event['target_key']
        
        # Usar o schema importado do arquivo externo
        result = process_parquet_conversion(
            source_bucket=source_bucket,
            source_key=source_key,
            target_bucket=target_bucket,
            target_key=target_key,
            schema_dict=PARQUET_SCHEMA
        )
        
        return {
            'statusCode': 200 if result['status'] == 'success' else 500,
            'body': json.dumps(result)
        }
    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps({
                'status': 'error',
                'message': f'Erro inesperado: {str(e)}'
            })
        }
