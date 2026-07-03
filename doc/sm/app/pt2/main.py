import sys
import json
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI, Request, Response

from predictor import Predictor


@asynccontextmanager
async def lifespan(_app: FastAPI):
    _app.state.predictor = Predictor()
    _app.state.predictor.load()
    yield


app = FastAPI(lifespan=lifespan)


@app.get("/ping")
def ping(request: Request):
    if not request.app.state.predictor.is_ready():
        return Response(status_code=503)
    return Response(status_code=200)


@app.get("/execution-parameters")
def execution_parameters():
    return {
        "MaxConcurrentTransforms": 1,
        "BatchStrategy": "MULTI_RECORD",
        "MaxPayloadInMB": 6,
    }


@app.post("/invocations")
async def invocations(request: Request):
    predictor = request.app.state.predictor
    body = await request.body()
    lines = [ln for ln in body.decode().strip().split("\n") if ln.strip()]
    results = [predictor.predict(json.loads(line)) for line in lines]
    output = "\n".join(json.dumps(r, ensure_ascii=False) for r in results)
    return Response(content=output, media_type="application/jsonlines")


# SageMaker executa: docker run <image> serve
# O argumento "serve" chega via sys.argv[1] e deve iniciar o servidor.
if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "serve":
        uvicorn.run("main:app", host="0.0.0.0", port=8080, workers=1)
    else:
        print("Usage: python main.py serve")
        sys.exit(1)
