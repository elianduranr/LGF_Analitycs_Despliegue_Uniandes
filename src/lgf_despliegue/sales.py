from __future__ import annotations

from pathlib import Path

import pandas as pd


def build_general_sales_outputs(sales: pd.DataFrame) -> dict[str, pd.DataFrame]:
    """Construye tablas compactas para la vista de ventas generales."""
    confirmed = sales[sales["es_confirmado"]].copy()
    if confirmed.empty:
        confirmed = sales.copy()

    annual = confirmed.groupby("anio", as_index=False).agg(
        tallos=("tallos_demanda", "sum"),
        ventas_usd=("ventas_usd", "sum"),
        clientes=("cliente_analisis", "nunique"),
        productos=("producto", "nunique"),
        lineas=("fecha", "size"),
    )
    annual["precio_promedio_usd_tallo"] = annual["ventas_usd"] / annual["tallos"].replace(0, pd.NA)

    monthly = confirmed.groupby(["anio", "mes"], as_index=False).agg(
        tallos=("tallos_demanda", "sum"),
        ventas_usd=("ventas_usd", "sum"),
        clientes=("cliente_analisis", "nunique"),
    )
    monthly["periodo"] = monthly["anio"].astype(str) + "-" + monthly["mes"].astype(str).str.zfill(2)

    by_client = (
        confirmed.groupby("cliente_analisis", as_index=False)
        .agg(tallos=("tallos_demanda", "sum"), ventas_usd=("ventas_usd", "sum"), productos=("producto", "nunique"))
        .sort_values("tallos", ascending=False)
        .head(30)
    )

    by_product_color = (
        confirmed.groupby(["producto", "color", "producto_color"], as_index=False)
        .agg(tallos=("tallos_demanda", "sum"), ventas_usd=("ventas_usd", "sum"), clientes=("cliente_analisis", "nunique"))
        .sort_values("tallos", ascending=False)
        .head(50)
    )

    solido_mix = confirmed.groupby("es_solido", as_index=False).agg(
        tallos=("tallos_demanda", "sum"),
        ventas_usd=("ventas_usd", "sum"),
        lineas=("fecha", "size"),
    )
    solido_mix["tipo_pedido"] = solido_mix["es_solido"].map({True: "SOLIDO", False: "NO_SOLIDO"})

    return {
        "ventas_anuales": annual,
        "ventas_mensuales": monthly,
        "top_clientes": by_client,
        "top_producto_color": by_product_color,
        "mix_solido_no_solido": solido_mix[["tipo_pedido", "tallos", "ventas_usd", "lineas"]],
    }


def write_sales_outputs(outputs: dict[str, pd.DataFrame], output_dir: str | Path) -> None:
    target = Path(output_dir)
    target.mkdir(parents=True, exist_ok=True)
    for name, frame in outputs.items():
        frame.to_csv(target / f"{name}.csv", index=False, encoding="utf-8")
