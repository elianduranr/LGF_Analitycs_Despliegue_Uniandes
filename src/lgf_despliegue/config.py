from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class AppConfig:
    """Configuracion comun para local, Docker y VM."""

    data_dir: Path
    output_dir: Path
    mlflow_tracking_uri: str
    model_name: str = "lgf_forecast_solidos"


def load_config() -> AppConfig:
    data_dir = Path(os.getenv("LGF_DATA_DIR", "../bases de datos historicas"))
    output_dir = Path(os.getenv("LGF_OUTPUT_DIR", "outputs"))
    mlflow_uri = os.getenv("MLFLOW_TRACKING_URI", "mlruns")
    model_name = os.getenv("LGF_MODEL_NAME", "lgf_forecast_solidos")
    return AppConfig(
        data_dir=data_dir,
        output_dir=output_dir,
        mlflow_tracking_uri=mlflow_uri,
        model_name=model_name,
    )
