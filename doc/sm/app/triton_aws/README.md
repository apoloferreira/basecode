# Triton Inference Server — AWS DLC + dependências próprias

Pipeline ensemble ResNet18 ONNX para classificação de materiais recicláveis (6 classes).

Usa a imagem oficial AWS (`sagemaker-tritonserver:24.09-py3`) como base — ela já inclui o
middleware SageMaker (`/ping` e `/invocations`). Um Dockerfile mínimo acrescenta `boto3` e
`Pillow`, que não estão presentes na imagem base.

Diferente de `app/onnx` (imagem NVIDIA + proxy customizado), aqui não há serve script nem nginx.

---

## Estrutura

```
app/triton_aws/
├── Dockerfile                        # FROM sagemaker-tritonserver + pip install
├── deploy/
│   └── buildspec.yml                 # CodeBuild: build + push para ECR próprio
└── model_repository/
    ├── classifier/                   # backend onnxruntime — ResNet18.onnx
    │   ├── 1/model.onnx              # gerado antes de empacotar (não versionado)
    │   └── config.pbtxt
    ├── preprocess/                   # backend python — download S3 + resize + normalize
    │   ├── 1/model.py
    │   └── config.pbtxt
    ├── postprocess/                  # backend python — argmax + nome da classe
    │   ├── 1/model.py
    │   └── config.pbtxt
    └── pipeline/                     # ensemble: preprocess → classifier → postprocess
        └── config.pbtxt
```

---

## Imagens ECR

| Imagem | URI |
|--------|-----|
| Base AWS DLC | `763104351884.dkr.ecr.us-east-1.amazonaws.com/sagemaker-tritonserver:24.09-py3` |
| Imagem própria (após build) | `891377318910.dkr.ecr.us-east-1.amazonaws.com/sm-batch-transform-triton-aws:latest` |

> **Por que 24.09-py3?** O `ml.g4dn.xlarge` tem kernel driver 470.x. A versão `26.03-py3`
> usa CUDA 12.9+, que exige driver ≥ 525 — causa error 803 na inicialização do Triton.
> A versão `24.09-py3` usa CUDA 12.6 com forward compatibility, que funciona no driver 470.x.

---

## 1 — Empacotar o modelo

```bash
# Copiar o ONNX para o model_repository
cp models/ResNet18.onnx app/triton_aws/model_repository/classifier/1/model.onnx

# Empacotar (a raiz do tar deve conter os subdiretórios dos modelos diretamente)
tar -czf model_sagemaker/model_triton_aws.tar.gz -C app/triton_aws/model_repository .

# Upload para S3
aws s3 cp model_sagemaker/model_triton_aws.tar.gz \
  s3://mlops-us-east-1-891377318910/sagemaker-batch-transform/refinamento/model/model_triton_aws.tar.gz
```

---

## 2 — Build e push da imagem Docker

### Build local

```bash
# Autenticar na DLC ECR (para pull da imagem base)
aws ecr get-login-password --region us-east-1 \
  | docker login --username AWS --password-stdin \
    763104351884.dkr.ecr.us-east-1.amazonaws.com

# Build
docker build -f app/triton_aws/Dockerfile -t triton-aws:latest .

# Autenticar no nosso ECR e fazer push
aws ecr get-login-password --region us-east-1 \
  | docker login --username AWS --password-stdin \
    891377318910.dkr.ecr.us-east-1.amazonaws.com

docker tag triton-aws:latest \
  891377318910.dkr.ecr.us-east-1.amazonaws.com/sm-batch-transform-triton-aws:latest

docker push \
  891377318910.dkr.ecr.us-east-1.amazonaws.com/sm-batch-transform-triton-aws:latest
```

### Via CodeBuild

O `buildspec.yml` em `deploy/` automatiza o build e o push.
Configure um projeto CodeBuild apontando para este repositório com `app/triton_aws/deploy/buildspec.yml`.

---

## 3 — Teste local

```bash
# Opção A: credenciais via volume ~/.aws
docker run --gpus all -p 8080:8080 \
  -e SAGEMAKER_TRITON_DEFAULT_MODEL_NAME=pipeline \
  -e ALLOWED_S3_BUCKETS=mlops-us-east-1-891377318910 \
  -v "$HOME/.aws:/root/.aws:ro" \
  -v "$(pwd)/app/triton_aws/model_repository:/opt/ml/model" \
  891377318910.dkr.ecr.us-east-1.amazonaws.com/sm-batch-transform-triton-aws:latest \
  serve

# Opção B: credenciais via variáveis de ambiente
docker run --gpus all -p 8080:8080 \
  -e SAGEMAKER_TRITON_DEFAULT_MODEL_NAME=pipeline \
  -e ALLOWED_S3_BUCKETS=mlops-us-east-1-891377318910 \
  -e AWS_ACCESS_KEY_ID \
  -e AWS_SECRET_ACCESS_KEY \
  -e AWS_SESSION_TOKEN \
  -e AWS_DEFAULT_REGION \
  -v "$(pwd)/app/triton_aws/model_repository:/opt/ml/model" \
  891377318910.dkr.ecr.us-east-1.amazonaws.com/sm-batch-transform-triton-aws:latest \
  serve
```

### Invocação via /invocations

```bash
# Health check
curl http://localhost:8080/ping

# Inferência
curl -s http://localhost:8080/invocations \
  -H 'Content-Type: application/json' \
  -d '{
    "inputs": [
      {"name": "record_id",     "shape": [1,1], "datatype": "BYTES", "data": ["cardboard1"]},
      {"name": "image_s3_path", "shape": [1,1], "datatype": "BYTES",
       "data": ["s3://mlops-us-east-1-891377318910/sagemaker-batch-transform/refinamento/input/cardboard1.jpg"]}
    ]
  }'
```

---

## 4 — Deploy via Batch Transform

Ver `notebooks/invocation_triton_aws.ipynb`.

Pontos-chave:
- `Image`: `891377318910.dkr.ecr.us-east-1.amazonaws.com/sm-batch-transform-triton-aws:latest`
- `ModelDataUrl`: `s3://.../model_triton_aws.tar.gz`
- `Environment`:
  - `SAGEMAKER_TRITON_DEFAULT_MODEL_NAME=pipeline` — obrigatório para ensemble
  - `ALLOWED_S3_BUCKETS=mlops-us-east-1-891377318910`
- `SplitType: "Line"`, `BatchStrategy: "SingleRecord"` — cada linha do JSONL vira um request
- `ContentType: "application/json"`
- Input JSONL: uma linha por imagem, cada linha é um request KServe v2 completo
