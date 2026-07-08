FROM pytorch/pytorch:2.3.1-cuda12.1-cudnn8-runtime

# libGL necessário para Pillow com JPEG/PNG
RUN apt-get update && apt-get install -y --no-install-recommends \
        libgl1 \
        libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH=/opt/program

WORKDIR /opt/program

# Camada cacheável: dependências raramente mudam
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Código fonte: camada mais volátil
COPY serve .
COPY src/ src/

RUN chmod +x serve

EXPOSE 8080

ENTRYPOINT ["python", "serve"]
