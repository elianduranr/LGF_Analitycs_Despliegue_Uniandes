from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class AppConfig:
    """Configuracion comun para local, Docker y VM."""

    data_dir: Path
    data_path: Path | None
    output_dir: Path
    mlflow_tracking_uri: str
    model_name: str = "lgf_forecast_solidos"


def load_config() -> AppConfig:
    data_dir = Path(os.getenv("LGF_DATA_DIR", "../bases de datos historicas"))
    raw_data_path = os.getenv("LGF_DATA_PATH", "").strip()
    data_path = Path(raw_data_path) if raw_data_path else None
    output_dir = Path(os.getenv("LGF_OUTPUT_DIR", "outputs"))
    mlflow_uri = os.getenv("MLFLOW_TRACKING_URI", "mlruns")
    model_name = os.getenv("LGF_MODEL_NAME", "lgf_forecast_solidos")
    return AppConfig(
        data_dir=data_dir,
        data_path=data_path,
        output_dir=output_dir,
        mlflow_tracking_uri=mlflow_uri,
        model_name=model_name,
    )
