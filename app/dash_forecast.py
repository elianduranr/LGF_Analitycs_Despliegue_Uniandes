from __future__ import annotations

import argparse
import os
from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from dash import Dash, Input, Output, dash_table, dcc, html

from app.dash_ventas import CORPORATE_BURGUNDY, CORPORATE_SEQUENCE, GRAPH_TEXT, apply_layout, metric_card, money, table
from lgf_despliegue.config import load_config
from lgf_despliegue.data import load_sales_source
from lgf_despliegue.forecast import build_weekly_solid_demand


def percent_plain(value: float | None) -> str:
    if value is None or pd.isna(value):
        return "NA"
    return f"{float(value):.1%}".replace(".", ",")


def empty_figure(title: str) -> go.Figure:
    fig = go.Figure()
    fig.add_annotation(text="Sin datos disponibles. Ejecuta primero tox run -e train.", x=0.5, y=0.5, showarrow=False)
    fig.update_layout(title=title)
    return apply_layout(fig, 340)


def read_csv_if_exists(path: Path, date_cols: list[str] | None = None) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame()
    return pd.read_csv(path, parse_dates=date_cols or [])


def load_forecast_outputs(output_dir: str | Path) -> dict[str, pd.DataFrame]:
    root = Path(output_dir) / "forecast"
    return {
        "weekly": read_csv_if_exists(root / "demanda_semanal_solidos.csv", ["week_start"]),
        "evaluation": read_csv_if_exists(root / "evaluacion_modelos.csv"),
        "fold_metrics": read_csv_if_exists(root / "metricas_backtest_folds.csv"),
        "backtest": read_csv_if_exists(root / "predicciones_backtest.csv", ["week_start"]),
        "future": read_csv_if_exists(root / "forecast_futuro.csv", ["week_start"]),
    }


def load_weekly_from_data(data_path: str | None, data_dir: str | None) -> pd.DataFrame:
    if not data_path and not data_dir:
        return pd.DataFrame()
    try:
        sales = load_sales_source(data_path=data_path, data_dir=data_dir)
    except Exception:
        return pd.DataFrame()
    return build_weekly_solid_demand(sales)


def prepare_dashboard_data(data_path: str | None, data_dir: str | None, output_dir: str | Path) -> dict[str, pd.DataFrame]:
    data = load_forecast_outputs(output_dir)
    if data["weekly"].empty:
        data["weekly"] = load_weekly_from_data(data_path, data_dir)
    return data


def evaluation_table(evaluation: pd.DataFrame) -> dash_table.DataTable:
    if evaluation.empty:
        return table(pd.DataFrame({"mensaje": ["Ejecuta tox run -e train para generar evaluacion_modelos.csv."]}))
    view = evaluation.copy()
    for col in ["mae", "rmse"]:
        if col in view:
            view[col] = view[col].map(lambda value: money(value, 0))
    for col in ["wape", "wape_std"]:
        if col in view:
            view[col] = view[col].map(percent_plain)
    return table(view, page_size=8, sort_by=[{"column_id": "wape", "direction": "asc"}])


def build_metric_cards(data: dict[str, pd.DataFrame]) -> list[html.Div]:
    weekly = data["weekly"]
    evaluation = data["evaluation"]
    future = data["future"]
    selected = evaluation[evaluation.get("modelo_seleccionado", False).astype(bool)] if not evaluation.empty else pd.DataFrame()
    selected_name = str(selected["modelo"].iloc[0]) if not selected.empty else "Pendiente"
    selected_wape = percent_plain(selected["wape"].iloc[0]) if not selected.empty else "NA"
    selected_rmse = money(selected["rmse"].iloc[0], 0) if not selected.empty else "NA"
    last_week = pd.to_datetime(weekly["week_start"]).max().strftime("%Y-%m-%d") if not weekly.empty else "NA"
    horizon = len(future) if not future.empty else 0
    total_future = float(future["prediccion"].sum()) if not future.empty else 0.0

    return [
        metric_card("Modelo seleccionado", selected_name, "Criterio: menor WAPE promedio"),
        metric_card("WAPE backtest", selected_wape, "Error porcentual ponderado"),
        metric_card("RMSE backtest", selected_rmse, "Error promedio cuadratico"),
        metric_card("Ultima semana observada", last_week, "Demanda SOLIDO confirmada"),
        metric_card("Horizonte", f"{horizon} semanas", "Forecast futuro exportado"),
        metric_card("Tallos estimados", money(total_future, 0), "Suma del horizonte"),
    ]


def build_figures(data: dict[str, pd.DataFrame]) -> dict[str, go.Figure]:
    weekly = data["weekly"]
    evaluation = data["evaluation"]
    backtest = data["backtest"]
    future = data["future"]

    if weekly.empty:
        weekly_fig = empty_figure("Demanda semanal SOLIDO")
    else:
        weekly_fig = px.line(weekly, x="week_start", y="tallos", title="Demanda semanal SOLIDO", markers=False)
        weekly_fig.update_traces(line=dict(color=CORPORATE_BURGUNDY, width=2))
        weekly_fig = apply_layout(weekly_fig, 360)

    if evaluation.empty:
        eval_fig = empty_figure("Comparacion de modelos")
    else:
        eval_view = evaluation.sort_values("wape", ascending=True)
        eval_fig = px.bar(eval_view, x="modelo", y="wape", title="WAPE promedio por modelo", color="modelo", color_discrete_sequence=CORPORATE_SEQUENCE)
        eval_fig.update_yaxes(tickformat=".1%")
        eval_fig = apply_layout(eval_fig, 360)

    if backtest.empty:
        backtest_fig = empty_figure("Backtesting")
    else:
        selected = evaluation[evaluation.get("modelo_seleccionado", False).astype(bool)]
        selected_name = str(selected["modelo"].iloc[0]) if not selected.empty else str(backtest["modelo"].iloc[0])
        view = backtest[backtest["modelo"].eq(selected_name)].copy()
        backtest_fig = go.Figure()
        backtest_fig.add_trace(go.Scatter(x=view["week_start"], y=view["tallos"], mode="lines+markers", name="Real", line=dict(color=GRAPH_TEXT)))
        backtest_fig.add_trace(go.Scatter(x=view["week_start"], y=view["prediccion"], mode="lines+markers", name="Prediccion", line=dict(color=CORPORATE_BURGUNDY)))
        backtest_fig.update_layout(title=f"Backtesting - {selected_name}")
        backtest_fig = apply_layout(backtest_fig, 360)

    if future.empty:
        future_fig = empty_figure("Forecast futuro")
    else:
        future_fig = px.bar(future, x="week_start", y="prediccion", title="Forecast futuro SOLIDO", color_discrete_sequence=[CORPORATE_BURGUNDY])
        future_fig = apply_layout(future_fig, 360)

    return {"weekly": weekly_fig, "evaluation": eval_fig, "backtest": backtest_fig, "future": future_fig}


def make_app(data_path: str | None = None, data_dir: str | None = None, output_dir: str | Path | None = None) -> Dash:
    config = load_config()
    source_path = data_path or (str(config.data_path) if config.data_path else None)
    source_dir = data_dir or str(config.data_dir)
    forecast_output_dir = output_dir or config.output_dir
    data = prepare_dashboard_data(source_path, source_dir, forecast_output_dir)
    models = sorted(data["backtest"]["modelo"].dropna().unique().tolist()) if not data["backtest"].empty else []

    app = Dash(__name__, title="LGF Forecast SOLIDO")
    app.layout = html.Div(
        [
            html.Div(
                [
                    html.Div(
                        [
                            html.Div("La Gaitana Farms", className="kicker"),
                            html.H1("Forecast SOLIDO"),
                            html.P("Versionamiento MLflow, backtesting y lectura ejecutiva de demanda semanal."),
                            html.Div(
                                [
                                    html.A("Ventas generales", href="http://127.0.0.1:8052", className="nav-link"),
                                    html.A("Forecast SOLIDO", href="http://127.0.0.1:8053", className="nav-link active"),
                                ],
                                className="nav-links",
                            ),
                        ],
                        className="hero-title",
                    ),
                    html.Div([html.Div("Fuente", className="source-label"), html.Div(source_path or source_dir, className="source-path")], className="source-card"),
                ],
                className="hero",
            ),
            html.Div(
                [
                    html.Div([html.Label("Modelo en backtest"), dcc.Dropdown(id="model", options=[{"label": m, "value": m} for m in models], value=models[0] if models else None, clearable=True)], className="control"),
                    html.Div([html.Label("Salida forecast"), html.Div(str(Path(forecast_output_dir) / "forecast"), className="source-path dark")], className="control control-wide"),
                ],
                className="filters",
            ),
            html.Div(id="metrics", className="metrics-grid"),
            html.Div(
                [
                    html.Div([html.Div("Demanda observada", className="panel-title"), dcc.Graph(id="fig-weekly")], className="panel"),
                    html.Div([html.Div("Comparacion MLflow", className="panel-title"), dcc.Graph(id="fig-evaluation")], className="panel"),
                    html.Div([html.Div("Backtesting", className="panel-title"), dcc.Graph(id="fig-backtest")], className="panel"),
                    html.Div([html.Div("Forecast futuro", className="panel-title"), dcc.Graph(id="fig-future")], className="panel"),
                ],
                className="grid-2",
            ),
            html.Div([html.Div("Metricas y seleccion", className="panel-title"), html.Div(id="evaluation-table")], className="table-panel section-gap"),
            html.Div([html.Div("Predicciones futuras exportables", className="panel-title"), html.Div(id="future-table")], className="table-panel section-gap"),
        ],
        className="page",
    )

    app.index_string = """
    <!DOCTYPE html><html><head>{%metas%}<title>{%title%}</title>{%favicon%}{%css%}
    <style>
    body{margin:0;background:#f4f6f8;color:#17202a;font-family:Inter,Arial,sans-serif}.page{max-width:1560px;margin:0 auto;padding:22px}
    .hero{display:grid;grid-template-columns:minmax(0,1fr) 430px;gap:18px;align-items:end;background:linear-gradient(135deg,#800020 0%,#9b1b3f 45%,#4e79a7 100%);color:#fff;border:1px solid #74122b;border-radius:8px;padding:26px 28px;margin-bottom:14px;box-shadow:0 14px 30px rgba(23,32,42,.12)}
    .kicker{color:#f8d7df;text-transform:uppercase;font-size:12px;font-weight:800;letter-spacing:.08em}h1{margin:5px 0 8px;font-size:42px;line-height:1.05;letter-spacing:0}.hero p{margin:0;color:#f6e7ec;font-size:16px;max-width:760px}
    .nav-links{display:flex;flex-wrap:wrap;gap:8px;margin-top:14px}.nav-link{display:inline-flex;align-items:center;min-height:34px;padding:7px 11px;border-radius:8px;border:1px solid rgba(255,255,255,.35);color:#fff;text-decoration:none;font-size:13px;font-weight:800;background:rgba(255,255,255,.10)}.nav-link.active{background:#fff;color:#800020}
    .source-card{background:rgba(255,255,255,.12);border:1px solid rgba(255,255,255,.28);border-radius:8px;padding:13px}.source-label{font-size:11px;font-weight:800;color:#f8d7df;text-transform:uppercase}.source-path{font-size:13px;word-break:break-all;color:#fff}.dark{color:#374151}
    .filters{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:10px;background:#fff;border:1px solid #d9dee7;border-left:5px solid #800020;border-radius:8px;padding:14px;margin-bottom:14px}.control-wide{grid-column:span 2}label{display:block;font-size:11px;font-weight:800;color:#374151;text-transform:uppercase;margin-bottom:4px}
    .metrics-grid{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:12px;margin-bottom:14px}.metric-card{background:#fff;border:1px solid #d9dee7;border-top:4px solid #800020;border-radius:8px;padding:13px;min-height:96px}.metric-head{display:flex;justify-content:space-between;gap:8px}.metric-title{font-size:11px;font-weight:800;color:#667085;text-transform:uppercase}.metric-value{font-size:24px;font-weight:800;margin-top:10px;color:#17202a}.metric-detail{font-size:12px;color:#667085;margin-top:5px}.delta{font-size:12px;font-weight:800;border-radius:999px;padding:3px 7px;background:#eef2f7}
    .grid-2{display:grid;grid-template-columns:1fr 1fr;gap:14px}.panel,.table-panel{background:#fff;border:1px solid #d9dee7;border-radius:8px;padding:13px;min-width:0;box-shadow:0 8px 20px rgba(23,32,42,.04)}.panel-title{font-size:16px;font-weight:800;margin:2px 0 10px;color:#17202a}.section-gap{margin-top:14px}
    .dash-table-container .dash-spreadsheet-container .dash-spreadsheet-inner th{background:#800020!important;color:#fff!important;font-weight:800!important}.dash-table-container .dash-spreadsheet-container .dash-spreadsheet-inner td{font-size:12px}
    @media(max-width:1150px){.hero,.filters,.grid-2{grid-template-columns:1fr}.control-wide{grid-column:auto}.metrics-grid{grid-template-columns:1fr 1fr}}@media(max-width:650px){.metrics-grid{grid-template-columns:1fr}.page{padding:12px}h1{font-size:32px}}
    </style></head><body>{%app_entry%}<footer>{%config%}{%scripts%}{%renderer%}</footer></body></html>
    """

    @app.callback(
        Output("metrics", "children"),
        Output("fig-weekly", "figure"),
        Output("fig-evaluation", "figure"),
        Output("fig-backtest", "figure"),
        Output("fig-future", "figure"),
        Output("evaluation-table", "children"),
        Output("future-table", "children"),
        Input("model", "value"),
    )
    def update(selected_model):
        view_data = {key: value.copy() for key, value in data.items()}
        if selected_model and not view_data["backtest"].empty:
            view_data["backtest"] = view_data["backtest"][view_data["backtest"]["modelo"].eq(selected_model)]
        figs = build_figures(view_data)
        future = view_data["future"].copy()
        if not future.empty:
            future["prediccion"] = future["prediccion"].map(lambda value: money(value, 0))
            future["week_start"] = pd.to_datetime(future["week_start"]).dt.strftime("%Y-%m-%d")
        return (
            build_metric_cards(data),
            figs["weekly"],
            figs["evaluation"],
            figs["backtest"],
            figs["future"],
            evaluation_table(data["evaluation"]),
            table(future, page_size=12),
        )

    return app


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Dashboard de forecast SOLIDO LGF.")
    parser.add_argument("--data-path", default=os.getenv("LGF_DATA_PATH"), help="Ruta al historic_sales_acum.csv")
    parser.add_argument("--data-dir", default=os.getenv("LGF_DATA_DIR"), help="Carpeta de respaldo con CSV por anio.")
    parser.add_argument("--output-dir", default=os.getenv("LGF_OUTPUT_DIR", "outputs"), help="Carpeta con outputs/forecast.")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", default=8053, type=int)
    parser.add_argument("--debug", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    app = make_app(data_path=args.data_path, data_dir=args.data_dir, output_dir=args.output_dir)
    app.run(host=args.host, port=args.port, debug=args.debug)


if __name__ == "__main__":
    main()
