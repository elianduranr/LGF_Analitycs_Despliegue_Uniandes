from __future__ import annotations

import argparse

from dash import Dash, dcc, html


def make_app(ventas_url: str, forecast_url: str) -> Dash:
    app = Dash(__name__, title="LGF Tablero Integrado")
    app.layout = html.Div(
        [
            html.Div(
                [
                    html.Div("La Gaitana Farms", className="kicker"),
                    html.H1("Tablero integrado"),
                    html.P("Ventas generales y forecast SOLIDO en un solo punto de entrada para la Entrega 2."),
                ],
                className="hero",
            ),
            dcc.Tabs(
                [
                    dcc.Tab(
                        label="Ventas generales",
                        value="ventas",
                        children=[html.Iframe(src=ventas_url, className="dashboard-frame")],
                    ),
                    dcc.Tab(
                        label="Forecast SOLIDO",
                        value="forecast",
                        children=[html.Iframe(src=forecast_url, className="dashboard-frame")],
                    ),
                ],
                value="ventas",
                className="tabs",
            ),
        ],
        className="page",
    )

    app.index_string = """
    <!DOCTYPE html><html><head>{%metas%}<title>{%title%}</title>{%favicon%}{%css%}
    <style>
    body{margin:0;background:#f4f6f8;color:#17202a;font-family:Inter,Arial,sans-serif}
    .page{min-height:100vh}.hero{background:linear-gradient(135deg,#800020 0%,#9b1b3f 45%,#4e79a7 100%);color:#fff;padding:22px 28px;border-bottom:1px solid #74122b}
    .kicker{color:#f8d7df;text-transform:uppercase;font-size:12px;font-weight:800;letter-spacing:.08em}
    h1{margin:5px 0 6px;font-size:34px;line-height:1.05;letter-spacing:0}.hero p{margin:0;color:#f6e7ec;font-size:15px}
    .tabs{background:#fff;border-bottom:1px solid #d9dee7}.dashboard-frame{width:100%;height:calc(100vh - 150px);border:0;display:block;background:#f4f6f8}
    .tab{font-weight:800!important;padding:12px 18px!important}.tab--selected{color:#800020!important;border-top:3px solid #800020!important}
    @media(max-width:650px){h1{font-size:28px}.hero{padding:18px}.dashboard-frame{height:calc(100vh - 155px)}}
    </style></head><body>{%app_entry%}<footer>{%config%}{%scripts%}{%renderer%}</footer></body></html>
    """
    return app


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Dashboard integrado LGF: ventas generales y forecast SOLIDO.")
    parser.add_argument("--ventas-url", default="http://127.0.0.1:8052")
    parser.add_argument("--forecast-url", default="http://127.0.0.1:8053")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", default=8050, type=int)
    parser.add_argument("--debug", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    app = make_app(ventas_url=args.ventas_url, forecast_url=args.forecast_url)
    app.run(host=args.host, port=args.port, debug=args.debug)


if __name__ == "__main__":
    main()
