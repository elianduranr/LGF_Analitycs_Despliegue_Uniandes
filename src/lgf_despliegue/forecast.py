from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd


@dataclass(frozen=True)
class ForecastConfig:
    test_weeks: int = 8
    min_train_weeks: int = 52
    experiment_name: str = "lgf_forecast_solidos"


def build_weekly_solid_demand(sales: pd.DataFrame) -> pd.DataFrame:
    solid = sales[sales["es_confirmado"] & sales["es_solido"]].copy()
    if solid.empty:
        return pd.DataFrame()
    weekly = solid.groupby(["week_start", "anio", "semana_iso"], as_index=False).agg(
        tallos=("tallos_demanda", "sum"),
        ventas_usd=("ventas_usd", "sum"),
        clientes=("cliente_analisis", "nunique"),
        producto_colores=("producto_color", "nunique"),
    )
    return weekly.sort_values("week_start").reset_index(drop=True)


def _add_features(weekly: pd.DataFrame) -> pd.DataFrame:
    out = weekly.sort_values("week_start").copy()
    out["t"] = np.arange(len(out))
    out["mes"] = out["week_start"].dt.month
    out["semana_sin"] = np.sin(2 * np.pi * out["semana_iso"] / 52)
    out["semana_cos"] = np.cos(2 * np.pi * out["semana_iso"] / 52)
    out["lag_1"] = out["tallos"].shift(1)
    out["lag_2"] = out["tallos"].shift(2)
    out["lag_4"] = out["tallos"].shift(4)
    out["rolling_4"] = out["tallos"].shift(1).rolling(4, min_periods=1).median()
    out["rolling_8"] = out["tallos"].shift(1).rolling(8, min_periods=1).median()
    prior = out[["anio", "semana_iso", "tallos"]].copy()
    prior["anio"] = prior["anio"] + 1
    prior = prior.rename(columns={"tallos": "same_week_prev_year"})
    out = out.merge(prior, on=["anio", "semana_iso"], how="left")
    return out.fillna(0)


def _wape(actual: pd.Series, predicted: pd.Series) -> float:
    denom = float(np.abs(actual).sum())
    return float(np.abs(actual - predicted).sum() / denom) if denom else np.nan


def _metrics(actual: pd.Series, predicted: pd.Series) -> dict[str, float]:
    from sklearn.metrics import mean_absolute_error, mean_squared_error

    rmse = mean_squared_error(actual, predicted) ** 0.5
    return {
        "mae": float(mean_absolute_error(actual, predicted)),
        "rmse": float(rmse),
        "wape": _wape(actual, predicted),
    }


def compare_models_with_mlflow(
    weekly: pd.DataFrame,
    tracking_uri: str | Path = "mlruns",
    artifact_dir: str | Path = "outputs/forecast",
    config: ForecastConfig | None = None,
) -> dict[str, pd.DataFrame]:
    """Compara modelos de forecast y registra cada corrida en MLflow."""
    config = config or ForecastConfig()
    if weekly.empty or weekly.shape[0] < config.min_train_weeks + config.test_weeks:
        raise ValueError(
            "No hay suficientes semanas para backtesting. "
            f"Se requieren al menos {config.min_train_weeks + config.test_weeks}."
        )

    import mlflow
    from sklearn.ensemble import HistGradientBoostingRegressor

    mlflow.set_tracking_uri(str(Path(tracking_uri).resolve()))
    mlflow.set_experiment(config.experiment_name)

    featured = _add_features(weekly)
    train = featured.iloc[: -config.test_weeks].copy()
    test = featured.iloc[-config.test_weeks :].copy()
    predictions = []

    baselines = {
        "baseline_mediana_8w": test["rolling_8"],
        "estacional_anio_anterior": test["same_week_prev_year"],
    }
    for model_name, pred in baselines.items():
        pred = pred.fillna(0).clip(lower=0)
        scores = _metrics(test["tallos"], pred)
        with mlflow.start_run(run_name=model_name):
            mlflow.log_params({"model_type": model_name, "test_weeks": config.test_weeks})
            mlflow.log_metrics(scores)
        predictions.append(test.assign(modelo=model_name, prediccion=pred.round(0)))

    feature_cols = [
        "t",
        "anio",
        "semana_iso",
        "mes",
        "semana_sin",
        "semana_cos",
        "lag_1",
        "lag_2",
        "lag_4",
        "rolling_4",
        "rolling_8",
        "same_week_prev_year",
        "clientes",
        "producto_colores",
    ]
    model = HistGradientBoostingRegressor(
        learning_rate=0.06,
        max_iter=150,
        max_leaf_nodes=31,
        min_samples_leaf=8,
        l2_regularization=0.1,
        random_state=42,
    )
    model.fit(train[feature_cols], train["tallos"])
    pred = pd.Series(model.predict(test[feature_cols]), index=test.index).clip(lower=0)
    scores = _metrics(test["tallos"], pred)
    with mlflow.start_run(run_name="hgb_regressor_semanal"):
        mlflow.log_params(
            {
                "model_type": "HistGradientBoostingRegressor",
                "test_weeks": config.test_weeks,
                "features": ",".join(feature_cols),
            }
        )
        mlflow.log_metrics(scores)
        mlflow.sklearn.log_model(model, artifact_path="model")
    predictions.append(test.assign(modelo="hgb_regressor_semanal", prediccion=pred.round(0)))

    pred_frame = pd.concat(predictions, ignore_index=True)
    pred_frame["error"] = pred_frame["prediccion"] - pred_frame["tallos"]
    pred_frame["error_abs"] = pred_frame["error"].abs()
    evaluation = (
        pred_frame.groupby("modelo", as_index=False)
        .apply(lambda g: pd.Series(_metrics(g["tallos"], g["prediccion"])), include_groups=False)
        .reset_index(drop=True)
        .sort_values(["wape", "rmse"])
    )
    best_model = evaluation.iloc[0]["modelo"]
    evaluation["modelo_seleccionado"] = evaluation["modelo"].eq(best_model)

    output = Path(artifact_dir)
    output.mkdir(parents=True, exist_ok=True)
    weekly.to_csv(output / "demanda_semanal_solidos.csv", index=False)
    evaluation.to_csv(output / "evaluacion_modelos.csv", index=False)
    pred_frame.to_csv(output / "predicciones_backtest.csv", index=False)
    return {"weekly": weekly, "evaluation": evaluation, "predictions": pred_frame}
