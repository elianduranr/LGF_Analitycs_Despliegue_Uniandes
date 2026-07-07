from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Callable
from urllib.parse import urlparse

import numpy as np
import pandas as pd


FEATURE_COLS = [
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


@dataclass(frozen=True)
class ForecastConfig:
    test_weeks: int = 8
    min_train_weeks: int = 52
    backtest_folds: int = 4
    forecast_horizon_weeks: int = 12
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


def _time_splits(n_rows: int, config: ForecastConfig) -> list[tuple[int, int, int]]:
    splits = []
    max_folds = min(config.backtest_folds, (n_rows - config.min_train_weeks) // config.test_weeks)
    for fold in range(max_folds):
        test_start = n_rows - (max_folds - fold) * config.test_weeks
        test_end = test_start + config.test_weeks
        if test_start >= config.min_train_weeks:
            splits.append((fold + 1, test_start, test_end))
    return splits


def _model_factories() -> dict[str, Callable[[], object]]:
    from sklearn.ensemble import HistGradientBoostingRegressor, RandomForestRegressor
    from sklearn.linear_model import Ridge

    return {
        "ridge_estacional": lambda: Ridge(alpha=1.0),
        "random_forest_semanal": lambda: RandomForestRegressor(
            n_estimators=250,
            max_depth=8,
            min_samples_leaf=4,
            random_state=42,
            n_jobs=-1,
        ),
        "hgb_regressor_semanal": lambda: HistGradientBoostingRegressor(
            learning_rate=0.06,
            max_iter=180,
            max_leaf_nodes=31,
            min_samples_leaf=8,
            l2_regularization=0.1,
            random_state=42,
        ),
    }


def _baseline_predictions(test: pd.DataFrame) -> dict[str, pd.Series]:
    return {
        "baseline_mediana_8w": test["rolling_8"].fillna(0).clip(lower=0),
        "estacional_anio_anterior": test["same_week_prev_year"].fillna(0).clip(lower=0),
    }


def _evaluate_backtests(featured: pd.DataFrame, config: ForecastConfig) -> tuple[pd.DataFrame, pd.DataFrame]:
    splits = _time_splits(len(featured), config)
    if not splits:
        raise ValueError(
            "No hay suficientes semanas para backtesting. "
            f"Se requieren al menos {config.min_train_weeks + config.test_weeks}."
        )

    predictions = []
    fold_scores = []
    factories = _model_factories()

    for fold, test_start, test_end in splits:
        train = featured.iloc[:test_start].copy()
        test = featured.iloc[test_start:test_end].copy()

        for model_name, pred in _baseline_predictions(test).items():
            scores = _metrics(test["tallos"], pred)
            fold_scores.append({"modelo": model_name, "fold": fold, **scores})
            predictions.append(
                test.assign(
                    modelo=model_name,
                    fold=fold,
                    prediccion=pred.round(0),
                    tipo_modelo="baseline",
                )
            )

        for model_name, factory in factories.items():
            model = factory()
            model.fit(train[FEATURE_COLS], train["tallos"])
            pred = pd.Series(model.predict(test[FEATURE_COLS]), index=test.index).clip(lower=0)
            scores = _metrics(test["tallos"], pred)
            fold_scores.append({"modelo": model_name, "fold": fold, **scores})
            predictions.append(
                test.assign(
                    modelo=model_name,
                    fold=fold,
                    prediccion=pred.round(0),
                    tipo_modelo="sklearn",
                )
            )

    pred_frame = pd.concat(predictions, ignore_index=True)
    pred_frame["error"] = pred_frame["prediccion"] - pred_frame["tallos"]
    pred_frame["error_abs"] = pred_frame["error"].abs()
    scores_frame = pd.DataFrame(fold_scores)
    return pred_frame, scores_frame


def _summarize_scores(scores_frame: pd.DataFrame) -> pd.DataFrame:
    evaluation = scores_frame.groupby("modelo", as_index=False).agg(
        mae=("mae", "mean"),
        rmse=("rmse", "mean"),
        wape=("wape", "mean"),
        mae_std=("mae", "std"),
        rmse_std=("rmse", "std"),
        wape_std=("wape", "std"),
        folds=("fold", "nunique"),
    )
    evaluation = evaluation.fillna(0).sort_values(["wape", "rmse", "mae"]).reset_index(drop=True)
    best_model = evaluation.iloc[0]["modelo"]
    evaluation["modelo_seleccionado"] = evaluation["modelo"].eq(best_model)
    evaluation["criterio_seleccion"] = np.where(
        evaluation["modelo_seleccionado"],
        "Menor WAPE promedio; desempate por RMSE y MAE.",
        "No seleccionado frente al menor WAPE promedio.",
    )
    return evaluation


def _future_frame(weekly: pd.DataFrame, horizon_weeks: int) -> pd.DataFrame:
    history = weekly.sort_values("week_start").copy()
    rows = []
    future_dates = pd.date_range(history["week_start"].max() + pd.Timedelta(weeks=1), periods=horizon_weeks, freq="W-MON")
    clientes_default = float(history["clientes"].tail(8).median())
    producto_colores_default = float(history["producto_colores"].tail(8).median())

    for week_start in future_dates:
        iso = week_start.isocalendar()
        rows.append(
            {
                "week_start": week_start,
                "anio": int(iso.year),
                "semana_iso": int(iso.week),
                "tallos": 0.0,
                "ventas_usd": 0.0,
                "clientes": clientes_default,
                "producto_colores": producto_colores_default,
            }
        )
    return pd.DataFrame(rows)


def _forecast_baseline(weekly: pd.DataFrame, horizon_weeks: int, model_name: str) -> pd.DataFrame:
    history = weekly.sort_values("week_start").copy()
    future = _future_frame(history, horizon_weeks)
    preds = []
    values = history["tallos"].tolist()
    prev_year = history.set_index(["anio", "semana_iso"])["tallos"].to_dict()

    for _, row in future.iterrows():
        if model_name == "estacional_anio_anterior":
            estimate = float(prev_year.get((int(row["anio"]) - 1, int(row["semana_iso"])), np.median(values[-8:])))
        else:
            estimate = float(np.median(values[-8:]))
        estimate = max(0.0, estimate)
        preds.append(estimate)
        values.append(estimate)

    return future.assign(modelo=model_name, prediccion=np.round(preds, 0), tipo_modelo="baseline")


def _forecast_sklearn(weekly: pd.DataFrame, model_name: str, horizon_weeks: int):
    factories = _model_factories()
    model = factories[model_name]()
    featured = _add_features(weekly)
    model.fit(featured[FEATURE_COLS], featured["tallos"])

    history = weekly.sort_values("week_start").copy()
    future_predictions = []
    for _ in range(horizon_weeks):
        future = _future_frame(history, 1)
        candidate = pd.concat([history, future], ignore_index=True)
        candidate_features = _add_features(candidate).tail(1)
        pred = float(model.predict(candidate_features[FEATURE_COLS])[0])
        pred = max(0.0, pred)
        future_row = future.iloc[0].copy()
        future_row["tallos"] = pred
        history = pd.concat([history, pd.DataFrame([future_row])], ignore_index=True)
        future_predictions.append({**future.iloc[0].to_dict(), "modelo": model_name, "prediccion": round(pred, 0), "tipo_modelo": "sklearn"})

    return pd.DataFrame(future_predictions), model


def _build_future_forecast(weekly: pd.DataFrame, selected_model: str, horizon_weeks: int) -> tuple[pd.DataFrame, object | None]:
    if selected_model in {"baseline_mediana_8w", "estacional_anio_anterior"}:
        return _forecast_baseline(weekly, horizon_weeks, selected_model), None
    return _forecast_sklearn(weekly, selected_model, horizon_weeks)


def _log_mlflow_runs(
    evaluation: pd.DataFrame,
    scores_frame: pd.DataFrame,
    predictions: pd.DataFrame,
    selected_model: str,
    selected_estimator: object | None,
    tracking_uri: str | Path,
    artifact_dir: Path,
    config: ForecastConfig,
) -> None:
    import mlflow

    parsed_uri = urlparse(str(tracking_uri))
    if parsed_uri.scheme in {"http", "https", "file", "sqlite", "postgresql", "mysql", "mssql", "databricks", "databricks-uc", "uc"}:
        mlflow.set_tracking_uri(str(tracking_uri))
    else:
        mlflow.set_tracking_uri(Path(tracking_uri).resolve().as_uri())
    mlflow.set_experiment(config.experiment_name)

    for _, row in evaluation.iterrows():
        model_name = row["modelo"]
        model_scores = scores_frame[scores_frame["modelo"].eq(model_name)]
        model_predictions = predictions[predictions["modelo"].eq(model_name)]
        with mlflow.start_run(run_name=str(model_name)):
            mlflow.log_params(
                {
                    "model_name": model_name,
                    "test_weeks": config.test_weeks,
                    "backtest_folds": int(row["folds"]),
                    "forecast_horizon_weeks": config.forecast_horizon_weeks,
                    "features": ",".join(FEATURE_COLS) if row["modelo"] not in {"baseline_mediana_8w", "estacional_anio_anterior"} else "historical_tallos",
                }
            )
            mlflow.log_metrics({"mae": row["mae"], "rmse": row["rmse"], "wape": row["wape"]})
            mlflow.set_tags(
                {
                    "selected_model": str(bool(row["modelo_seleccionado"])),
                    "selection_criterion": row["criterio_seleccion"],
                    "business_scope": "forecast_SOLIDO_weekly_confirmed_stems",
                }
            )
            fold_path = artifact_dir / f"fold_metrics_{model_name}.csv"
            pred_path = artifact_dir / f"backtest_{model_name}.csv"
            model_scores.to_csv(fold_path, index=False)
            model_predictions.to_csv(pred_path, index=False)
            mlflow.log_artifact(str(fold_path), artifact_path="evaluation")
            mlflow.log_artifact(str(pred_path), artifact_path="evaluation")
            if model_name == selected_model and selected_estimator is not None:
                mlflow.sklearn.log_model(selected_estimator, artifact_path="model")


def compare_models_with_mlflow(
    weekly: pd.DataFrame,
    tracking_uri: str | Path = "mlruns",
    artifact_dir: str | Path = "outputs/forecast",
    config: ForecastConfig | None = None,
) -> dict[str, pd.DataFrame]:
    """Compara modelos de forecast, registra corridas en MLflow y exporta salidas."""
    config = config or ForecastConfig()
    if weekly.empty or weekly.shape[0] < config.min_train_weeks + config.test_weeks:
        raise ValueError(
            "No hay suficientes semanas para backtesting. "
            f"Se requieren al menos {config.min_train_weeks + config.test_weeks}."
        )

    featured = _add_features(weekly)
    predictions, scores_frame = _evaluate_backtests(featured, config)
    evaluation = _summarize_scores(scores_frame)
    selected_model = str(evaluation.loc[evaluation["modelo_seleccionado"], "modelo"].iloc[0])
    future, estimator = _build_future_forecast(weekly, selected_model, config.forecast_horizon_weeks)

    output = Path(artifact_dir)
    output.mkdir(parents=True, exist_ok=True)
    weekly.to_csv(output / "demanda_semanal_solidos.csv", index=False)
    evaluation.to_csv(output / "evaluacion_modelos.csv", index=False)
    scores_frame.to_csv(output / "metricas_backtest_folds.csv", index=False)
    predictions.to_csv(output / "predicciones_backtest.csv", index=False)
    future.to_csv(output / "forecast_futuro.csv", index=False)

    _log_mlflow_runs(
        evaluation=evaluation,
        scores_frame=scores_frame,
        predictions=predictions,
        selected_model=selected_model,
        selected_estimator=estimator,
        tracking_uri=tracking_uri,
        artifact_dir=output,
        config=config,
    )
    return {"weekly": weekly, "evaluation": evaluation, "fold_metrics": scores_frame, "predictions": predictions, "future": future}
