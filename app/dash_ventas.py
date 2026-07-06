from __future__ import annotations

import argparse
import os
from functools import lru_cache
from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from dash import Dash, Input, Output, dash_table, dcc, html

from lgf_despliegue.config import load_config
from lgf_despliegue.data import load_sales_source


PLOT_TEMPLATE = "plotly_white"
FLOWER_COLORS = {
    "green": "#2f6f5e",
    "leaf": "#8fb339",
    "pink": "#c4417b",
    "red": "#b8323a",
    "yellow": "#d6a629",
    "blue": "#3867a6",
    "ink": "#1f2933",
    "muted": "#667085",
    "line": "#d9dee7",
    "panel": "#ffffff",
    "background": "#f5f7f3",
}


def _fmt_int(value: float | int) -> str:
    return f"{float(value):,.0f}".replace(",", ".")


def _fmt_usd(value: float | int) -> str:
    return "US$ " + f"{float(value):,.0f}".replace(",", ".")


def _fmt_pct(value: float | int) -> str:
    return f"{float(value) * 100:,.1f}%".replace(",", "X").replace(".", ",").replace("X", ".")


@lru_cache(maxsize=2)
def load_dashboard_data(data_path: str | None, data_dir: str) -> pd.DataFrame:
    sales = load_sales_source(data_path=data_path or None, data_dir=data_dir)
    confirmed = sales[sales["es_confirmado"]].copy()
    if confirmed.empty:
        confirmed = sales.copy()
    confirmed["tipo_pedido"] = confirmed["es_solido"].map({True: "SOLIDO", False: "NO_SOLIDO"})
    confirmed["periodo"] = confirmed["anio"].astype(str) + "-" + confirmed["mes"].astype(str).str.zfill(2)
    confirmed["precio_usd_tallo"] = confirmed["ventas_usd"] / confirmed["tallos_demanda"].replace(0, pd.NA)
    return confirmed


def _source_from_env() -> tuple[str | None, str]:
    config = load_config()
    return (str(config.data_path) if config.data_path else None, str(config.data_dir))


def _filter_frame(frame: pd.DataFrame, years: list[int] | None, order_types: list[str] | None) -> pd.DataFrame:
    out = frame.copy()
    if years:
        out = out[out["anio"].isin([int(year) for year in years])]
    if order_types:
        out = out[out["tipo_pedido"].isin(order_types)]
    return out


def _kpi(label: str, value: str, detail: str) -> html.Div:
    return html.Div(
        [
            html.Div(label, className="kpi-label"),
            html.Div(value, className="kpi-value"),
            html.Div(detail, className="kpi-detail"),
        ],
        className="kpi",
    )


def _empty_figure(title: str) -> go.Figure:
    fig = go.Figure()
    fig.update_layout(
        template=PLOT_TEMPLATE,
        title=title,
        xaxis={"visible": False},
        yaxis={"visible": False},
        annotations=[{"text": "Sin datos para los filtros seleccionados", "xref": "paper", "yref": "paper", "showarrow": False}],
        height=360,
    )
    return fig


def _build_figures(filtered: pd.DataFrame) -> tuple[go.Figure, go.Figure, go.Figure, go.Figure]:
    if filtered.empty:
        return (
            _empty_figure("Tallos y ventas por mes"),
            _empty_figure("Top clientes por tallos"),
            _empty_figure("Producto-color por tallos"),
            _empty_figure("Mezcla SOLIDO / NO_SOLIDO"),
        )

    monthly = filtered.groupby(["periodo", "tipo_pedido"], as_index=False).agg(
        tallos=("tallos_demanda", "sum"),
        ventas_usd=("ventas_usd", "sum"),
    )
    fig_monthly = px.bar(
        monthly,
        x="periodo",
        y="tallos",
        color="tipo_pedido",
        color_discrete_map={"SOLIDO": FLOWER_COLORS["pink"], "NO_SOLIDO": FLOWER_COLORS["green"]},
        template=PLOT_TEMPLATE,
        title="Tallos confirmados por mes",
        labels={"periodo": "Mes", "tallos": "Tallos", "tipo_pedido": "Tipo"},
    )
    fig_monthly.update_layout(height=390, legend_orientation="h", legend_y=1.1, margin=dict(l=40, r=20, t=60, b=80))

    clients = (
        filtered.groupby("cliente_analisis", as_index=False)
        .agg(tallos=("tallos_demanda", "sum"), ventas_usd=("ventas_usd", "sum"))
        .sort_values("tallos", ascending=False)
        .head(12)
        .sort_values("tallos")
    )
    fig_clients = px.bar(
        clients,
        x="tallos",
        y="cliente_analisis",
        orientation="h",
        template=PLOT_TEMPLATE,
        title="Clientes que explican mayor volumen",
        labels={"cliente_analisis": "Cliente", "tallos": "Tallos"},
        color_discrete_sequence=[FLOWER_COLORS["blue"]],
    )
    fig_clients.update_layout(height=430, margin=dict(l=20, r=20, t=60, b=40), yaxis={"automargin": True})

    product_color = (
        filtered.groupby(["producto_color", "producto", "color"], as_index=False)
        .agg(tallos=("tallos_demanda", "sum"), ventas_usd=("ventas_usd", "sum"))
        .sort_values("tallos", ascending=False)
        .head(15)
        .sort_values("tallos")
    )
    fig_product = px.bar(
        product_color,
        x="tallos",
        y="producto_color",
        orientation="h",
        template=PLOT_TEMPLATE,
        title="Producto-color con mayor demanda",
        labels={"producto_color": "Producto-color", "tallos": "Tallos"},
        color="producto",
        color_discrete_sequence=[FLOWER_COLORS["pink"], FLOWER_COLORS["green"], FLOWER_COLORS["yellow"], FLOWER_COLORS["red"], FLOWER_COLORS["blue"]],
    )
    fig_product.update_layout(height=430, margin=dict(l=20, r=20, t=60, b=40), yaxis={"automargin": True}, legend_title_text="Producto")

    mix = filtered.groupby("tipo_pedido", as_index=False).agg(tallos=("tallos_demanda", "sum"))
    fig_mix = px.pie(
        mix,
        values="tallos",
        names="tipo_pedido",
        hole=0.55,
        template=PLOT_TEMPLATE,
        title="Participacion por tipo de pedido",
        color="tipo_pedido",
        color_discrete_map={"SOLIDO": FLOWER_COLORS["pink"], "NO_SOLIDO": FLOWER_COLORS["green"]},
    )
    fig_mix.update_layout(height=360, margin=dict(l=20, r=20, t=60, b=30), legend_orientation="h", legend_y=-0.05)
    return fig_monthly, fig_clients, fig_product, fig_mix


def _build_tables(filtered: pd.DataFrame) -> tuple[list[dict], list[dict], list[dict]]:
    if filtered.empty:
        return [], [], []
    by_year = filtered.groupby("anio", as_index=False).agg(
        tallos=("tallos_demanda", "sum"),
        ventas_usd=("ventas_usd", "sum"),
        clientes=("cliente_analisis", "nunique"),
        producto_colores=("producto_color", "nunique"),
    )
    by_year["usd_tallo"] = by_year["ventas_usd"] / by_year["tallos"].replace(0, pd.NA)

    client = (
        filtered.groupby("cliente_analisis", as_index=False)
        .agg(tallos=("tallos_demanda", "sum"), ventas_usd=("ventas_usd", "sum"), producto_colores=("producto_color", "nunique"))
        .sort_values("tallos", ascending=False)
        .head(10)
    )
    product = (
        filtered.groupby("producto_color", as_index=False)
        .agg(tallos=("tallos_demanda", "sum"), ventas_usd=("ventas_usd", "sum"), clientes=("cliente_analisis", "nunique"))
        .sort_values("tallos", ascending=False)
        .head(10)
    )
    for table in [by_year, client, product]:
        if "tallos" in table:
            table["tallos"] = table["tallos"].map(_fmt_int)
        if "ventas_usd" in table:
            table["ventas_usd"] = table["ventas_usd"].map(_fmt_usd)
        if "usd_tallo" in table:
            table["usd_tallo"] = table["usd_tallo"].map(lambda value: f"US$ {float(value):.3f}" if pd.notna(value) else "NA")
    return by_year.to_dict("records"), client.to_dict("records"), product.to_dict("records")


def _insights(filtered: pd.DataFrame) -> list[html.Li]:
    if filtered.empty:
        return [html.Li("No hay datos para los filtros seleccionados.")]
    total_tallos = filtered["tallos_demanda"].sum()
    total_ventas = filtered["ventas_usd"].sum()
    solid_tallos = filtered.loc[filtered["tipo_pedido"].eq("SOLIDO"), "tallos_demanda"].sum()
    top_client = (
        filtered.groupby("cliente_analisis")["tallos_demanda"].sum().sort_values(ascending=False).head(1)
    )
    top_product = (
        filtered.groupby("producto_color")["tallos_demanda"].sum().sort_values(ascending=False).head(1)
    )
    monthly = filtered.groupby("periodo")["tallos_demanda"].sum().sort_values(ascending=False).head(1)
    return [
        html.Li(f"SOLIDO representa {_fmt_pct(solid_tallos / total_tallos if total_tallos else 0)} del volumen confirmado filtrado."),
        html.Li(f"El cliente con mayor peso es {top_client.index[0]} con {_fmt_int(top_client.iloc[0])} tallos."),
        html.Li(f"La combinacion producto-color lider es {top_product.index[0]} con {_fmt_int(top_product.iloc[0])} tallos."),
        html.Li(f"El mes de mayor demanda filtrada es {monthly.index[0]} con {_fmt_int(monthly.iloc[0])} tallos."),
        html.Li(f"El precio promedio ponderado es US$ {total_ventas / total_tallos:.3f} por tallo." if total_tallos else "No se puede calcular precio por tallo."),
    ]


def build_app(data_path: str | None = None, data_dir: str | None = None) -> Dash:
    env_data_path, env_data_dir = _source_from_env()
    source_path = data_path or env_data_path
    source_dir = data_dir or env_data_dir
    frame = load_dashboard_data(source_path, source_dir)
    years = sorted(frame["anio"].dropna().astype(int).unique().tolist())
    app = Dash(__name__, title="LGF Ventas Generales")

    app.layout = html.Div(
        [
            html.Div(
                [
                    html.Div(
                        [
                            html.Div("La Gaitana Farms", className="brand"),
                            html.H1("Ventas generales"),
                            html.P("Lectura comercial de tallos, ventas, clientes y producto-color para enfocar decisiones de demanda."),
                        ],
                        className="title-block",
                    ),
                    html.Div(
                        [
                            html.Label("Anios"),
                            dcc.Dropdown(
                                id="year-filter",
                                options=[{"label": str(year), "value": year} for year in years],
                                value=years,
                                multi=True,
                                clearable=False,
                            ),
                            html.Label("Tipo de pedido"),
                            dcc.Checklist(
                                id="type-filter",
                                options=[
                                    {"label": "SOLIDO", "value": "SOLIDO"},
                                    {"label": "NO_SOLIDO", "value": "NO_SOLIDO"},
                                ],
                                value=["SOLIDO", "NO_SOLIDO"],
                                inline=True,
                            ),
                        ],
                        className="controls",
                    ),
                ],
                className="hero",
            ),
            html.Div(id="kpi-strip", className="kpi-strip"),
            html.Div(
                [
                    html.Div(dcc.Graph(id="monthly-chart", config={"displayModeBar": False}), className="panel wide"),
                    html.Div(dcc.Graph(id="mix-chart", config={"displayModeBar": False}), className="panel"),
                    html.Div(dcc.Graph(id="clients-chart", config={"displayModeBar": False}), className="panel"),
                    html.Div(dcc.Graph(id="product-chart", config={"displayModeBar": False}), className="panel"),
                ],
                className="grid",
            ),
            html.Div(
                [
                    html.Div(
                        [
                            html.H2("Lecturas de negocio"),
                            html.Ul(id="insight-list"),
                        ],
                        className="insights",
                    ),
                    html.Div(
                        [
                            html.H2("Resumen anual"),
                            dash_table.DataTable(
                                id="annual-table",
                                columns=[
                                    {"name": "Anio", "id": "anio"},
                                    {"name": "Tallos", "id": "tallos"},
                                    {"name": "Ventas USD", "id": "ventas_usd"},
                                    {"name": "Clientes", "id": "clientes"},
                                    {"name": "Producto-color", "id": "producto_colores"},
                                    {"name": "USD/tallo", "id": "usd_tallo"},
                                ],
                                page_size=8,
                                style_as_list_view=True,
                                style_cell={"fontFamily": "Segoe UI, Arial, sans-serif", "fontSize": 13, "padding": "8px", "textAlign": "left"},
                                style_header={"fontWeight": "700", "backgroundColor": "#eef2ea"},
                            ),
                        ],
                        className="table-panel",
                    ),
                ],
                className="lower-grid",
            ),
            html.Div(
                [
                    html.Div(
                        [
                            html.H2("Top clientes"),
                            dash_table.DataTable(
                                id="client-table",
                                columns=[
                                    {"name": "Cliente", "id": "cliente_analisis"},
                                    {"name": "Tallos", "id": "tallos"},
                                    {"name": "Ventas USD", "id": "ventas_usd"},
                                    {"name": "Producto-color", "id": "producto_colores"},
                                ],
                                page_size=10,
                                style_as_list_view=True,
                                style_cell={"fontFamily": "Segoe UI, Arial, sans-serif", "fontSize": 13, "padding": "8px", "textAlign": "left"},
                                style_header={"fontWeight": "700", "backgroundColor": "#eef2ea"},
                            ),
                        ],
                        className="table-panel",
                    ),
                    html.Div(
                        [
                            html.H2("Top producto-color"),
                            dash_table.DataTable(
                                id="product-table",
                                columns=[
                                    {"name": "Producto-color", "id": "producto_color"},
                                    {"name": "Tallos", "id": "tallos"},
                                    {"name": "Ventas USD", "id": "ventas_usd"},
                                    {"name": "Clientes", "id": "clientes"},
                                ],
                                page_size=10,
                                style_as_list_view=True,
                                style_cell={"fontFamily": "Segoe UI, Arial, sans-serif", "fontSize": 13, "padding": "8px", "textAlign": "left"},
                                style_header={"fontWeight": "700", "backgroundColor": "#eef2ea"},
                            ),
                        ],
                        className="table-panel",
                    ),
                ],
                className="table-grid",
            ),
        ],
        className="page",
    )

    app.index_string = """
    <!DOCTYPE html>
    <html>
        <head>
            {%metas%}
            <title>{%title%}</title>
            {%favicon%}
            {%css%}
            <style>
                body { margin: 0; background: #f5f7f3; color: #1f2933; font-family: Segoe UI, Arial, sans-serif; }
                .page { max-width: 1500px; margin: 0 auto; padding: 24px; }
                .hero { display: grid; grid-template-columns: minmax(0, 1fr) 420px; gap: 24px; align-items: end; padding: 28px 0 18px; border-bottom: 1px solid #d9dee7; }
                .brand { color: #2f6f5e; font-weight: 700; font-size: 14px; text-transform: uppercase; }
                h1 { margin: 6px 0 8px; font-size: 42px; line-height: 1.05; font-weight: 760; }
                h2 { margin: 0 0 12px; font-size: 18px; }
                p { margin: 0; color: #667085; max-width: 760px; font-size: 16px; }
                .controls { display: grid; gap: 8px; background: #ffffff; border: 1px solid #d9dee7; border-radius: 8px; padding: 16px; }
                label { font-weight: 700; font-size: 13px; }
                .kpi-strip { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 14px; margin: 18px 0; }
                .kpi { background: #ffffff; border: 1px solid #d9dee7; border-radius: 8px; padding: 16px; min-height: 92px; }
                .kpi-label { color: #667085; font-size: 13px; font-weight: 700; text-transform: uppercase; }
                .kpi-value { font-size: 28px; font-weight: 760; margin-top: 8px; }
                .kpi-detail { color: #667085; font-size: 13px; margin-top: 4px; }
                .grid { display: grid; grid-template-columns: 1.35fr 0.75fr; gap: 16px; }
                .panel, .table-panel, .insights { background: #ffffff; border: 1px solid #d9dee7; border-radius: 8px; padding: 12px; min-width: 0; }
                .wide { grid-column: span 1; }
                .lower-grid { display: grid; grid-template-columns: 0.8fr 1.2fr; gap: 16px; margin-top: 16px; align-items: start; }
                .table-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; margin-top: 16px; }
                .insights ul { margin: 0; padding-left: 20px; color: #344054; line-height: 1.55; }
                @media (max-width: 980px) {
                    .hero, .grid, .lower-grid, .table-grid { grid-template-columns: 1fr; }
                    .kpi-strip { grid-template-columns: repeat(2, minmax(0, 1fr)); }
                    h1 { font-size: 34px; }
                }
                @media (max-width: 620px) {
                    .page { padding: 14px; }
                    .kpi-strip { grid-template-columns: 1fr; }
                    h1 { font-size: 30px; }
                }
            </style>
        </head>
        <body>
            {%app_entry%}
            <footer>
                {%config%}
                {%scripts%}
                {%renderer%}
            </footer>
        </body>
    </html>
    """

    @app.callback(
        Output("kpi-strip", "children"),
        Output("monthly-chart", "figure"),
        Output("clients-chart", "figure"),
        Output("product-chart", "figure"),
        Output("mix-chart", "figure"),
        Output("insight-list", "children"),
        Output("annual-table", "data"),
        Output("client-table", "data"),
        Output("product-table", "data"),
        Input("year-filter", "value"),
        Input("type-filter", "value"),
    )
    def update_dashboard(selected_years, selected_types):
        filtered = _filter_frame(frame, selected_years, selected_types)
        total_tallos = filtered["tallos_demanda"].sum() if not filtered.empty else 0
        total_ventas = filtered["ventas_usd"].sum() if not filtered.empty else 0
        clientes = filtered["cliente_analisis"].nunique() if not filtered.empty else 0
        product_colors = filtered["producto_color"].nunique() if not filtered.empty else 0
        usd_tallo = total_ventas / total_tallos if total_tallos else 0
        kpis = [
            _kpi("Tallos confirmados", _fmt_int(total_tallos), "Volumen despachado filtrado"),
            _kpi("Ventas", _fmt_usd(total_ventas), f"US$ {usd_tallo:.3f} por tallo"),
            _kpi("Clientes", _fmt_int(clientes), "Clientes con venta confirmada"),
            _kpi("Producto-color", _fmt_int(product_colors), "Combinaciones comerciales activas"),
        ]
        fig_monthly, fig_clients, fig_product, fig_mix = _build_figures(filtered)
        annual, client, product = _build_tables(filtered)
        return kpis, fig_monthly, fig_clients, fig_product, fig_mix, _insights(filtered), annual, client, product

    return app


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Dashboard descriptivo de ventas generales LGF.")
    parser.add_argument("--data-path", default=os.getenv("LGF_DATA_PATH"), help="Ruta al historic_sales_acum.csv")
    parser.add_argument("--data-dir", default=os.getenv("LGF_DATA_DIR"), help="Carpeta de respaldo con CSV por anio.")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", default=8051, type=int)
    parser.add_argument("--debug", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.data_path:
        os.environ["LGF_DATA_PATH"] = str(Path(args.data_path))
    if args.data_dir:
        os.environ["LGF_DATA_DIR"] = str(Path(args.data_dir))
    app = build_app(data_path=args.data_path, data_dir=args.data_dir)
    app.run(host=args.host, port=args.port, debug=args.debug)


if __name__ == "__main__":
    main()
