# Servidor de Inferência — SageMaker Batch Transform

Servidor FastAPI customizado para classificação de imagens com ResNet18, projetado para rodar como contêiner no **AWS SageMaker Batch Transform**.

## Arquitetura

```
app/
├── main.py          # FastAPI: /ping, /invocations, /execution-parameters
├── predictor.py     # Classe Predictor: carregamento e inferência
├── s3_utils.py      # Download de imagens do S3 via boto3
├── requirements.txt
└── Dockerfile
```

**Endpoints implementados:**

| Endpoint | Método | Descrição |
|---|---|---|
| `/ping` | GET | Health check — 200 se modelo carregado, 503 caso contrário |
| `/invocations` | POST | Inferência em batch (JSONL) |
| `/execution-parameters` | GET | Parâmetros de configuração do job |

**Formato JSONL de entrada:**
```jsonl
{"record_id": "abc", "image_s3_path": "s3://meu-bucket/imagens/img1.jpg"}
{"record_id": "def", "image_s3_path": "s3://meu-bucket/imagens/img2.jpg"}
```

**Formato JSONL de saída:**
```jsonl
{"record_id": "abc", "classe": "glass", "score": 0.9512}
{"record_id": "def", "classe": "cardboard", "score": 0.8843}
```

---

## Pré-requisitos

- Docker
- AWS CLI configurado (`aws configure`)
- Permissões IAM: `ecr:*`, `s3:GetObject`, `sagemaker:*`

---

## 1. Build da imagem Docker

```bash
# A partir da raiz do projeto (diretório refinamento/)
docker build -t resnet18-batch-transform .
```

---

## 2. Teste local

O modelo precisa estar montado em `/opt/ml/model/`. As credenciais AWS são usadas para acessar o S3.

> **Atenção:** os comandos abaixo devem ser executados a partir do diretório raiz do projeto
> (`refinamento/`). Defina `PROJECT_ROOT` uma vez e use em todos os comandos para evitar
> erros de caminho com `$(pwd)`.

```bash
# Execute este comando UMA VEZ antes de qualquer docker run
PROJECT_ROOT=/home/apolo/Dropbox/programacao/Itau/sandbox/prd_sens_remoto_models/refinamento
```

> Os comandos `curl` exigem que o contêiner esteja rodando.
> Inicie-o em um terminal separado **antes** de executar os testes, ou use a opção com `--detach`.

### Opção A — terminal separado (recomendado)

**Terminal 1 — iniciar o servidor:**

```bash
# Opção 1: montar ~/.aws do host (recomendado para testes locais)
docker run --rm \
  -p 8080:8080 \
  -v $PROJECT_ROOT/model_artifacts:/opt/ml/model \
  -v $HOME/.aws:/root/.aws:ro \
  -e AWS_DEFAULT_REGION=us-east-1 \
  resnet18-batch-transform serve

# Opção 2: passar credenciais por variável de ambiente
docker run --rm \
  -p 8080:8080 \
  -v $PROJECT_ROOT/model_artifacts:/opt/ml/model \
  -e AWS_DEFAULT_REGION=us-east-1 \
  -e AWS_ACCESS_KEY_ID=$AWS_ACCESS_KEY_ID \
  -e AWS_SECRET_ACCESS_KEY=$AWS_SECRET_ACCESS_KEY \
  -e AWS_SESSION_TOKEN=$AWS_SESSION_TOKEN \
  resnet18-batch-transform serve
# Aguarde a mensagem: Application startup complete.
```

**Terminal 2 — executar os testes:**

```bash
# Health check
curl -s -o /dev/null -w "%{http_code}\n" http://localhost:8080/ping
# Esperado: 200

# Execution parameters
curl -s http://localhost:8080/execution-parameters | python3 -m json.tool

# Inferência simples
echo '{"record_id":"t1","image_s3_path":"s3://mlops-us-east-1-891377318910/sagemaker-batch-transform/refinamento/input/trash1.jpg"}' | \
curl -s -X POST http://localhost:8080/invocations \
     -H "Content-Type: application/jsonlines" \
     --data-binary @-

# Inferência MultiRecord
printf '{"record_id":"r1","image_s3_path":"s3://mlops-us-east-1-891377318910/sagemaker-batch-transform/refinamento/input/trash1.jpg"}\n{"record_id":"r2","image_s3_path":"s3://mlops-us-east-1-891377318910/sagemaker-batch-transform/refinamento/input/plastic1.jpg"}\n' | \
curl -s -X POST http://localhost:8080/invocations \
     -H "Content-Type: application/jsonlines" \
     --data-binary @-
```

### Opção B — background com --detach

```bash
# Inicia em background e guarda o ID do contêiner
CONTAINER_ID=$(docker run -d --rm \
  -p 8080:8080 \
  -v $PROJECT_ROOT/model_artifacts:/opt/ml/model \
  -e AWS_DEFAULT_REGION=us-east-1 \
  -e AWS_ACCESS_KEY_ID=$AWS_ACCESS_KEY_ID \
  -e AWS_SECRET_ACCESS_KEY=$AWS_SECRET_ACCESS_KEY \
  resnet18-batch-transform serve)

# Aguarda o modelo carregar (~10s)
sleep 12

# Testes
curl -s -o /dev/null -w "ping: %{http_code}\n" http://localhost:8080/ping
curl -s http://localhost:8080/execution-parameters | python3 -m json.tool

# Para o contêiner ao finalizar
docker stop $CONTAINER_ID
```

---

## 3. Criar repositório no ECR

```bash
# Variáveis — ajuste conforme seu ambiente
AWS_REGION="us-east-1"
AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
ECR_REPO_NAME="resnet18-batch-transform"

# Criar repositório
aws ecr create-repository \
  --repository-name $ECR_REPO_NAME \
  --region $AWS_REGION
```

---

## 4. Autenticar Docker no ECR

```bash
aws ecr get-login-password --region $AWS_REGION | \
docker login \
  --username AWS \
  --password-stdin \
  ${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com
```

```bash
aws ecr get-login-password --region us-east-1 | \
docker login --username AWS --password-stdin 891377318910.dkr.ecr.us-east-1.amazonaws.com
```

---

## 5. Tag e push da imagem

```bash
ECR_IMAGE_URI="891377318910.dkr.ecr.us-east-1.amazonaws.com/sm-batch-transform-refinamento:latest"

# Tag
docker tag resnet18-batch-transform $ECR_IMAGE_URI

# Push
docker push $ECR_IMAGE_URI
```

---

## 6. Upload do model.tar.gz para o S3

```bash
S3_BUCKET="meu-bucket-modelos"
S3_MODEL_PREFIX="models/resnet18"

aws s3 cp model.tar.gz s3://${S3_BUCKET}/${S3_MODEL_PREFIX}/model.tar.gz
```

---

## 7. Criar SageMaker Model

```bash
SAGEMAKER_ROLE_ARN="arn:aws:iam::${AWS_ACCOUNT_ID}:role/SageMakerExecutionRole"
MODEL_NAME="resnet18-classifier-$(date +%Y%m%d%H%M%S)"

aws sagemaker create-model \
  --model-name $MODEL_NAME \
  --primary-container \
    Image=${ECR_IMAGE_URI},\
ModelDataUrl=s3://${S3_BUCKET}/${S3_MODEL_PREFIX}/model.tar.gz \
  --execution-role-arn $SAGEMAKER_ROLE_ARN \
  --region $AWS_REGION

echo "SageMaker Model criado: $MODEL_NAME"
```

---

## 8. Criar Batch Transform Job

```bash
JOB_NAME="batch-job-$(date +%Y%m%d%H%M%S)"
INPUT_S3="s3://meu-bucket/input/"       # prefixo com arquivos .jsonl
OUTPUT_S3="s3://meu-bucket/output/"

aws sagemaker create-transform-job \
  --transform-job-name $JOB_NAME \
  --model-name $MODEL_NAME \
  --max-concurrent-transforms 1 \
  --batch-strategy MultiRecord \
  --max-payload-in-mb 6 \
  --transform-input \
    DataSource={S3DataSource={S3DataType=S3Prefix,S3Uri=${INPUT_S3}}},\
ContentType=application/jsonlines,\
SplitType=Line \
  --transform-output \
    S3OutputPath=${OUTPUT_S3},\
AssembleWith=Line \
  --transform-resources \
    InstanceType=ml.m5.large,InstanceCount=1 \
  --region $AWS_REGION

echo "Batch Transform Job iniciado: $JOB_NAME"
```

### Acompanhar status do job

```bash
aws sagemaker describe-transform-job \
  --transform-job-name $JOB_NAME \
  --query 'TransformJobStatus' \
  --output text \
  --region $AWS_REGION
```

---

## Observações

- **`SplitType=Line`** — SageMaker divide o arquivo JSONL por linha antes de enviar ao contêiner.
- **`AssembleWith=Line`** — SageMaker concatena as respostas linha a linha no arquivo de saída.
- A role do SageMaker precisa ter acesso de leitura ao S3 das imagens (`s3:GetObject` no bucket das imagens).
- O contêiner acessa o S3 com as credenciais da role do job — não são necessárias credenciais hardcoded.
