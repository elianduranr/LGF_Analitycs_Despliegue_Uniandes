from __future__ import annotations

import argparse
import json
import os
from functools import lru_cache
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from dash import Dash, Input, Output, dash_table, dcc, html

from lgf_despliegue.config import load_config
from lgf_despliegue.data import clean_sales_frame, load_sales_source


CORPORATE_BURGUNDY = "#800020"
GRAPH_TEXT = "#374151"
GRAPH_BG = "#FAFAFA"
CORPORATE_SEQUENCE = [CORPORATE_BURGUNDY, "#4E79A7", "#59A14F", "#F28E2B", "#B07AA1", "#9CA3AF", "#E15759", "#76B7B2"]
LOW_USD_BASE_THRESHOLD = 1_000.0
LOW_STEMS_BASE_THRESHOLD = 1_000.0
MONTHS = ["Ene", "Feb", "Mar", "Abr", "May", "Jun", "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"]
FLOWER_COLOR_MAP = {
    "white": "#E5E7EB",
    "red": "#C1121F",
    "hot pink": "#EC4899",
    "light pink": "#F9A8D4",
    "pink": "#F472B6",
    "green": "#59A14F",
    "orange": "#F28E2B",
    "peach": "#FDBA74",
    "lavender": "#A78BFA",
    "purple": "#7C3AED",
    "yellow": "#F2C94C",
    "cream": "#F7E7CE",
    "burgundy": CORPORATE_BURGUNDY,
    "bicolor burgundy": CORPORATE_BURGUNDY,
}


def money(value: float, decimals: int = 0) -> str:
    if pd.isna(value):
        return "NA"
    return f"{float(value):,.{decimals}f}".replace(",", "X").replace(".", ",").replace("X", ".")


def percent(value: float | None) -> str:
    if value is None or pd.isna(value):
        return "NA"
    return f"{float(value):+.1%}".replace(".", ",")


def pct_change(base: float, comp: float, low_threshold: float = 0.0) -> float | None:
    base = float(base or 0)
    comp = float(comp or 0)
    if base == 0:
        return np.nan
    if abs(base) < low_threshold:
        return np.nan
    return (comp - base) / base


def variation_label(base: float, comp: float, low_threshold: float = 0.0) -> str:
    base = float(base or 0)
    comp = float(comp or 0)
    if base == 0 and comp > 0:
        return "Nuevo"
    if base > 0 and comp == 0:
        return "Perdido"
    if abs(base) < low_threshold and comp != base:
        return "Base baja"
    change = pct_change(base, comp)
    if pd.isna(change):
        return "Sin base"
    return percent(change)


def apply_layout(fig: go.Figure, height: int = 360) -> go.Figure:
    fig.update_layout(
        template="plotly_white",
        height=height,
        margin=dict(l=24, r=24, t=56, b=42),
        font=dict(family="Arial, sans-serif", size=12, color=GRAPH_TEXT),
        paper_bgcolor=GRAPH_BG,
        plot_bgcolor=GRAPH_BG,
        colorway=CORPORATE_SEQUENCE,
        legend_title_text="",
    )
    fig.update_xaxes(gridcolor="#E5E7EB", zerolinecolor="#D1D5DB")
    fig.update_yaxes(gridcolor="#E5E7EB", zerolinecolor="#D1D5DB")
    return fig


def flower_color(value: object, index: int = 0) -> str:
    text = str(value or "").strip().lower()
    for key, color in FLOWER_COLOR_MAP.items():
        if key in text:
            return color
    return CORPORATE_SEQUENCE[index % len(CORPORATE_SEQUENCE)]


def empty_figure(title: str) -> go.Figure:
    fig = go.Figure()
    fig.add_annotation(text="Sin datos para los filtros seleccionados", x=0.5, y=0.5, showarrow=False)
    fig.update_layout(title=title)
    return apply_layout(fig, 340)


def selected_values(value) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(item) for item in value if str(item).strip()]
    text = str(value).strip()
    return [text] if text else []


def table(df: pd.DataFrame, page_size: int = 10, sort_by: list[dict] | None = None) -> dash_table.DataTable:
    if df.empty:
        df = pd.DataFrame({"mensaje": ["Sin datos para mostrar"]})
    numeric_cols = {col for col in df.columns if pd.api.types.is_numeric_dtype(df[col])}
    return dash_table.DataTable(
        data=df.to_dict("records"),
        columns=[{"name": col, "id": col, "type": "numeric"} if col in numeric_cols else {"name": col, "id": col} for col in df.columns],
        page_size=page_size,
        sort_action="native",
        filter_action="native",
        sort_by=sort_by or [],
        export_format="xlsx",
        style_table={"overflowX": "auto", "maxHeight": "430px", "overflowY": "auto"},
        style_cell={
            "fontFamily": "Arial, sans-serif",
            "fontSize": 12,
            "padding": "7px",
            "minWidth": "90px",
            "maxWidth": "280px",
            "whiteSpace": "normal",
            "height": "auto",
        },
        style_header={"backgroundColor": CORPORATE_BURGUNDY, "color": "white", "fontWeight": "600"},
        style_data_conditional=[{"if": {"row_index": "odd"}, "backgroundColor": "#f7f9fb"}],
    )


def metric_card(title: str, value: str, detail: str = "", delta: str | None = None) -> html.Div:
    delta_class = "delta neutral"
    if delta and delta.startswith("+"):
        delta_class = "delta positive"
    elif delta and delta.startswith("-"):
        delta_class = "delta negative"
    return html.Div(
        [
            html.Div([html.Div(title, className="metric-title"), html.Span(delta or "", className=delta_class)], className="metric-head"),
            html.Div(value, className="metric-value"),
            html.Div(detail, className="metric-detail"),
        ],
        className="metric-card",
    )


def scope_card(label: str, value: str, detail: str = "") -> html.Div:
    return html.Div(
        [html.Div(label, className="scope-label"), html.Div(value, className="scope-value"), html.Div(detail, className="scope-detail")],
        className="scope-card",
    )


def flower_chip(label: str, value: str, color: str, detail: str = "") -> html.Div:
    return html.Div(
        [
            html.Div(style={"backgroundColor": color}, className="flower-swatch"),
            html.Div(
                [
                    html.Div(label, className="flower-chip-label"),
                    html.Div(value, className="flower-chip-value"),
                    html.Div(detail, className="flower-chip-detail"),
                ],
                className="flower-chip-copy",
            ),
        ],
        className="flower-chip",
    )


@lru_cache(maxsize=2)
def load_dashboard_data(data_path: str | None, data_dir: str) -> pd.DataFrame:
    cache_dir = Path(os.getenv("LGF_OUTPUT_DIR", "outputs")) / "cache"
    cache_path = cache_dir / "ventas_dashboard.parquet"
    metadata_path = cache_dir / "ventas_dashboard.json"
    source = Path(data_path) if data_path else None

    if source and source.exists() and cache_path.exists() and metadata_path.exists():
        try:
            metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
            signature = {"path": str(source.resolve()), "size": source.stat().st_size, "mtime_ns": source.stat().st_mtime_ns}
            if metadata.get("source") == signature:
                return pd.read_parquet(cache_path)
        except (OSError, ValueError, KeyError):
            pass

    if source and source.suffix.lower() == ".csv":
        dashboard_source_columns = {
            "NomCompania", "fecha", "cod_cliente", "cliente", "cliente_consolidado",
            "producto", "color", "pais", "pedido", "tipo_orden_empaque", "tipo_empaque",
            "empaque", "tallos_total", "tallos_confirmados", "estado", "VALORTOTAL",
            "ventas_usd",
        }
        available = set(pd.read_csv(source, nrows=0).columns)
        usecols = sorted(dashboard_source_columns & available)
        confirmed_chunks = []
        for chunk in pd.read_csv(source, usecols=usecols, chunksize=100_000, low_memory=False):
            cleaned = clean_sales_frame(chunk)
            confirmed = cleaned[cleaned["es_confirmado"]].copy()
            if not confirmed.empty:
                confirmed_chunks.append(confirmed)
        raw = pd.concat(confirmed_chunks, ignore_index=True) if confirmed_chunks else pd.DataFrame()
    else:
        raw = load_sales_source(data_path=data_path or None, data_dir=data_dir)
    df = raw[raw["es_confirmado"]].copy()
    if df.empty:
        df = raw.copy()
    df["tallos_confirmados"] = pd.to_numeric(df["tallos_demanda"], errors="coerce").fillna(0)
    df["ventas_usd"] = pd.to_numeric(df["ventas_usd"], errors="coerce").fillna(0)
    df["valor_total_original"] = pd.to_numeric(df.get("valor_total_original", df.get("valor_total", 0)), errors="coerce").fillna(0)
    df["precio_usd_tallo"] = (df["ventas_usd"] / df["tallos_confirmados"].replace(0, np.nan)).fillna(0)
    df["tipo_pedido_operativo"] = df["tipo_pedido_operativo"].fillna("NO_SOLIDO").astype(str).str.upper()
    df["tipo_pedido_operativo"] = np.where(df["tipo_pedido_operativo"].isin(["", "SIN_INFO", "NAN", "NONE"]), df["es_solido"].map({True: "SOLIDO", False: "NO_SOLIDO"}), df["tipo_pedido_operativo"])
    df["NomCompania"] = df["NomCompania"].where(~df["NomCompania"].isin(["sin_info", "nan", "none", ""]), df["cliente_analisis"])
    df["cod_cliente"] = df["cod_cliente"].astype(str)
    df["cliente"] = df["cliente_analisis"].astype(str)
    df["pedidos"] = df["pedidos"].astype(str)
    df["anio_semana"] = df["anio"].astype(str) + "-S" + df["semana_iso"].astype(str).str.zfill(2)

    dashboard_columns = [
        "anio", "mes", "semana_iso", "NomCompania", "cod_cliente", "cliente", "pais",
        "producto", "color", "producto_color", "tipo_pedido_operativo", "es_solido",
        "tallos_confirmados", "ventas_usd", "valor_total_original", "precio_usd_tallo",
        "pedidos", "anio_semana",
    ]
    df = df[dashboard_columns].copy()
    for column in ["NomCompania", "pais", "producto", "color", "producto_color", "tipo_pedido_operativo", "anio_semana"]:
        df[column] = df[column].astype("category")

    if source and source.exists():
        cache_dir.mkdir(parents=True, exist_ok=True)
        df.to_parquet(cache_path, index=False, compression="snappy")
        signature = {"path": str(source.resolve()), "size": source.stat().st_size, "mtime_ns": source.stat().st_mtime_ns}
        metadata_path.write_text(json.dumps({"source": signature}, ensure_ascii=False, indent=2), encoding="utf-8")
    return df


def summarize(df: pd.DataFrame, group_cols: list[str]) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame()
    out = df.groupby(group_cols, dropna=False, as_index=False).agg(
        tallos_confirmados=("tallos_confirmados", "sum"),
        ventas_usd=("ventas_usd", "sum"),
        valor_total_original=("valor_total_original", "sum"),
        pedidos=("pedidos", "nunique"),
        clientes=("cod_cliente", "nunique"),
        productos=("producto", "nunique"),
        producto_colores=("producto_color", "nunique"),
    )
    out["precio_usd_tallo"] = (out["ventas_usd"] / out["tallos_confirmados"].replace(0, np.nan)).fillna(0)
    return out


def filter_frame(df: pd.DataFrame, years, weeks, companies, clients, countries, products, colors, order_types) -> pd.DataFrame:
    out = df.copy()
    vals = selected_values(years)
    if vals:
        out = out[out["anio"].isin([int(v) for v in vals])]
    if weeks and len(weeks) == 2:
        out = out[out["semana_iso"].between(int(weeks[0]), int(weeks[1]))]
    for col, value in [
        ("NomCompania", companies),
        ("cod_cliente", clients),
        ("pais", countries),
        ("producto", products),
        ("color", colors),
        ("tipo_pedido_operativo", order_types),
    ]:
        vals = selected_values(value)
        if vals:
            out = out[out[col].astype(str).isin(vals)]
    return out


def build_context(view: pd.DataFrame, base_year: int | None, compare_year: int | None) -> dict:
    years = sorted(pd.to_numeric(view["anio"], errors="coerce").dropna().astype(int).unique().tolist()) if not view.empty else []
    if not years:
        return {"ok": False, "years": []}
    comp = int(compare_year) if compare_year in years else years[-1]
    base = int(base_year) if base_year in years and int(base_year) != comp else None
    if base is None and len(years) > 1:
        base = [y for y in years if y != comp][-1]
    comparison = base is not None and base != comp
    comp_frame = view[view["anio"].eq(comp)].copy()
    base_frame = view[view["anio"].eq(base)].copy() if comparison else view.iloc[0:0].copy()

    def metrics(frame: pd.DataFrame) -> dict:
        tallos = float(frame["tallos_confirmados"].sum())
        ventas = float(frame["ventas_usd"].sum())
        pedidos = float(frame["pedidos"].nunique()) if "pedidos" in frame else float(len(frame))
        return {
            "ventas": ventas,
            "tallos": tallos,
            "precio": ventas / tallos if tallos else 0,
            "pedidos": pedidos,
            "clientes": float(frame["cod_cliente"].nunique()),
            "productos": float(frame["producto"].nunique()),
            "venta_pedido": ventas / pedidos if pedidos else 0,
            "tallos_pedido": tallos / pedidos if pedidos else 0,
        }

    base_m = metrics(base_frame)
    comp_m = metrics(comp_frame)
    return {"ok": True, "base": base, "compare": comp, "comparison": comparison, "base_frame": base_frame, "compare_frame": comp_frame, "base_m": base_m, "comp_m": comp_m}


def product_compare_table(ctx: dict, rows: int = 20) -> pd.DataFrame:
    comp = ctx["compare_frame"].groupby("producto", as_index=False).agg(tallos_compare=("tallos_confirmados", "sum"), usd_compare=("ventas_usd", "sum"))
    base = ctx["base_frame"].groupby("producto", as_index=False).agg(tallos_base=("tallos_confirmados", "sum"), usd_base=("ventas_usd", "sum")) if ctx["comparison"] else pd.DataFrame(columns=["producto", "tallos_base", "usd_base"])
    out = base.merge(comp, on="producto", how="outer").fillna(0)
    out["dif_usd"] = out["usd_compare"] - out["usd_base"]
    out["dif_tallos"] = out["tallos_compare"] - out["tallos_base"]
    out["var_usd"] = out.apply(lambda r: variation_label(r["usd_base"], r["usd_compare"], LOW_USD_BASE_THRESHOLD), axis=1)
    out["var_tallos"] = out.apply(lambda r: variation_label(r["tallos_base"], r["tallos_compare"], LOW_STEMS_BASE_THRESHOLD), axis=1)
    total_tallos = max(float(out["tallos_compare"].sum()), 1)
    out["share"] = out["tallos_compare"] / total_tallos
    out = out.sort_values(["usd_compare", "dif_usd"], ascending=False).head(rows)
    display = out.rename(columns={
        "producto": "Producto",
        "usd_base": f"USD {ctx['base'] or 'base'}",
        "usd_compare": f"USD {ctx['compare']}",
        "dif_usd": "Dif. USD",
        "var_usd": "Var. USD",
        "tallos_base": f"Tallos {ctx['base'] or 'base'}",
        "tallos_compare": f"Tallos {ctx['compare']}",
        "dif_tallos": "Dif. tallos",
        "var_tallos": "Var. tallos",
        "share": f"Share tallos {ctx['compare']}",
    })
    for col in [c for c in display.columns if c.startswith("USD") or c == "Dif. USD"]:
        display[col] = display[col].map(lambda v: money(v, 2))
    for col in [c for c in display.columns if c.startswith("Tallos") or c == "Dif. tallos"]:
        display[col] = display[col].map(lambda v: money(v, 0))
    if f"Share tallos {ctx['compare']}" in display:
        display[f"Share tallos {ctx['compare']}"] = display[f"Share tallos {ctx['compare']}"].map(lambda v: percent(v).replace("+", ""))
    return display


def dimension_growth(view: pd.DataFrame, ctx: dict, group_cols: list[str], rows: int = 20) -> pd.DataFrame:
    if not ctx["comparison"]:
        return pd.DataFrame()
    base = ctx["base_frame"].groupby(group_cols, dropna=False, as_index=False).agg(usd_base=("ventas_usd", "sum"), tallos_base=("tallos_confirmados", "sum"))
    comp = ctx["compare_frame"].groupby(group_cols, dropna=False, as_index=False).agg(usd_compare=("ventas_usd", "sum"), tallos_compare=("tallos_confirmados", "sum"))
    out = base.merge(comp, on=group_cols, how="outer").fillna(0)
    out["dif_usd"] = out["usd_compare"] - out["usd_base"]
    out["var_usd"] = out.apply(lambda r: variation_label(r["usd_base"], r["usd_compare"], LOW_USD_BASE_THRESHOLD), axis=1)
    out = out.sort_values("usd_compare", ascending=False).head(rows)
    rename = {col: col.replace("_", " ").title() for col in group_cols}
    rename.update({"usd_base": f"USD {ctx['base']}", "usd_compare": f"USD {ctx['compare']}", "dif_usd": "Dif. USD", "var_usd": "Var. USD"})
    out = out.rename(columns=rename)
    for col in [f"USD {ctx['base']}", f"USD {ctx['compare']}", "Dif. USD"]:
        out[col] = out[col].map(lambda v: money(v, 2))
    return out[[*rename.values()]]


def product_week_matrix(view: pd.DataFrame, rows: int = 80) -> pd.DataFrame:
    if view.empty:
        return pd.DataFrame()
    work = view.copy()
    work["semana_col"] = work["anio"].astype(str) + "-S" + work["semana_iso"].astype(str).str.zfill(2)
    grouped = work.groupby(["producto", "semana_col"], as_index=False)["tallos_confirmados"].sum()
    matrix = grouped.pivot_table(index="producto", columns="semana_col", values="tallos_confirmados", aggfunc="sum", fill_value=0).reset_index()
    week_cols = [col for col in matrix.columns if col != "producto"]
    matrix["Total"] = matrix[week_cols].sum(axis=1)
    matrix = matrix.sort_values("Total", ascending=False).head(rows).rename(columns={"producto": "Producto"})
    for col in week_cols + ["Total"]:
        matrix[col] = matrix[col].map(lambda v: money(v, 0))
    return matrix


def build_figures(view: pd.DataFrame, ctx: dict) -> dict[str, go.Figure]:
    if view.empty or not ctx.get("ok"):
        return {key: empty_figure(title) for key, title in {
            "consolidated": "Consolidado real USD",
            "monthly": "Facturacion USD por mes",
            "weekly": "Tallos confirmados por semana",
            "product_usd": "Facturacion por producto",
            "mix": "Mix por producto",
            "price": "Precio por producto",
            "opportunity": "Matriz de oportunidad",
            "color": "Color comercial",
            "country": "Mercados destino",
            "product_color": "Producto-color",
        }.items()}

    annual_rows = []
    if ctx["comparison"]:
        annual_rows.append({"anio": f"Año base {ctx['base']}", "ventas": ctx["base_m"]["ventas"]})
    annual_rows.append({"anio": f"Año seleccionado {ctx['compare']}", "ventas": ctx["comp_m"]["ventas"]})
    fig_consolidated = px.bar(pd.DataFrame(annual_rows), x="anio", y="ventas", title="Facturación anual: base vs. seleccionado", color="anio", color_discrete_sequence=["#4E79A7", CORPORATE_BURGUNDY])
    apply_layout(fig_consolidated, 330)
    fig_consolidated.update_yaxes(title="USD", tickformat=",.2f")

    monthly = summarize(view[view["anio"].isin([y for y in [ctx["base"], ctx["compare"]] if y])], ["anio", "mes"])
    monthly["Mes"] = monthly["mes"].map(lambda m: MONTHS[int(m) - 1] if 1 <= int(m) <= 12 else str(m))
    monthly["Año"] = monthly["anio"].astype(int).astype(str)
    year_colors = {
        str(ctx["base"]): "#4E79A7",
        str(ctx["compare"]): CORPORATE_BURGUNDY,
    }
    fig_monthly = px.bar(
        monthly,
        x="Mes",
        y="ventas_usd",
        color="Año",
        barmode="group",
        title="Facturación mensual: año base vs. año seleccionado",
        labels={"ventas_usd": "Facturación (USD)"},
        color_discrete_map=year_colors,
        category_orders={"Mes": MONTHS},
    )
    apply_layout(fig_monthly, 360)
    fig_monthly.update_yaxes(title="Facturación (USD)", tickformat="$,.0f")
    fig_monthly.update_xaxes(title="Mes")
    fig_monthly.update_layout(legend_title_text="Año", hovermode="x unified")

    weekly = summarize(view, ["anio", "semana_iso"]).sort_values(["anio", "semana_iso"])
    weekly["Año"] = weekly["anio"].astype(int).astype(str)
    fig_weekly = px.line(weekly, x="semana_iso", y="tallos_confirmados", color="Año", markers=True, title="Tallos semanales por año", color_discrete_map=year_colors)
    apply_layout(fig_weekly, 370)
    fig_weekly.update_yaxes(title="Tallos", tickformat=",d")
    fig_weekly.update_xaxes(title="Semana ISO")

    prod = product_compare_table(ctx, rows=10)
    raw_prod = ctx["compare_frame"].groupby("producto", as_index=False).agg(ventas_usd=("ventas_usd", "sum"), tallos_confirmados=("tallos_confirmados", "sum")).sort_values("ventas_usd", ascending=False).head(10)
    fig_product_usd = px.bar(raw_prod.sort_values("ventas_usd"), y="producto", x="ventas_usd", orientation="h", title=f"Productos que explican la facturación — {ctx['compare']}", color_discrete_sequence=[CORPORATE_BURGUNDY])
    apply_layout(fig_product_usd, 370)
    fig_product_usd.update_xaxes(title="USD", tickformat=",.2f")
    fig_product_usd.update_yaxes(title="")

    mix = ctx["compare_frame"].groupby("producto", as_index=False)["tallos_confirmados"].sum().sort_values("tallos_confirmados", ascending=False)
    if len(mix) > 7:
        mix = pd.concat([mix.head(7), pd.DataFrame([{"producto": "Otros", "tallos_confirmados": mix.iloc[7:]["tallos_confirmados"].sum()}])])
    fig_mix = px.pie(mix, names="producto", values="tallos_confirmados", hole=0.42, title=f"Mix de tallos {ctx['compare']}", color_discrete_sequence=CORPORATE_SEQUENCE)
    apply_layout(fig_mix, 360)

    price = ctx["compare_frame"].groupby("producto", as_index=False).agg(ventas_usd=("ventas_usd", "sum"), tallos=("tallos_confirmados", "sum"))
    price["precio"] = (price["ventas_usd"] / price["tallos"].replace(0, np.nan)).fillna(0)
    price = price.sort_values("ventas_usd", ascending=False).head(12).sort_values("precio")
    fig_price = px.bar(price, y="producto", x="precio", orientation="h", title=f"Precio promedio por producto — {ctx['compare']}", color_discrete_sequence=["#4E79A7"])
    apply_layout(fig_price, 360)
    fig_price.update_xaxes(title="USD/tallo", tickformat=",.4f")
    fig_price.update_yaxes(title="")

    opp = ctx["compare_frame"].groupby("producto", as_index=False).agg(ventas_usd=("ventas_usd", "sum"), tallos=("tallos_confirmados", "sum"), clientes=("cod_cliente", "nunique"))
    opp["precio"] = (opp["ventas_usd"] / opp["tallos"].replace(0, np.nan)).fillna(0)
    fig_opp = px.scatter(opp, x="tallos", y="precio", size="ventas_usd", color="producto", hover_data=["clientes", "ventas_usd"], title=f"Matriz de oportunidad: volumen vs. precio — {ctx['compare']}", color_discrete_sequence=CORPORATE_SEQUENCE)
    apply_layout(fig_opp, 360)
    fig_opp.update_xaxes(title="Tallos", tickformat=",d")
    fig_opp.update_yaxes(title="USD/tallo", tickformat=",.4f")

    colors = ctx["compare_frame"].groupby("color", as_index=False).agg(tallos=("tallos_confirmados", "sum"), ventas_usd=("ventas_usd", "sum")).sort_values("tallos", ascending=False).head(14)
    color_map = {row["color"]: flower_color(row["color"], idx) for idx, row in colors.reset_index(drop=True).iterrows()}
    fig_color = px.bar(
        colors.sort_values("tallos"),
        y="color",
        x="tallos",
        orientation="h",
        title=f"Colores comerciales con mayor volumen — {ctx['compare']}",
        color="color",
        color_discrete_map=color_map,
        hover_data=["ventas_usd"],
    )
    apply_layout(fig_color, 390)
    fig_color.update_xaxes(title="Tallos", tickformat=",d")
    fig_color.update_yaxes(title="")

    country = ctx["compare_frame"].groupby("pais", as_index=False).agg(ventas_usd=("ventas_usd", "sum"), tallos=("tallos_confirmados", "sum"), clientes=("cod_cliente", "nunique")).sort_values("ventas_usd", ascending=False).head(14)
    fig_country = px.bar(
        country.sort_values("ventas_usd"),
        y="pais",
        x="ventas_usd",
        orientation="h",
        title=f"Mercados destino por facturación — {ctx['compare']}",
        color_discrete_sequence=["#4E79A7"],
        hover_data=["tallos", "clientes"],
    )
    apply_layout(fig_country, 390)
    fig_country.update_xaxes(title="Ventas USD", tickformat=",.2f")
    fig_country.update_yaxes(title="")

    pc = ctx["compare_frame"].groupby("producto_color", as_index=False).agg(tallos=("tallos_confirmados", "sum"), ventas_usd=("ventas_usd", "sum"), clientes=("cod_cliente", "nunique")).sort_values("tallos", ascending=False).head(16)
    fig_product_color = px.bar(
        pc.sort_values("tallos"),
        y="producto_color",
        x="tallos",
        orientation="h",
        title=f"Producto-color: demanda accionable — {ctx['compare']}",
        color_discrete_sequence=[CORPORATE_BURGUNDY],
        hover_data=["ventas_usd", "clientes"],
    )
    apply_layout(fig_product_color, 440)
    fig_product_color.update_xaxes(title="Tallos", tickformat=",d")
    fig_product_color.update_yaxes(title="")

    return {
        "consolidated": fig_consolidated,
        "monthly": fig_monthly,
        "weekly": fig_weekly,
        "product_usd": fig_product_usd,
        "mix": fig_mix,
        "price": fig_price,
        "opportunity": fig_opp,
        "color": fig_color,
        "country": fig_country,
        "product_color": fig_product_color,
    }


def insight_cards(view: pd.DataFrame, ctx: dict) -> list[html.Div]:
    if view.empty or not ctx.get("ok"):
        return [html.Div("No hay datos para construir lectura ejecutiva.", className="strategy-card")]
    items = []
    if ctx["comparison"]:
        usd_delta = ctx["comp_m"]["ventas"] - ctx["base_m"]["ventas"]
        tallos_delta = ctx["comp_m"]["tallos"] - ctx["base_m"]["tallos"]
        items.append(f"Ventas: {money(ctx['base_m']['ventas'], 2)} USD en {ctx['base']} vs {money(ctx['comp_m']['ventas'], 2)} USD en {ctx['compare']} ({variation_label(ctx['base_m']['ventas'], ctx['comp_m']['ventas'], LOW_USD_BASE_THRESHOLD)}).")
        items.append(f"Tallos: diferencia de {money(tallos_delta, 0)} tallos frente al año base.")
        items.append(f"Precio: pasa de {money(ctx['base_m']['precio'], 4)} a {money(ctx['comp_m']['precio'], 4)} USD/tallo.")
    else:
        items.append(f"El alcance filtrado tiene {money(ctx['comp_m']['ventas'], 2)} USD y {money(ctx['comp_m']['tallos'], 0)} tallos confirmados en {ctx['compare']}.")
    top_product = ctx["compare_frame"].groupby("producto")["ventas_usd"].sum().sort_values(ascending=False).head(1)
    top_client = ctx["compare_frame"].groupby("cliente")["ventas_usd"].sum().sort_values(ascending=False).head(1)
    if not top_product.empty:
        items.append(f"Producto líder por facturación: {top_product.index[0]} con {money(top_product.iloc[0], 2)} USD.")
    if not top_client.empty:
        items.append(f"Cliente líder por facturación: {top_client.index[0]} con {money(top_client.iloc[0], 2)} USD.")
    top_color = ctx["compare_frame"].groupby("color")["tallos_confirmados"].sum().sort_values(ascending=False).head(1)
    if not top_color.empty:
        items.append(f"Color comercial líder por volumen: {top_color.index[0]} con {money(top_color.iloc[0], 0)} tallos.")
    return [html.Div([html.Div(f"{idx:02d}", className="strategy-index"), html.Div(text, className="strategy-text")], className="strategy-card") for idx, text in enumerate(items[:5], 1)]


def concentration_cards(view: pd.DataFrame, ctx: dict) -> list[html.Div]:
    frame = ctx.get("compare_frame", pd.DataFrame())
    if frame.empty:
        return [scope_card("Concentracion", "Sin datos", "No hay informacion para el año seleccionado")]
    total_tallos = float(frame["tallos_confirmados"].sum())
    total_usd = float(frame["ventas_usd"].sum())

    def share(group_col: str, value_col: str, top_n: int) -> float:
        if frame.empty or group_col not in frame or total_tallos <= 0:
            return 0.0
        grouped = frame.groupby(group_col)[value_col].sum().sort_values(ascending=False)
        denom = total_tallos if value_col == "tallos_confirmados" else total_usd
        return float(grouped.head(top_n).sum() / denom) if denom else 0.0

    return [
        scope_card("Top 5 clientes", percent(share("cod_cliente", "ventas_usd", 5)).replace("+", ""), "Participación en ventas USD"),
        scope_card("Top 5 productos", percent(share("producto", "tallos_confirmados", 5)).replace("+", ""), "Participación en tallos"),
        scope_card("Top 5 colores", percent(share("color", "tallos_confirmados", 5)).replace("+", ""), "Lectura de mix floral"),
        scope_card("Países activos", money(frame["pais"].nunique(), 0), "Mercados con venta confirmada"),
    ]


def flower_mix_cards(ctx: dict) -> list[html.Div]:
    frame = ctx.get("compare_frame", pd.DataFrame())
    if frame.empty:
        return [flower_chip("Sin color", "Sin datos", "#9CA3AF", "No hay ventas para el alcance seleccionado")]
    colors = (
        frame.groupby("color", as_index=False)
        .agg(tallos=("tallos_confirmados", "sum"), ventas_usd=("ventas_usd", "sum"), productos=("producto", "nunique"))
        .sort_values("tallos", ascending=False)
        .head(6)
        .reset_index(drop=True)
    )
    total = max(float(colors["tallos"].sum()), 1.0)
    cards = []
    for idx, row in colors.iterrows():
        share = float(row["tallos"]) / total
        cards.append(
            flower_chip(
                str(row["color"]).title(),
                money(row["tallos"], 0),
                flower_color(row["color"], idx),
                f"{percent(share).replace('+', '')} del top color | {money(row['productos'], 0)} productos",
            )
        )
    return cards


def build_options(df: pd.DataFrame, column: str, label_col: str | None = None, top: int | None = None) -> list[dict]:
    if df.empty or column not in df:
        return []
    label_col = label_col or column
    grouped = df.groupby(column, dropna=False).agg(label=(label_col, "first"), tallos=("tallos_confirmados", "sum")).reset_index().sort_values("tallos", ascending=False)
    if top:
        grouped = grouped.head(top)
    return [{"label": f"{row['label']} | {money(row['tallos'], 0)} tallos", "value": str(row[column])} for _, row in grouped.iterrows()]


def make_app(data_path: str | None = None, data_dir: str | None = None) -> Dash:
    config = load_config()
    source_path = data_path or (str(config.data_path) if config.data_path else None)
    source_dir = data_dir or str(config.data_dir)
    df = load_dashboard_data(source_path, source_dir)
    years = sorted(df["anio"].dropna().astype(int).unique().tolist())
    default_compare = years[-1] if years else None
    default_base = years[-2] if len(years) > 1 else None
    default_visible_years = [year for year in [default_base, default_compare] if year is not None]
    week_min, week_max = int(df["semana_iso"].min()), int(df["semana_iso"].max())

    app = Dash(__name__, title="LGF Ventas Generales")
    app.layout = html.Div(
        [
            html.Div(
                [
                    html.Div(
                        [
                            html.Div("La Gaitana Farms", className="kicker"),
                            html.H1("Ventas generales"),
                            html.P("Vista descriptiva enfocada en los dos años más recientes; puedes ampliar el histórico desde los filtros."),
                            html.Div(
                                [
                                    html.A("Ventas generales", href="http://127.0.0.1:8052", className="nav-link active"),
                                    html.A("Forecast SOLIDO", href="http://127.0.0.1:8053", className="nav-link"),
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
                    html.Div([html.Label("Año base"), dcc.Dropdown(id="base-year", options=[{"label": str(y), "value": y} for y in years], value=default_base, clearable=True)], className="control"),
                    html.Div([html.Label("Año comparativo"), dcc.Dropdown(id="compare-year", options=[{"label": str(y), "value": y} for y in years], value=default_compare, clearable=False)], className="control"),
                    html.Div([html.Label("Años visibles"), dcc.Dropdown(id="years", options=[{"label": str(y), "value": y} for y in years], value=default_visible_years, multi=True, clearable=False)], className="control control-wide"),
                    html.Div([html.Label("Semanas ISO"), dcc.RangeSlider(id="weeks", min=week_min, max=week_max, value=[week_min, week_max], marks={week_min: str(week_min), week_max: str(week_max)}, tooltip={"placement": "bottom"})], className="control control-wide"),
                    html.Div([html.Label("Compañía"), dcc.Dropdown(id="companies", options=build_options(df, "NomCompania", top=80), multi=True, placeholder="Todas")], className="control"),
                    html.Div([html.Label("Cliente"), dcc.Dropdown(id="clients", options=build_options(df, "cod_cliente", "cliente", top=120), multi=True, placeholder="Todos")], className="control"),
                    html.Div([html.Label("Pais"), dcc.Dropdown(id="countries", options=build_options(df, "pais"), multi=True, placeholder="Todos")], className="control"),
                    html.Div([html.Label("Producto"), dcc.Dropdown(id="products", options=build_options(df, "producto"), multi=True, placeholder="Todos")], className="control"),
                    html.Div([html.Label("Color"), dcc.Dropdown(id="colors", options=build_options(df, "color", top=120), multi=True, placeholder="Todos")], className="control"),
                    html.Div([html.Label("Tipo operativo"), dcc.Dropdown(id="types", options=build_options(df, "tipo_pedido_operativo"), multi=True, placeholder="Todos")], className="control"),
                ],
                className="filters",
            ),
            html.Div(id="metrics", className="metrics-grid"),
            html.Div(
                [
                    html.Div([html.Div("Comparativo contra año base", className="panel-title"), dcc.Graph(id="fig-consolidated")], className="panel"),
                    html.Div([html.Div("Facturacion mensual", className="panel-title"), dcc.Graph(id="fig-monthly")], className="panel"),
                    html.Div([html.Div("Volumen semanal", className="panel-title"), dcc.Graph(id="fig-weekly")], className="panel"),
                    html.Div([html.Div("Facturacion por producto", className="panel-title"), dcc.Graph(id="fig-product-usd")], className="panel"),
                    html.Div([html.Div("Mix comercial", className="panel-title"), dcc.Graph(id="fig-mix")], className="panel"),
                    html.Div([html.Div("Precio y oportunidad", className="panel-title"), dcc.Graph(id="fig-price"), dcc.Graph(id="fig-opportunity")], className="panel"),
                ],
                className="grid-2",
            ),
            html.Div([html.Div("Lectura ejecutiva", className="panel-title"), html.Div(id="insights", className="strategy-grid")], className="strategy-panel section-gap"),
            html.Div(
                [
                    html.Div("Concentracion y alcance", className="panel-title"),
                    html.Div(id="scope-cards", className="scope-strip"),
                ],
                className="strategy-panel section-gap",
            ),
            html.Div(
                [
                    html.Div("Lectura floral del mix", className="panel-title"),
                    html.Div("Colores dominantes por tallos confirmados para orientar oferta, surtido y conversacion comercial.", className="panel-note"),
                    html.Div(id="flower-mix", className="flower-strip"),
                ],
                className="flower-panel section-gap",
            ),
            html.Div(
                [
                    html.Div([html.Div("Producto-color accionable", className="panel-title"), dcc.Graph(id="fig-product-color")], className="panel"),
                    html.Div([html.Div("Color comercial", className="panel-title"), dcc.Graph(id="fig-color")], className="panel"),
                    html.Div([html.Div("Mercados destino", className="panel-title"), dcc.Graph(id="fig-country")], className="panel panel-wide"),
                ],
                className="grid-2 section-gap",
            ),
            html.Div(
                [
                    html.Div([html.Div("Comparativo por producto", className="panel-title"), html.Div(id="product-table")], className="table-panel"),
                    html.Div([html.Div("Clientes por facturacion", className="panel-title"), html.Div(id="client-table")], className="table-panel"),
                    html.Div([html.Div("Crecimiento por pais", className="panel-title"), html.Div(id="country-table")], className="table-panel"),
                    html.Div([html.Div("Producto por semana", className="panel-title"), html.Div(id="week-matrix")], className="table-panel"),
                ],
                className="table-grid",
            ),
        ],
        className="page",
    )

    app.index_string = """
    <!DOCTYPE html><html><head>{%metas%}<title>{%title%}</title>{%favicon%}{%css%}
    <style>
    body{margin:0;background:#eef2f6;color:#17202a;font-family:Inter,Arial,sans-serif}.page{max-width:1600px;margin:0 auto;padding:20px}
    .hero{display:grid;grid-template-columns:minmax(0,1fr) 430px;gap:18px;align-items:end;background:linear-gradient(135deg,#7a001f 0%,#a51f43 44%,#326fa8 100%);color:#fff;border:1px solid #74122b;border-radius:8px;padding:24px 28px;margin-bottom:12px;box-shadow:0 14px 30px rgba(23,32,42,.14)}
    .kicker{color:#f8d7df;text-transform:uppercase;font-size:12px;font-weight:800;letter-spacing:.08em}h1{margin:5px 0 8px;font-size:40px;line-height:1.05;letter-spacing:0}.hero p{margin:0;color:#f6e7ec;font-size:16px;max-width:820px}
    .nav-links{display:flex;flex-wrap:wrap;gap:8px;margin-top:14px}.nav-link{display:inline-flex;align-items:center;min-height:34px;padding:7px 11px;border-radius:8px;border:1px solid rgba(255,255,255,.35);color:#fff;text-decoration:none;font-size:13px;font-weight:800;background:rgba(255,255,255,.10)}.nav-link.active{background:#fff;color:#800020}
    .source-card{background:rgba(255,255,255,.12);border:1px solid rgba(255,255,255,.28);border-radius:8px;padding:13px}.source-label{font-size:11px;font-weight:800;color:#f8d7df;text-transform:uppercase}.source-path{font-size:13px;word-break:break-all;color:#fff}
    .filters{display:grid;grid-template-columns:repeat(5,minmax(0,1fr));gap:10px;background:#fff;border:1px solid #d9dee7;border-left:5px solid #800020;border-radius:8px;padding:13px;margin-bottom:12px;box-shadow:0 8px 18px rgba(23,32,42,.05)}.control-wide{grid-column:span 2}label{display:block;font-size:11px;font-weight:800;color:#374151;text-transform:uppercase;margin-bottom:4px}
    .metrics-grid{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:12px;margin-bottom:12px}.metric-card{background:#fff;border:1px solid #d9dee7;border-top:4px solid #800020;border-radius:8px;padding:13px;min-height:96px;box-shadow:0 8px 18px rgba(23,32,42,.05)}.metric-head{display:flex;justify-content:space-between;gap:8px}.metric-title{font-size:11px;font-weight:800;color:#667085;text-transform:uppercase}.metric-value{font-size:27px;font-weight:800;margin-top:10px;color:#17202a}.metric-detail{font-size:12px;color:#667085;margin-top:5px}.delta{font-size:12px;font-weight:800;border-radius:999px;padding:3px 7px;background:#eef2f7}.positive{background:#e8f5ef;color:#027a48}.negative{background:#fdecec;color:#b42318}.neutral{background:#eef2f7;color:#667085}
    .grid-2{display:grid;grid-template-columns:1fr 1fr;gap:12px}.panel,.table-panel,.strategy-panel,.flower-panel{background:#fff;border:1px solid #d9dee7;border-radius:8px;padding:13px;min-width:0;box-shadow:0 8px 18px rgba(23,32,42,.05)}.panel-wide{grid-column:1/-1}.panel-title{font-size:16px;font-weight:800;margin:2px 0 10px;color:#17202a}.panel-note{color:#667085;font-size:13px;margin:-4px 0 12px}.section-gap{margin-top:12px}
    .strategy-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:10px}.strategy-card{display:grid;grid-template-columns:40px 1fr;gap:10px;background:#fbfcfd;border:1px solid #e6e9ef;border-radius:8px;padding:12px}.strategy-index{display:flex;align-items:center;justify-content:center;height:32px;width:32px;border-radius:50%;background:#f8d7df;font-weight:800;color:#800020}.strategy-text{line-height:1.45;color:#374151}
    .scope-strip{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:10px}.scope-card{background:#fbfcfd;border:1px solid #e6e9ef;border-radius:8px;padding:12px}.scope-label{font-size:11px;text-transform:uppercase;font-weight:800;color:#667085}.scope-value{font-size:22px;font-weight:800;margin-top:6px}.scope-detail{font-size:12px;color:#667085;margin-top:4px}
    .flower-panel{border-left:5px solid #59a14f;background:linear-gradient(180deg,#fff 0%,#fbfdfb 100%)}.flower-strip{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:10px}.flower-chip{display:grid;grid-template-columns:42px 1fr;gap:10px;align-items:center;background:#fff;border:1px solid #e6e9ef;border-radius:8px;padding:10px}.flower-swatch{width:32px;height:32px;border-radius:50%;border:3px solid #fff;box-shadow:0 0 0 1px #d9dee7}.flower-chip-label{font-size:12px;font-weight:800;text-transform:uppercase;color:#374151}.flower-chip-value{font-size:20px;font-weight:800;color:#17202a}.flower-chip-detail{font-size:12px;color:#667085}
    .table-grid{display:grid;grid-template-columns:1fr 1fr;gap:14px;margin-top:14px}.dash-table-container .dash-spreadsheet-container .dash-spreadsheet-inner th{background:#800020!important;color:#fff!important;font-weight:800!important}.dash-table-container .dash-spreadsheet-container .dash-spreadsheet-inner td{font-size:12px}
    @media(max-width:1150px){.hero,.filters,.grid-2,.table-grid{grid-template-columns:1fr}.control-wide{grid-column:auto}.metrics-grid,.scope-strip,.flower-strip{grid-template-columns:1fr 1fr}}@media(max-width:650px){.metrics-grid,.strategy-grid,.scope-strip,.flower-strip{grid-template-columns:1fr}.page{padding:12px}h1{font-size:32px}}
    </style></head><body>{%app_entry%}<footer>{%config%}{%scripts%}{%renderer%}</footer></body></html>
    """

    @app.callback(
        Output("metrics", "children"),
        Output("fig-consolidated", "figure"),
        Output("fig-monthly", "figure"),
        Output("fig-weekly", "figure"),
        Output("fig-product-usd", "figure"),
        Output("fig-mix", "figure"),
        Output("fig-price", "figure"),
        Output("fig-opportunity", "figure"),
        Output("insights", "children"),
        Output("scope-cards", "children"),
        Output("flower-mix", "children"),
        Output("fig-product-color", "figure"),
        Output("fig-color", "figure"),
        Output("fig-country", "figure"),
        Output("product-table", "children"),
        Output("client-table", "children"),
        Output("country-table", "children"),
        Output("week-matrix", "children"),
        Input("base-year", "value"),
        Input("compare-year", "value"),
        Input("years", "value"),
        Input("weeks", "value"),
        Input("companies", "value"),
        Input("clients", "value"),
        Input("countries", "value"),
        Input("products", "value"),
        Input("colors", "value"),
        Input("types", "value"),
    )
    def update(base_year, compare_year, years_sel, weeks, companies, clients, countries, products, colors, types):
        view = filter_frame(df, years_sel, weeks, companies, clients, countries, products, colors, types)
        ctx = build_context(view, base_year, compare_year)
        if not ctx.get("ok"):
            figs = build_figures(view, ctx)
            return (
                [],
                figs["consolidated"],
                figs["monthly"],
                figs["weekly"],
                figs["product_usd"],
                figs["mix"],
                figs["price"],
                figs["opportunity"],
                [],
                [],
                [],
                figs["product_color"],
                figs["color"],
                figs["country"],
                table(pd.DataFrame()),
                table(pd.DataFrame()),
                table(pd.DataFrame()),
                table(pd.DataFrame()),
            )

        bm, cm = ctx["base_m"], ctx["comp_m"]
        cards = [
            metric_card("Ventas USD", money(cm["ventas"], 2), f"Año seleccionado {ctx['compare']}", variation_label(bm["ventas"], cm["ventas"], LOW_USD_BASE_THRESHOLD) if ctx["comparison"] else None),
            metric_card("Tallos confirmados", money(cm["tallos"], 0), "Volumen real", variation_label(bm["tallos"], cm["tallos"], LOW_STEMS_BASE_THRESHOLD) if ctx["comparison"] else None),
            metric_card("Precio promedio", f"US$ {money(cm['precio'], 4)}", "USD/tallo ponderado", variation_label(bm["precio"], cm["precio"]) if ctx["comparison"] else None),
            metric_card("Pedidos", money(cm["pedidos"], 0), "Pedidos distintos", variation_label(bm["pedidos"], cm["pedidos"]) if ctx["comparison"] else None),
            metric_card("Clientes activos", money(cm["clientes"], 0), "Con venta confirmada", variation_label(bm["clientes"], cm["clientes"]) if ctx["comparison"] else None),
            metric_card("Productos activos", money(cm["productos"], 0), "Portafolio vendido", variation_label(bm["productos"], cm["productos"]) if ctx["comparison"] else None),
            metric_card("Venta prom. pedido", f"US$ {money(cm['venta_pedido'], 2)}", "Facturacion / pedido"),
            metric_card("Tallos prom. pedido", money(cm["tallos_pedido"], 0), "Tallos / pedido"),
        ]
        figs = build_figures(view, ctx)
        clients_table = summarize(view, ["cod_cliente", "cliente"]).sort_values("ventas_usd", ascending=False).head(30)
        clients_table = clients_table.rename(columns={"cod_cliente": "Cod. cliente", "cliente": "Cliente", "ventas_usd": "Facturacion USD", "tallos_confirmados": "Tallos", "pedidos": "Pedidos", "precio_usd_tallo": "USD/tallo"})
        clients_table = clients_table[["Cod. cliente", "Cliente", "Facturacion USD", "Tallos", "Pedidos", "USD/tallo"]]
        clients_table["Facturacion USD"] = clients_table["Facturacion USD"].map(lambda v: money(v, 2))
        clients_table["Tallos"] = clients_table["Tallos"].map(lambda v: money(v, 0))
        clients_table["USD/tallo"] = clients_table["USD/tallo"].map(lambda v: money(v, 4))
        return (
            cards,
            figs["consolidated"],
            figs["monthly"],
            figs["weekly"],
            figs["product_usd"],
            figs["mix"],
            figs["price"],
            figs["opportunity"],
            insight_cards(view, ctx),
            concentration_cards(view, ctx),
            flower_mix_cards(ctx),
            figs["product_color"],
            figs["color"],
            figs["country"],
            table(product_compare_table(ctx), 12),
            table(clients_table, 12, [{"column_id": "Facturacion USD", "direction": "desc"}]),
            table(dimension_growth(view, ctx, ["pais"]), 12),
            table(product_week_matrix(view), 12, [{"column_id": "Total", "direction": "desc"}]),
        )

    return app


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Dashboard ejecutivo de ventas generales LGF.")
    parser.add_argument("--data-path", default=os.getenv("LGF_DATA_PATH"), help="Ruta al historic_sales_acum.csv")
    parser.add_argument("--data-dir", default=os.getenv("LGF_DATA_DIR"), help="Carpeta de respaldo con CSV por anio.")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", default=8052, type=int)
    parser.add_argument("--debug", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    app = make_app(data_path=args.data_path, data_dir=args.data_dir)
    app.run(host=args.host, port=args.port, debug=args.debug)


if __name__ == "__main__":
    main()
