from __future__ import annotations

import argparse
from pathlib import Path

from lgf_despliegue.data import load_historical_sales
from lgf_despliegue.forecast import build_weekly_solid_demand, compare_models_with_mlflow
from lgf_despliegue.sales import build_general_sales_outputs, write_sales_outputs


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Pipeline reducido LGF: ventas generales y forecast SOLIDO.")
    parser.add_argument(
        "--data-dir",
        default="../bases de datos historicas",
        help="Carpeta con ventas_facturadas_2021.csv ... ventas_facturadas_2026.csv",
    )
    parser.add_argument("--output-dir", default="outputs", help="Carpeta de salidas CSV.")
    parser.add_argument("--mlflow-uri", default="mlruns", help="Tracking URI local de MLflow.")
    parser.add_argument("--skip-forecast", action="store_true", help="Solo generar ventas generales.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    output_dir = Path(args.output_dir)
    sales = load_historical_sales(args.data_dir)

    sales_outputs = build_general_sales_outputs(sales)
    write_sales_outputs(sales_outputs, output_dir / "ventas_generales")

    if not args.skip_forecast:
        weekly = build_weekly_solid_demand(sales)
        compare_models_with_mlflow(
            weekly,
            tracking_uri=args.mlflow_uri,
            artifact_dir=output_dir / "forecast",
        )

    print(f"Pipeline terminado. Salidas en: {output_dir.resolve()}")


if __name__ == "__main__":
    main()
