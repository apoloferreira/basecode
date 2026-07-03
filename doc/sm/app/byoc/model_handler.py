import threading
import importlib.util
from pathlib import Path
from dataclasses import dataclass
from typing import Any, Callable

import torch


PreprocessFn = Callable[[Any], torch.Tensor]


@dataclass(frozen=True)
class ModelEntry:
    name: str
    path: Path


@dataclass
class ModelSpec:
    module: torch.nn.Module
    preprocess: PreprocessFn
    device: torch.device = torch.device("cuda") if torch.cuda.is_available() else torch.device("cpu")


class ModelCatalog:

    def __init__(self, models_root: Path) -> None:
        self._root = models_root
        self._entries: dict[str, ModelEntry] = {}

    def scan(self) -> None:
        """
        Procura por subdiretórios em models/* que contenham model.py e preprocess.py.
        """
        root = self._root
        if not root.exists() or not root.is_dir():
            raise FileNotFoundError(f"models_root not found or not a dir: {root}")

        entries: dict[str, ModelEntry] = {}
        for d in root.iterdir():
            if not d.is_dir():
                continue
            if (d / "model.py").is_file() and (d / "preprocess.py").is_file():
                entries[d.name] = ModelEntry(name=d.name, path=d)

        self._entries = entries

    def get(self, name: str) -> ModelEntry:
        entry = self._entries.get(name)
        if entry is None:
            raise KeyError(f"Model not found in catalog: {name}")
        return entry

    def list_models(self) -> tuple[str, ...]:
        return tuple(sorted(self._entries.keys()))


def _load_module_from_file(module_name: str, file_path: Path):
    spec = importlib.util.spec_from_file_location(module_name, str(file_path))
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot import from: {file_path}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)  # type: ignore[attr-defined]
    return mod


class ModelRegistry:

    def __init__(self, catalog: ModelCatalog) -> None:
        self._catalog = catalog
        self._cache: dict[str, ModelSpec] = {}
        self._lock = threading.RLock()

    def load(self, name: str) -> None:
        """
        Carrega o modelo do diretório:
          - model.py: build_model() -> nn.Module
          - preprocess.py: preprocess_fn(payload) -> torch.Tensor
        """
        with self._lock:
            if name in self._cache:
                return

            entry = self._catalog.get(name)
            model_py = entry.path / "model.py"
            prep_py = entry.path / "preprocess.py"

            # nomes únicos pra não colidir entre modelos
            model_mod = _load_module_from_file(f"models.{name}.model", model_py)
            prep_mod = _load_module_from_file(f"models.{name}.preprocess", prep_py)

            if not hasattr(model_mod, "build_model"):
                raise AttributeError(f"{model_py} must define build_model()")
            if not hasattr(prep_mod, "preprocess_fn"):
                raise AttributeError(f"{prep_py} must define preprocess_fn(payload)")

            build_model = getattr(model_mod, "build_model")
            preprocess = getattr(prep_mod, "preprocess_fn")

            device= torch.device("cuda") if torch.cuda.is_available() else torch.device("cpu")
            module: torch.nn.Module = build_model()
            module.to(device)
            module.eval()

            self._cache[name] = ModelSpec(module=module, preprocess=preprocess, device=device)

    def get(self, name: str) -> ModelSpec:
        with self._lock:
            m = self._cache.get(name)
            if m is None:
                raise KeyError(f"Model not loaded: {name}")
            return m

    def list_loaded(self) -> tuple[str, ...]:
        with self._lock:
            return tuple(sorted(self._cache.keys()))


# @dataclass
# class ModelBundle:
#     model: torch.nn.Module
#     device: torch.device
#     preprocess: PreprocessFn


# def load_model_bundle() -> ModelBundle:
#     device = "cuda" if torch.cuda.is_available() else "cpu"

#     # Exemplo: no model.tar.gz você colocou "model.pt"
#     model_path = os.path.join(settings.model_dir, "model.pt")

#     model = Resnet()
#     state = torch.load(model_path, map_location=device)
#     model.load_state_dict(state)
#     model.to(device)
#     model.eval()

#     preprocess = build_preprocess()
#     return ModelBundle(model=model, device=device, preprocess=preprocess)
