# =============================================================================
# Stage 1: builder
# Instala gcc/g++ (necessários para compilar uvloop e extensões C) e todas as
# dependências Python em um venv isolado. Ferramentas de build não vão para a
# imagem final.
# =============================================================================
FROM python:3.11-slim AS builder

WORKDIR /build

RUN apt-get update && apt-get install -y --no-install-recommends \
        gcc \
        g++ \
    && rm -rf /var/lib/apt/lists/*

RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

COPY requirements.txt .

# Instala PyTorch CPU-only primeiro (index URL separado para evitar baixar
# a variante CUDA, que ocupa ~2 GB a mais na imagem final).
# O job roda em ml.m5.large (CPU) e o modelo foi exportado em CPU.
RUN pip install --no-cache-dir \
        torch==2.8.0 torchvision==0.23.0 \
        --index-url https://download.pytorch.org/whl/cpu \
    && pip install --no-cache-dir -r requirements.txt

# =============================================================================
# Stage 2: runtime
# Imagem final leve: sem gcc/g++, apenas libgomp1 (dep de runtime do PyTorch
# para operações paralelas com OpenMP) + venv copiado do builder.
# =============================================================================
FROM python:3.11-slim AS runtime

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
        libgomp1 \
    && rm -rf /var/lib/apt/lists/*

COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

COPY . .

EXPOSE 8080

# SageMaker executa: docker run <image> serve
# O argumento "serve" chega via sys.argv[1] e é tratado em main.py.
# ENTRYPOINT é obrigatório — CMD seria substituído pelo "serve" e nunca executaria.
ENTRYPOINT ["python", "main.py"]
