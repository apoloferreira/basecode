import os
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class Settings:
    model_dir: str = field(default_factory=lambda: os.getenv("SM_MODEL_DIR", "/opt/ml/model"))
    model_file: str = field(default_factory=lambda: os.getenv("MODEL_FILE", "model.pt"))
    input_size: int = field(default_factory=lambda: int(os.getenv("INPUT_SIZE", "224")))
    use_half_precision: bool = field(
        default_factory=lambda: os.getenv("USE_HALF_PRECISION", "false").lower() == "true"
    )
    log_level: str = field(default_factory=lambda: os.getenv("LOG_LEVEL", "INFO").upper())
    port: int = field(default_factory=lambda: int(os.getenv("PORT", "8080")))
    sagemaker_batch: bool = field(
        default_factory=lambda: os.getenv("SAGEMAKER_BATCH", "false").lower() == "true"
    )
    max_payload_mb: int = field(
        default_factory=lambda: int(os.getenv("SAGEMAKER_MAX_PAYLOAD_IN_MB", "6"))
    )
    batch_strategy: str = field(
        default_factory=lambda: os.getenv("SAGEMAKER_BATCH_STRATEGY", "MULTI_RECORD")
    )
    max_concurrent_transforms: int = field(
        default_factory=lambda: int(os.getenv("SAGEMAKER_MAX_CONCURRENT_TRANSFORMS", "1"))
    )

    @property
    def model_path(self) -> str:
        return str(Path(self.model_dir) / self.model_file)
