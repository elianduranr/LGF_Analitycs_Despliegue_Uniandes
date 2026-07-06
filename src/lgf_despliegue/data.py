from __future__ import annotations

from pathlib import Path

import pandas as pd


COLUMN_ALIASES = {
    "fecha": ["fecha", "FECHA", "Fecha"],
    "cod_cliente": ["cod_cliente", "CODCUSTOM", "CodCustom"],
    "cliente": ["cliente", "CLIENTE", "Cliente"],
    "NomCompania": ["NomCompania", "NOMCOMPANIA", "Compania", "COMPANIA"],
    "cliente_consolidado": ["cliente_consolidado", "CLIENTECONSOL", "ClienteConsol"],
    "producto": ["producto", "PRODUCTO", "Producto"],
    "color": ["color", "COLOR", "Color", "NomColor"],
    "pais": ["pais", "PAIS", "Pais"],
    "ciudad": ["ciudad", "CIUDAD", "Ciudad"],
    "estado": ["estado", "ESTADO", "Estado"],
    "pedido": ["pedido", "PEDIDO", "Pedido"],
    "tipo_pedido_operativo": ["tipo_pedido_operativo", "TIPO_PEDIDO_OPERATIVO"],
    "tipo_empaque": ["tipo_empaque", "TIPEMPAQUE", "TipoEmpaque"],
    "tipo_orden_empaque": ["tipo_orden_empaque", "TIPORDENEMPAQUE", "TipoOrdenEmpaque"],
    "empaque": ["empaque", "EMPAQUE", "Empaque"],
    "tallos_pedidos": ["tallos_pedidos", "TallosPedidos", "TALLOSPEDIDOS"],
    "tallos_confirmados": ["tallos_confirmados", "TallosConfirmados", "TALLOSCONFIRMADOS"],
    "tallos_total": ["tallos_total", "TOTALTALLOS", "TotalTallos"],
    "ventas_usd": ["ventas_usd", "VENTAS_USD", "Ventas_USD"],
    "valor_total": ["valor_total", "VALORTOTAL", "ValorTotal"],
    "valor_total_original": ["valor_total_original", "VALORTOTAL", "ValorTotal"],
    "moneda": ["moneda", "NomMoneda", "NOMMONEDA"],
}


def _rename_columns(frame: pd.DataFrame) -> pd.DataFrame:
    rename = {}
    columns = set(frame.columns)
    for canonical, aliases in COLUMN_ALIASES.items():
        if canonical in columns:
            continue
        for alias in aliases:
            if alias in columns:
                rename[alias] = canonical
                break
    return frame.rename(columns=rename)


def _normalize_text(series: pd.Series) -> pd.Series:
    return (
        series.fillna("sin_info")
        .astype(str)
        .str.strip()
        .str.lower()
        .replace({"": "sin_info", "nan": "sin_info", "none": "sin_info"})
    )


def clean_sales_frame(frame: pd.DataFrame) -> pd.DataFrame:
    """Normaliza columnas minimas para ventas generales y forecast."""
    out = _rename_columns(frame.copy())
    required = [
        "fecha",
        "cod_cliente",
        "cliente",
        "NomCompania",
        "cliente_consolidado",
        "producto",
        "color",
        "pais",
        "ciudad",
        "estado",
        "pedido",
        "tipo_pedido_operativo",
        "tipo_empaque",
        "tipo_orden_empaque",
        "empaque",
        "tallos_pedidos",
        "tallos_confirmados",
        "tallos_total",
        "ventas_usd",
        "valor_total",
        "valor_total_original",
        "moneda",
    ]
    for col in required:
        if col not in out.columns:
            out[col] = pd.NA

    out["fecha"] = pd.to_datetime(out["fecha"], errors="coerce")
    out = out[out["fecha"].notna()].copy()
    for col in ["tallos_pedidos", "tallos_confirmados", "tallos_total", "ventas_usd", "valor_total", "valor_total_original"]:
        out[col] = pd.to_numeric(out[col], errors="coerce").fillna(0)

    for col in [
        "cod_cliente",
        "cliente",
        "NomCompania",
        "cliente_consolidado",
        "producto",
        "color",
        "pais",
        "ciudad",
        "estado",
        "tipo_pedido_operativo",
        "tipo_empaque",
        "tipo_orden_empaque",
        "empaque",
        "moneda",
    ]:
        out[col] = _normalize_text(out[col])

    out["cliente_analisis"] = out["cliente_consolidado"].where(
        ~out["cliente_consolidado"].isin(["sin_info", "nan", "none", ""]), out["cliente"]
    )
    out["tallos_demanda"] = out["tallos_confirmados"].where(out["tallos_confirmados"] > 0, out["tallos_total"])
    out["producto_color"] = out["producto"] + " / " + out["color"]
    out["es_confirmado"] = out["estado"].str.contains("confirm", na=False)
    text_for_type = (
        out["tipo_empaque"].astype(str)
        + " "
        + out["tipo_orden_empaque"].astype(str)
        + " "
        + out["empaque"].astype(str)
    )
    out["es_solido"] = text_for_type.str.contains("solido|solid", regex=True, na=False)
    source_type = out["tipo_pedido_operativo"].where(~out["tipo_pedido_operativo"].isin(["sin_info", "nan", "none", ""]), "")
    out["tipo_pedido_operativo"] = source_type.str.upper().where(source_type.ne(""), out["es_solido"].map({True: "SOLIDO", False: "NO_SOLIDO"}))
    out["pedidos"] = out["pedido"].where(~out["pedido"].isin(["sin_info", "nan", "none", ""]), out.index.astype(str))

    iso = out["fecha"].dt.isocalendar()
    out["anio"] = iso.year.astype(int)
    out["semana_iso"] = iso.week.astype(int)
    out["mes"] = out["fecha"].dt.month.astype(int)
    out["week_start"] = pd.to_datetime(
        out["anio"].astype(str) + "-W" + out["semana_iso"].astype(str).str.zfill(2) + "-1",
        format="%G-W%V-%u",
        errors="coerce",
    )
    return out.reset_index(drop=True)


def load_historical_sales(data_dir: str | Path) -> pd.DataFrame:
    """Lee todos los CSV historicos locales de ventas y devuelve una base limpia."""
    root = Path(data_dir)
    files = sorted(root.glob("ventas_facturadas_*.csv"))
    if not files:
        raise FileNotFoundError(f"No se encontraron CSV historicos en {root}")

    frames = []
    for path in files:
        frame = pd.read_csv(path, low_memory=False)
        frame["archivo_origen"] = path.name
        frames.append(frame)
    return clean_sales_frame(pd.concat(frames, ignore_index=True))


def load_sales_source(data_path: str | Path | None = None, data_dir: str | Path | None = None) -> pd.DataFrame:
    """Carga la fuente oficial del proyecto.

    Prioridad:
    1. `data_path`: archivo acumulado unico, recomendado para Elian/Julian.
    2. `data_dir`: carpeta con `ventas_facturadas_*.csv`, respaldo de Entrega 1.
    """
    if data_path:
        path = Path(data_path)
        if not path.exists():
            raise FileNotFoundError(f"No se encontro el acumulado: {path}")
        frame = pd.read_csv(path, low_memory=False)
        frame["archivo_origen"] = path.name
        return clean_sales_frame(frame)
    if data_dir is None:
        raise ValueError("Debe definirse data_path o data_dir.")
    return load_historical_sales(data_dir)
