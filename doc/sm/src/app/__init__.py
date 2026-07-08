from typing import Optional
from fastapi import FastAPI
from src.app.routes import router
from src.app.handler import InferenceHandler


def create_app(handler: Optional[InferenceHandler] = None) -> FastAPI:
    app = FastAPI(title="SageMaker Batch Transform Inference Server")
    app.state.handler = handler
    app.include_router(router)
    return app
