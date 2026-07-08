import torch
import uvicorn
from src.config import Settings
from src.logger import configure_logging, get_logger
from src.model_loader import ModelLoader
from src.app import create_app
from src.app.handler import InferenceHandler

logger = get_logger(__name__)


def build_app(settings: Settings) -> InferenceHandler:
    device = "cuda" if torch.cuda.is_available() else "cpu"
    logger.info(
        msg="Container starting",
        extra={
            "model_file": settings.model_file,
            "device": device,
            "use_fp16": settings.use_half_precision,
            "input_size": settings.input_size,
        },
    )

    torch.backends.cudnn.benchmark = True

    loader = ModelLoader(
        model_path=settings.model_path,
        use_half_precision=settings.use_half_precision,
        device=device,
    )
    loader.load()

    handler = InferenceHandler(
        model=loader.model,
        input_size=settings.input_size,
        use_half_precision=settings.use_half_precision,
        device=device,
    )

    return handler


def main():
    settings = Settings()
    configure_logging(settings.log_level)

    handler = build_app(settings)
    app = create_app(handler)

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=settings.port,
        workers=1,
        loop="uvloop",
        log_config=None,
    )


if __name__ == "__main__":
    main()
