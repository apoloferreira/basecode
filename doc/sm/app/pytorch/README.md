# SageMaker Script Mode — PyTorch DLC

Inferência batch com **SageMaker Script Mode** usando a DLC (Deep Learning Container) `pytorch-inference` gerenciada pela AWS.

Diferente da abordagem com container customizado (`app/pt2/`), aqui **não existe Dockerfile** — o código de inferência é empacotado junto ao modelo em um `.tar.gz` e o próprio DLC da AWS cuida do servidor HTTP, da instalação de dependências e do roteamento das requisições.

---

## Estrutura do diretório

```
app/pytorch/
├── inference.py      # As 4 funções do contrato Script Mode
├── s3_utils.py       # Download de imagens do S3
└── requirements.txt  # Dependências extras (boto3, pillow)
```

---

## Contrato Script Mode — as 4 funções

O DLC da AWS espera que `inference.py` exporte exatamente essas funções:

| Função | Chamada quando | Responsabilidade |
|---|---|---|
| `model_fn(model_dir)` | Container sobe (1x) | Carrega o modelo de `model_dir` e retorna o contexto de inferência |
| `input_fn(body, content_type)` | Cada POST `/invocations` | Deserializa o body HTTP recebido |
| `predict_fn(data, model_ctx)` | Cada POST `/invocations` | Executa a inferência e retorna os resultados |
| `output_fn(prediction, accept)` | Cada POST `/invocations` | Serializa os resultados para a resposta HTTP |

O DLC compõe o pipeline automaticamente:

```
POST /invocations
      │
      ▼
  input_fn(body, content_type)
      │  lista de dicts
      ▼
  predict_fn(data, model_ctx)
      │  lista de resultados
      ▼
  output_fn(prediction, accept)
      │  body + content-type
      ▼
  HTTP 200
```

---

## Ciclo de vida do container

Esta é a principal diferença em relação ao container customizado: as dependências **não estão baked na imagem** — elas são instaladas em runtime pelo próprio DLC a cada vez que o container sobe.

```
┌─────────────────────────────────────────────────────────────┐
│  SageMaker inicia a instância e faz pull da DLC             │
│  763104351884.dkr.ecr.<região>.amazonaws.com/               │
│  pytorch-inference:2.5.1-gpu-py311-cu121-ubuntu20.04-...    │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│  DLC extrai model.tar.gz → /opt/ml/model/                   │
│                                                             │
│  /opt/ml/model/                                             │
│  ├── ResNet18.pt2                                           │
│  └── code/                                                  │
│      ├── inference.py                                       │
│      ├── s3_utils.py                                        │
│      └── requirements.txt                                   │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│  pip install -r /opt/ml/model/code/requirements.txt         │
│                                                             │
│  ← Único momento de instalação por execução do job.         │
│    Pago uma vez, não por registro processado.               │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│  SAGEMAKER_PROGRAM=inference.py é importado                 │
│  model_fn("/opt/ml/model") é chamado → modelo carregado     │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│  Container pronto — GET /ping retorna 200                   │
│                                                             │
│  Batch Transform envia N requests POST /invocations         │
│  (SingleRecord + MaxConcurrentTransforms=8)                 │
│                                                             │
│  Para cada request:                                         │
│    input_fn → predict_fn → output_fn                        │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│  Job finalizado → container destruído                       │
│  Dependências instaladas são descartadas junto              │
└─────────────────────────────────────────────────────────────┘
```

---

## Estrutura do model.tar.gz

O arquivo precisa ter `ResNet18.pth` na raiz e os scripts sob `code/`. O DLC detecta a pasta `code/` automaticamente.

```
model_pytorch_script.tar.gz
├── ResNet18.pth          ← state dict (model_fn recebe o diretório pai como model_dir)
└── code/
    ├── inference.py      ← lido via SAGEMAKER_PROGRAM=inference.py
    ├── model.py          ← ResNet18Model (copiado de src/model.py pelo script de empacotamento)
    ├── s3_utils.py       ← importado por inference.py
    └── requirements.txt  ← instalado pelo DLC antes de chamar model_fn
```

Para gerar o tar.gz a partir da raiz do projeto:

```bash
python scripts/package_pytorch_script.py
# Saída: model_pytorch_script.tar.gz
```

Para fazer o upload ao S3:

```bash
aws s3 cp model_pytorch_script.tar.gz \
  s3://mlops-us-east-1-891377318910/sagemaker-batch-transform/refinamento/model/model_pytorch_script.tar.gz
```

---

## Formato dos dados

**Entrada** (cada linha do JSONL de input):
```json
{"record_id": "r0001", "image_s3_path": "s3://bucket/imagens/img.jpg"}
```

**Saída** (cada linha do JSONL de output):
```json
{"record_id": "r0001", "class_name": "metal", "score": 0.999757}
```

Diferente do Triton (KServe v2), não há envelope de tensores — o formato é JSON puro nos dois sentidos.

---

## Teste local (sem Docker)

As funções podem ser testadas diretamente em Python, simulando o que o DLC faz internamente:

```python
import sys, json
sys.path.insert(0, '.')  # raiz do projeto

from app.pytorch.inference import model_fn, input_fn, predict_fn, output_fn

# 1. Carrega o modelo (equivalente à inicialização do container)
model_ctx = model_fn('models/')

# 2. Simula uma requisição SingleRecord
body = json.dumps({
    "record_id": "teste1",
    "image_s3_path": "s3://bucket/input/cardboard1.jpg"
})

data        = input_fn(body, "application/json")
result      = predict_fn(data, model_ctx)
body, ctype = output_fn(result, "application/jsonlines")

print(body)
# {"record_id": "teste1", "class_name": "cardboard", "score": 0.999529}
```

---

## Deploy no SageMaker

```python
import boto3
import sagemaker

region     = "us-east-1"
account_id = boto3.client("sts").get_caller_identity()["Account"]

# URI da DLC (sem ECR próprio)
DLC_IMAGE_URI = sagemaker.image_uris.retrieve(
    framework     = "pytorch",
    region        = region,
    version       = "2.5.1",
    py_version    = "py311",
    image_scope   = "inference",
    instance_type = "ml.g4dn.xlarge",
)

sm_client = boto3.client("sagemaker", region_name=region)

# Criar modelo
sm_client.create_model(
    ModelName="resnet18-pytorch-script",
    PrimaryContainer={
        "Image":        DLC_IMAGE_URI,
        "ModelDataUrl": "s3://bucket/model_pytorch_script.tar.gz",
        "Environment": {
            "SAGEMAKER_PROGRAM": "inference.py",  # aponta para code/inference.py
        },
    },
    ExecutionRoleArn="arn:aws:iam::ACCOUNT:role/SageMakerExecutionRole",
)

# Criar Batch Transform Job
sm_client.create_transform_job(
    TransformJobName="batch-pytorch-script",
    ModelName="resnet18-pytorch-script",
    BatchStrategy="SingleRecord",
    MaxConcurrentTransforms=8,   # paralelismo de requests ao container
    MaxPayloadInMB=1,
    TransformInput={
        "DataSource": {"S3DataSource": {"S3DataType": "S3Prefix", "S3Uri": "s3://bucket/metadata/"}},
        "ContentType": "application/json",
        "SplitType":   "Line",
    },
    TransformOutput={
        "S3OutputPath": "s3://bucket/output/",
        "AssembleWith": "Line",
    },
    TransformResources={"InstanceType": "ml.g4dn.xlarge", "InstanceCount": 1},
)
```

---

## Comparação com container customizado (`app/pt2/`)

| | Script Mode (`app/pytorch/`) | Container customizado (`app/pt2/`) |
|---|---|---|
| Dockerfile | Não | Sim |
| Push para ECR | Não | Sim |
| Servidor HTTP | DLC gerencia | FastAPI + uvicorn |
| Formato do modelo | `.pth` (state dict) | `.pt2` (ExportedProgram) |
| Dependências | Instaladas em runtime (`pip install`) | Baked na imagem |
| Cold start | Mais lento (pip install) | Mais rápido |
| Manutenção | Baixa — só atualizar o tar.gz | Alta — rebuild + push a cada mudança |
| Flexibilidade | Limitada ao contrato das 4 funções | Total |

**Quando usar Script Mode:** prototipagem rápida, dependências leves, sem necessidade de customizar o servidor HTTP.

**Quando usar container customizado:** dependências pesadas que tornam o cold start inaceitável, necessidade de endpoints extras, controle total sobre o servidor.
