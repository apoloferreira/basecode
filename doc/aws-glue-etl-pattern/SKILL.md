---
name: aws-glue-etl-pattern
description: Padrão da equipe para jobs de ETL no AWS Glue com PySpark. Define a estrutura do projeto (main.py, session, readers, writers, transformations por domínio, utils), o padrão de código (prefixo df_ em DataFrames, parâmetros do job em maiúsculas, imports no topo, dataclasses imutáveis, transformações como funções puras ou BaseTransformation), a sessão Spark com configurações padrão e por job, e o deploy. Use ao criar, alterar, migrar ou revisar qualquer job AWS Glue / PySpark, ou ao responder dúvidas sobre como organizar esse código, mesmo que o pedido não cite o padrão.
metadata:
  version: "1.0"
---

# Padrão de jobs AWS Glue (PySpark)

Guia **exclusivo para jobs de ETL no AWS Glue com PySpark**. Separa **sessão**, **leitura**,
**transformação** e **escrita**, com o `main.py` atuando como controlador do fluxo.

## Tópicos

| Tópico | Seção | Status |
|---|---|---|
| Padrão de código | [1. Padrão de código](#1-padrão-de-código) | v1 |
| Estruturação e código | [2. Estruturação e código](#2-estruturação-e-código) | v1 |
| Recomendações de infraestrutura | [3. Infraestrutura](#3-infraestrutura) | planejado |
| Performance | [4. Performance](#4-performance) | planejado |
| Testes | — | planejado |

Tópicos planejados ainda não têm regras definidas. Para eles, siga a documentação oficial da AWS e
do Apache Spark e **não apresente recomendações próprias como se fossem parte deste padrão**.

O código de exemplo completo está em `assets/template/src/` e segue todas as regras desta skill.

## Como aplicar esta skill

- **Criar um novo job:** use `assets/template/src/` como ponto de partida. Os domínios de exemplo
  (`talhao`, `imovel`, `producao`), o `JOB_ARGS` e o `SPARK_CONF` são ilustrativos: substitua pelos
  do job. Mantenha `session/`, `utils/`, `readers/base.py`, `writers/base.py` e
  `transformations/base.py`, e mantenha apenas os leitores e escritores que o job usa, ou todos, se o
  repositório for compartilhado entre jobs.
- **Alterar um job que já segue o padrão:** coloque cada mudança na camada responsável (seção 2.2)
  e siga as regras da seção 1.
- **Migrar um job fora do padrão:** mapeie o código existente para as camadas: leituras para
  `readers`, regras de negócio para `transformations/<dominio>.py`, escritas para `writers` e a
  orquestração para `main.py`. Preserve o comportamento e aponte o que mudou.
- **Revisar código:** use o [checklist de revisão](#17-checklist-de-revisão).
- **Conflito com um pedido explícito do usuário:** siga o pedido, mas informe qual regra do padrão
  está sendo quebrada.

---

## 1. Padrão de código

Regras de codificação válidas para todo o código do job, em qualquer camada.

### 1.1 Nomenclatura

- **DataFrames começam com `df_`.** Vale para variáveis, parâmetros e atributos: `df_talhoes`,
  `df_imoveis`, `df_area_plantada`. Funções genéricas usam `df_input`; o parâmetro de `write` é
  `df_output`. Objetos que não são `DataFrame` (`DynamicFrame`, `DataFrameReader`,
  `DataFrameWriter`, `Column`) não usam o prefixo.
- **Parâmetros do job em letras maiúsculas** (uppercase completo, palavras separadas por `_`):
  `--REFERENCE_DATE`, `--TARGET_PATH`. O mesmo nome na declaração (`JobArg("REFERENCE_DATE")`), no
  acesso (`args["REFERENCE_DATE"]`) e na configuração do job no Glue/IaC. Parâmetros especiais do
  próprio Glue (`--extra-py-files`, `--enable-glue-datacatalog` etc.) mantêm os nomes da AWS.
- **Nomes Python conforme a PEP 8:** módulos, funções e variáveis em `snake_case`; classes em
  `PascalCase`; constantes de módulo em `UPPER_CASE` (`JOB_ARGS`, `SPARK_CONF`,
  `DEFAULT_SPARK_CONF`, `OUTPUT_COLUMNS`); funções auxiliares internas com prefixo `_`.
- **Sufixos e prefixos de classe:** classes abstratas começam com `Base` (`BaseReader`,
  `BaseWriter`, `BaseTransformation`); leitores terminam em `Reader`; escritores em `Writer`.
- **Módulos de transformação têm o nome do domínio** (`talhao.py`, `imovel.py`), não do job.

### 1.2 Imports

- **Todos os imports no início do arquivo** (PEP 8). Nada de import dentro de função, método ou
  bloco condicional (inclusive `if TYPE_CHECKING`).
- Ordem: `from __future__ import annotations`; biblioteca padrão; terceiros (`awsglue`, `pyspark`);
  módulos do projeto. Um grupo por bloco, separados por linha em branco.
- Imports de módulos do projeto são absolutos a partir de `src/` (`from readers.base import
  BaseReader`), nunca relativos.

### 1.3 Tipagem

- Type hints em todas as funções e métodos públicos, incluindo o retorno.
- Use `from __future__ import annotations` e a sintaxe moderna (`str | None`, `list[str]`,
  `dict[str, str]`).
- Valores restritos usam `Literal` (ex.: `WriteMode = Literal["overwrite", "append", ...]`).

### 1.4 Funções e classes

- **Transformações: funções por padrão.** Funções pequenas e puras `DataFrame -> DataFrame`, com o
  DataFrame de entrada como primeiro parâmetro, encadeadas com `DataFrame.transform(...)`.
- **Classes quando fizer sentido**, sempre herdando da base da camada (`BaseReader`, `BaseWriter`,
  `BaseTransformation`) e declaradas como `@dataclass(frozen=True)`: parâmetros como campos,
  imutáveis, dependências recebidas no construtor.
- Um único método público por classe da camada: `read()`, `write(df_output)` ou `transform(...)`.
- Classes intermediárias de reuso (ex.: `S3FileReader`) validam em `__post_init__` o que as
  subclasses precisam definir.
- Sem estado global mutável e sem singletons: tudo o que uma função ou classe precisa entra por
  parâmetro ou construtor.

### 1.5 Documentação no código

- Docstrings e comentários **descrevem o que aquele código faz** (e por quê, quando não é óbvio).
- **As regras deste padrão ficam só nesta skill**: não as repita em docstrings ou comentários do
  código.
- Docstrings em português, no estilo `Args:` / `Raises:` quando houver parâmetros ou exceções
  relevantes.

### 1.6 Fluxo, erros e logs

- O `main.py` segue a ordem: parâmetros → logger → sessão → `try` com as etapas **1. Extract**,
  **2. Transform** e **3. Load**, marcadas por comentários de seção → `session.commit()`.
- Erros não são silenciados: o `main.py` registra com `logger.exception(...)` e relança (`raise`),
  para o Glue marcar a execução como falha. O `commit` só acontece após sucesso.
- Logs via `get_logger` (stdout → CloudWatch), com a data de referência nas mensagens de início,
  fim e falha. Não use `print`.
- Valores de parâmetros chegam como `str`; a conversão de tipo é feita no `main.py`
  (`float(args["AREA_MINIMA_HA"])`).

### 1.7 Checklist de revisão

- [ ] Todo `DataFrame` tem nome iniciado por `df_`.
- [ ] Todos os imports estão no topo, na ordem definida, sem imports locais ou condicionais.
- [ ] Parâmetros do job em maiúsculas, declarados em `JOB_ARGS` com `JobArg`.
- [ ] Type hints completos em funções e métodos públicos.
- [ ] Regra de negócio apenas em `transformations/`, no módulo do domínio correto.
- [ ] Leitores e escritores sem regra de negócio; escrita idempotente.
- [ ] Leitura de fonte particionada filtra a partição.
- [ ] Classes herdam da base da camada e são `@dataclass(frozen=True)`.
- [ ] Configurações Spark do job em `SPARK_CONF`, passadas na criação da sessão.
- [ ] `main.py` com as etapas Extract/Transform/Load, `logger.exception` + `raise` e `commit` no fim.
- [ ] Docstrings e comentários sem repetir regras do padrão.

---

## 2. Estruturação e código

### 2.1 Estrutura

```
src/
├── main.py                     # entrypoint do job: controla extract -> transform -> load
├── session/
│   └── glue_session.py         # DEFAULT_SPARK_CONF, create_spark_session(), create_glue_session()
├── readers/
│   ├── base.py                 # BaseReader (ABC)          -> read() -> DataFrame
│   ├── catalog.py              # GlueCatalogReader, IcebergTableReader
│   └── s3.py                   # S3FileReader -> S3ParquetReader, S3JsonReader, S3CsvReader
├── writers/
│   ├── base.py                 # BaseWriter (ABC)          -> write(df_output) -> None
│   ├── catalog.py              # GlueCatalogTableWriter, IcebergTableWriter
│   └── s3.py                   # S3FileWriter -> S3ParquetWriter, S3JsonWriter, S3CsvWriter
├── transformations/
│   ├── base.py                 # BaseTransformation (ABC)  -> transform(...) -> DataFrame
│   ├── common.py               # funções genéricas, sem domínio
│   ├── talhao.py               # domínio talhão
│   ├── imovel.py               # domínio imóvel rural
│   └── producao.py             # domínio produção agrícola (AreaPlantadaPorImovel)
└── utils/
    ├── args.py                 # JobArg, get_job_args(): parâmetros com valor padrão
    └── logger.py               # get_logger(): logger padrão (stdout -> CloudWatch)
```

### 2.2 Responsabilidade de cada módulo

| Módulo | Responsabilidade | Pode conter | Não pode conter |
|---|---|---|---|
| `main.py` | Orquestrar o job: ler parâmetros, criar a sessão, instanciar leitores/escritores, chamar as transformações, fazer commit | Chamadas aos demais módulos, tratamento de erro de topo | Regra de negócio, lógica de leitura/escrita |
| `session` | Criar a `SparkSession` (com as configurações Spark) e, sobre ela, `GlueContext` e `Job` | Configurações Spark padrão | Leitura ou escrita de dados |
| `readers` | Obter dados de uma fonte e devolver `DataFrame` | Filtro de partição, schema, opções de leitura | Regra de negócio |
| `writers` | Persistir um `DataFrame` em um destino | Modo de escrita, particionamento, opções | Regra de negócio, alteração de dados |
| `transformations` | Regra de negócio, separada por domínio | Funções puras e classes `BaseTransformation` | `awsglue`, leitura, escrita, `spark.read`, `boto3` |
| `utils` | Funções auxiliares transversais | Parâmetros, logging, helpers genéricos | Dependência de outros módulos do projeto |

#### Dependência entre módulos

```
main.py ──► session
        ──► readers ──┐
        ──► writers ──┼──► (apenas pyspark / awsglue)
        ──► transformations
        ──► utils
```

- Só o `main.py` importa todos os outros módulos.
- `readers`, `writers` e `transformations` **não** importam uns aos outros.
- `transformations` depende apenas de `pyspark` e de outros módulos de `transformations`.

### 2.3 Parâmetros do job

Os parâmetros são declarados no `main.py` como uma lista de `JobArg` e resolvidos por
`get_job_args`. Os nomes seguem a regra de maiúsculas da seção 1.1; `JobArg` rejeita nomes fora
desse padrão com `ValueError`.

```python
JOB_ARGS = [
    JobArg("REFERENCE_DATE"),                                       # obrigatório, sem padrão
    JobArg("IMOVEIS_DATABASE", default="cadastro"),                 # obrigatório, com padrão
    JobArg("TALHOES_MULTILINE", required=False, default="false"),   # opcional, com padrão
]
args = get_job_args(sys.argv, JOB_ARGS)
```

| Declaração | Não informado na execução | Informado |
|---|---|---|
| `JobArg("X")` | Erro | Valor informado |
| `JobArg("X", default="a")` | `"a"` | Valor informado |
| `JobArg("X", required=False)` | `None` | Valor informado |
| `JobArg("X", required=False, default="a")` | `"a"` | Valor informado |

- `required=True` garante que o parâmetro tenha valor ao final (informado ou padrão); se faltar, o
  job falha antes de criar a sessão, listando todos os ausentes.
- `JOB_NAME` é sempre resolvido automaticamente.

### 2.4 Sessão Spark

A sessão é criada no `main.py` por `create_glue_session`, que primeiro monta a `SparkSession`
(`SparkSession.builder` + configurações + `enableHiveSupport()`) e depois cria o `GlueContext` e o
`Job` sobre ela. `create_spark_session` também pode ser usada isoladamente.

#### Configurações padrão

`DEFAULT_SPARK_CONF` (em `session/glue_session.py`) vale para todos os jobs:

| Configuração | Valor | Motivo |
|---|---|---|
| `spark.sql.adaptive.enabled` | `true` | Adaptive Query Execution (AQE) |
| `spark.sql.adaptive.coalescePartitions.enabled` | `true` | AQE junta partições pequenas após shuffle |
| `spark.sql.adaptive.skewJoin.enabled` | `true` | AQE divide partições com skew em joins |
| `spark.sql.execution.arrow.pyspark.enabled` | `true` | Conversões Spark ↔ pandas via Arrow |
| `spark.sql.parquet.datetimeRebaseModeInRead` | `CORRECTED` | Lê datas antigas em Parquet sem rebase de calendário |
| `spark.sql.parquet.datetimeRebaseModeInWrite` | `CORRECTED` | Escreve datas antigas em Parquet sem rebase de calendário |
| `spark.sql.legacy.timeParserPolicy` | `CORRECTED` | Parsing de datas com o parser atual do Spark |
| `spark.sql.sources.partitionOverwriteMode` | `dynamic` | Overwrite substitui só as partições escritas (idempotência) |
| `hive.exec.dynamic.partition` / `.mode` | `true` / `nonstrict` | `insertInto` com partições dinâmicas no Glue Data Catalog |

Alterar um default afeta todos os jobs; isso é uma mudança no padrão, não em um job.

#### Configurações por job

Cada job pode ter configurações próprias para ajustar a execução à sua carga. Elas são declaradas
no `main.py` como um dicionário `SPARK_CONF` e passadas em `spark_conf`. São **adicionadas** aos
defaults e **sobrescrevem** o default quando a chave já existe:

```python
SPARK_CONF = {
    "spark.sql.shuffle.partitions": "64",                       # nova
    "spark.sql.adaptive.advisoryPartitionSizeInBytes": "128m",  # nova
    "spark.sql.execution.arrow.pyspark.enabled": "false",       # sobrescreve o default
}

session = create_glue_session(job_name=args["JOB_NAME"], job_args=args, spark_conf=SPARK_CONF)
```

- Para combinar com as configurações de Iceberg: `spark_conf={**iceberg_spark_conf(warehouse), **SPARK_CONF}`.
- Chaves inexistentes são aceitas pelo Spark sem erro e sem efeito: confira o nome na documentação
  do Spark da versão do Glue usada.
- Configurações estáticas (ex.: `spark.sql.extensions`) só têm efeito na criação da sessão, por isso
  toda configuração passa por `create_glue_session`, nunca por `spark.conf.set` depois.
- Capacidade de processamento (memória, executores) é definida pelo tipo e quantidade de workers do
  job no Glue, não por `SPARK_CONF`.
- `enable_hive_support=True` é o padrão; necessário para acessar o Glue Data Catalog via Spark
  (junto com o parâmetro de job `--enable-glue-datacatalog`).

### 2.5 Leitura e escrita: classes

Classe abstrata para tipagem e contrato, e uma classe concreta por tipo de fonte/destino:

```
BaseReader (ABC)                       BaseWriter (ABC)
├── GlueCatalogReader                  ├── GlueCatalogTableWriter
├── IcebergTableReader                 ├── IcebergTableWriter
└── S3FileReader (intermediária)       └── S3FileWriter (intermediária)
    ├── S3ParquetReader                    ├── S3ParquetWriter
    ├── S3JsonReader                       ├── S3JsonWriter
    └── S3CsvReader                        └── S3CsvWriter
```

1. Toda classe concreta é `@dataclass(frozen=True)`: parâmetros declarados como campos e imutáveis.
2. Dependências (`spark`, `glue_context`, caminhos, filtros) entram **no construtor**.
3. Um único método público: `read() -> DataFrame` ou `write(df_output) -> None`.
4. Leitores não aplicam regra de negócio: no máximo filtro de partição, schema e opções de leitura.
5. Classes intermediárias (`S3FileReader`, `S3FileWriter`) concentram a lógica comum; as subclasses
   definem apenas `file_format` e `default_options`. Instanciá-las diretamente gera `TypeError`.
6. Escritores são idempotentes por padrão (overwrite dinâmico de partições / `overwritePartitions`):
   reexecutar o job para a mesma data substitui a partição, não duplica.
7. Sempre que a fonte for particionada, filtre a partição na leitura (`push_down_predicate`, `where`
   ou caminho `dt=.../`).

```python
df_talhoes = S3JsonReader(spark=session.spark, path="s3://bucket/talhoes/dt=2026-09-30/").read()
S3ParquetWriter(path="s3://bucket/saida/", partition_by=["dt"]).write(df_area_plantada)
```

### 2.6 Transformações

#### Separação por domínio

As transformações ficam em `transformations/`, **separadas por domínio de negócio**: um módulo por
domínio (`talhao.py`, `imovel.py`, `producao.py`). Uma transformação pertence ao domínio da entidade
que ela trata, não ao job que a usa, para que outros jobs reaproveitem o mesmo código.

- `common.py`: apenas funções genéricas, sem regra de nenhum domínio (normalizar nomes, deduplicar,
  metadados de processamento).
- Um domínio pode usar funções de outro (ex.: `producao` compõe `talhao` e `imovel`).
- Quando um domínio crescer, o módulo vira subpacote: `transformations/talhao/{limpeza,agregacoes}.py`.

#### Funções (padrão preferencial)

Funções pequenas e puras `DataFrame -> DataFrame`, encadeadas com `DataFrame.transform(...)`. O
primeiro parâmetro é o DataFrame de entrada; os demais são configurações ou outros DataFrames.

```python
def area_por_cultura(df_talhoes: DataFrame, casas_decimais: int = 4) -> DataFrame:
    return df_talhoes.groupBy("cod_imovel", "cultura").agg(...)

df_resultado = (
    df_talhoes.transform(area_por_cultura, casas_decimais=2)
    .transform(enrich_with_imovel, df_imoveis=df_imoveis)
)
```

#### Classes (quando fizer sentido)

Use uma classe que herda de `BaseTransformation` quando a transformação:

- tem parâmetros de configuração que vale nomear e agrupar (limiares, listas de valores, regras);
- é a composição principal de um job, chamada pelo `main.py`;
- precisa de variações intercambiáveis com a mesma assinatura.

Regras: `@dataclass(frozen=True)`, configuração nos atributos, DataFrames de entrada como parâmetros
de `transform`, que é o único método obrigatório. Internamente, a classe compõe funções dos domínios.

```python
@dataclass(frozen=True)
class AreaPlantadaPorImovel(BaseTransformation):
    casas_decimais: int = 4

    def transform(self, df_imoveis: DataFrame, df_talhoes: DataFrame, reference_date: str) -> DataFrame:
        return (
            df_talhoes.transform(area_por_cultura, casas_decimais=self.casas_decimais)
            .transform(enrich_with_imovel, df_imoveis=df_imoveis)
            ...
        )
```

#### Chamada no `main.py`

O `main.py` de exemplo usa as duas formas em sequência na etapa de transformação: uma função
(`clean_talhoes`, domínio talhão) e uma classe (`AreaPlantadaPorImovel`, domínio produção agrícola).
Na função, a configuração vai como argumento da chamada; na classe, vai no construtor, e os
DataFrames vão em `transform`.

```python
# função
df_talhoes_validos = clean_talhoes(
    df_talhoes,
    area_minima_ha=float(args["AREA_MINIMA_HA"]),
)

# classe
df_area_plantada = AreaPlantadaPorImovel(
    casas_decimais=int(args["CASAS_DECIMAIS"]),
).transform(
    df_imoveis=df_imoveis,
    df_talhoes=df_talhoes_validos,
    reference_date=reference_date,
)
```

### 2.7 Como estender

- **Novo tipo de leitura** (ex.: JDBC): crie a classe em `readers/<tipo>.py`, herdando de
  `BaseReader`, como `@dataclass(frozen=True)`, implemente `read()` e exporte em
  `readers/__init__.py`.
- **Novo formato de arquivo no S3** (ex.: ORC): basta uma subclasse definindo o formato.

  ```python
  class S3OrcReader(S3FileReader):
      file_format = "orc"
  ```

- **Novo tipo de escrita**: mesmo processo, herdando de `BaseWriter` e implementando
  `write(df_output)`.
- **Nova regra de negócio**: adicione a função no módulo do domínio correspondente; crie um novo
  módulo apenas para um domínio novo.
- **Novo job**: parta de `assets/template/src/`, declare `JOB_ARGS` e `SPARK_CONF`, escolha leitores
  e escritores no `main.py` e componha as transformações dos domínios (função ou classe
  `BaseTransformation`).

### 2.8 Deploy no Glue

O `main.py` é o script do job; os demais pacotes vão em um zip passado via `--extra-py-files`.

```bash
cd src
zip -r ../dist/libs.zip . -x "main.py" -x "*__pycache__*"
aws s3 cp main.py            s3://<bucket-artefatos>/jobs/<nome_do_job>/main.py
aws s3 cp ../dist/libs.zip   s3://<bucket-artefatos>/jobs/<nome_do_job>/libs.zip
```

| Parâmetro do Glue | Quando |
|---|---|
| `--extra-py-files s3://.../libs.zip` | Sempre |
| `--enable-glue-datacatalog true` | Ao usar `GlueCatalogTableWriter` (e `spark.table` em tabelas do catálogo) |
| `--datalake-formats iceberg` | Ao usar `IcebergTableReader`/`IcebergTableWriter`, junto com `spark_conf={**iceberg_spark_conf(...), **SPARK_CONF}` |
| `--job-bookmark-option job-bookmark-enable` | Ao usar bookmarks (informe `transformation_ctx` no `GlueCatalogReader`) |

### 2.9 Código de exemplo

Job completo em `assets/template/src/`: lê imóveis do Glue Data Catalog e talhões em JSON no S3,
calcula a área plantada por imóvel e cultura e grava Parquet particionado por `dt`.

| Arquivo | O que demonstra |
|---|---|
| `main.py` | Orquestração, `JOB_ARGS` com os quatro tipos de parâmetro, `SPARK_CONF`, transformação via função e via classe, tratamento de erro e commit |
| `session/glue_session.py` | `DEFAULT_SPARK_CONF`, sobrescrita por job, `iceberg_spark_conf`, criação da sessão |
| `readers/` | Classe abstrata, classe intermediária com `__post_init__`, leitores de catálogo, Iceberg e S3 |
| `writers/` | Escrita idempotente em S3, tabela do catálogo (`insertInto` com reordenação de colunas) e Iceberg |
| `transformations/` | `BaseTransformation`, funções genéricas em `common.py` e três domínios compondo-se |
| `utils/` | `JobArg` / `get_job_args` com validação de maiúsculas e padrões; logger |

Parâmetros de negócio do exemplo: `--REFERENCE_DATE`, `--TALHOES_PATH`, `--TARGET_PATH`
(obrigatórios); `--IMOVEIS_DATABASE` e `--IMOVEIS_TABLE` (obrigatórios com padrão);
`--TALHOES_MULTILINE`, `--AREA_MINIMA_HA` e `--CASAS_DECIMAIS` (opcionais com padrão).

---

## 3. Infraestrutura

Planejado. Ainda sem regras definidas neste padrão.

## 4. Performance

Planejado. Ainda sem regras definidas neste padrão. As configurações Spark padrão e por job estão
na seção [2.4 Sessão Spark](#24-sessão-spark).

---

## Manutenção desta skill

- Toda mudança de regra atualiza esta skill **e** o código em `assets/template/src/` na mesma
  alteração, e incrementa `metadata.version` no cabeçalho.
- Novos tópicos entram como nova seção numerada e na tabela de [Tópicos](#tópicos). Se um tópico
  ficar extenso, mova o conteúdo para `references/<topico>.md` e deixe na seção um resumo e o link.
