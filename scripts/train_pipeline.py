from __future__ import annotations

import os
from pathlib import Path

import pandas as pd

from lgf_despliegue.config import load_config
from lgf_despliegue.data import load_sales_source
from lgf_despliegue.forecast import build_weekly_solid_demand, compare_models_with_mlflow
from lgf_despliegue.sales import build_general_sales_outputs, write_sales_outputs


def main() -> None:
    config = load_config()
    weekly_path = Path(os.getenv("LGF_WEEKLY_PATH", "datos/processed/demanda_semanal_solidos.csv"))
    if weekly_path.exists():
        weekly = pd.read_csv(weekly_path, parse_dates=["week_start"])
        print(f"Entrenando forecast desde serie semanal liviana: {weekly_path}")
    else:
        sales = load_sales_source(data_path=config.data_path, data_dir=config.data_dir)
        write_sales_outputs(build_general_sales_outputs(sales), config.output_dir / "ventas_generales")
        weekly = build_weekly_solid_demand(sales)
    compare_models_with_mlflow(
        weekly,
        tracking_uri=config.mlflow_tracking_uri,
        artifact_dir=Path(config.output_dir) / "forecast",
    )
    print("Entrenamiento/evaluacion finalizado.")


if __name__ == "__main__":
    main()
