# =============================================================================
# Triton Inference Server — AWS DLC com boto3 + Pillow
#
# Base: imagem oficial AWS (já inclui /ping e /invocations para SageMaker).
# Apenas instalamos as dependências extras dos Python backends.
#
# Build (a partir do root do projeto):
#   aws ecr get-login-password --region us-east-1 \
#     | docker login --username AWS --password-stdin \
#       763104351884.dkr.ecr.us-east-1.amazonaws.com
#   docker build -f app/triton_aws/Dockerfile -t triton-aws .
# =============================================================================
FROM 763104351884.dkr.ecr.us-east-1.amazonaws.com/sagemaker-tritonserver:24.09-py3

RUN pip install --no-cache-dir \
    "boto3>=1.34" \
    "Pillow>=10.0"
