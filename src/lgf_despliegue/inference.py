from __future__ import annotations

import os
from pathlib import Path

import pandas as pd

from lgf_despliegue.data import load_sales_source
from lgf_despliegue.forecast import build_weekly_solid_demand


def _latest_trained_forecast(horizon_weeks: int) -> dict | None:
    output_dir = Path(os.getenv("LGF_OUTPUT_DIR", "outputs"))
    forecast_path = output_dir / "forecast" / "forecast_futuro.csv"
    evaluation_path = output_dir / "forecast" / "evaluacion_modelos.csv"
    if not forecast_path.exists():
        return None

    forecast = pd.read_csv(forecast_path).head(horizon_weeks)
    if forecast.empty:
        return None

    selected_model = str(forecast["modelo"].iloc[0]) if "modelo" in forecast.columns else "modelo_entrenado"
    metrics = {}
    if evaluation_path.exists():
        evaluation = pd.read_csv(evaluation_path)
        selected = evaluation[evaluation.get("modelo_seleccionado", False).astype(bool)]
        if not selected.empty:
            selected_model = str(selected["modelo"].iloc[0])
            metrics = {
                "mae": float(selected["mae"].iloc[0]),
                "rmse": float(selected["rmse"].iloc[0]),
                "wape": float(selected["wape"].iloc[0]),
            }

    predictions = [
        {
            "week_start": str(row["week_start"])[:10],
            "tallos_estimados": int(round(float(row["prediccion"]))),
            "modelo": selected_model,
        }
        for _, row in forecast.iterrows()
    ]
    return {
        "model": selected_model,
        "source": str(forecast_path),
        "horizon_weeks": horizon_weeks,
        "metrics": metrics,
        "predictions": predictions,
    }


def baseline_solid_forecast(
    data_dir: str,
    data_path: str | None = None,
    horizon_weeks: int = 8,
    lookback_weeks: int = 8,
) -> dict:
    """Inferencia baseline para la API mientras se consolida el modelo MLflow.

    Usa la mediana de las ultimas semanas de demanda SOLIDO confirmada. Es
    deliberadamente simple y estable para que la API sea ejecutable desde el
    primer despliegue; Julian puede reemplazar esta funcion por carga del mejor
    modelo registrado en MLflow.
    """
    trained = _latest_trained_forecast(horizon_weeks)
    if trained:
        return trained

    sales = load_sales_source(data_path=data_path, data_dir=data_dir)
    weekly = build_weekly_solid_demand(sales)
    if weekly.empty:
        return {"model": "baseline_mediana_reciente", "predictions": []}

    weekly = weekly.sort_values("week_start")
    recent = weekly.tail(max(1, lookback_weeks))
    estimate = int(round(float(recent["tallos"].median())))
    last_week = pd.to_datetime(weekly["week_start"].max())
    future_weeks = pd.date_range(last_week + pd.Timedelta(weeks=1), periods=horizon_weeks, freq="W-MON")
    predictions = [
        {
            "week_start": week.strftime("%Y-%m-%d"),
            "tallos_estimados": estimate,
            "modelo": "baseline_mediana_reciente",
        }
        for week in future_weeks
    ]
    return {
        "model": "baseline_mediana_reciente",
        "horizon_weeks": horizon_weeks,
        "lookback_weeks": lookback_weeks,
        "last_observed_week": last_week.strftime("%Y-%m-%d"),
        "predictions": predictions,
    }
