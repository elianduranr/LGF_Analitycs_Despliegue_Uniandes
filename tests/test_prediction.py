import pandas as pd

from lgf_despliegue.forecast import build_weekly_solid_demand
from lgf_despliegue.sales import build_general_sales_outputs


def test_sales_outputs_contract():
    frame = pd.DataFrame(
        {
            "fecha": pd.to_datetime(["2024-01-01", "2024-01-08"]),
            "anio": [2024, 2024],
            "mes": [1, 1],
            "cliente_analisis": ["cliente a", "cliente b"],
            "producto": ["carnation", "carnation"],
            "color": ["white", "red"],
            "producto_color": ["carnation / white", "carnation / red"],
            "tallos_demanda": [100, 200],
            "ventas_usd": [20.0, 50.0],
            "es_confirmado": [True, True],
            "es_solido": [True, True],
        }
    )
    outputs = build_general_sales_outputs(frame)
    assert outputs["ventas_anuales"].loc[0, "tallos"] == 300
    assert set(outputs) == {
        "ventas_anuales",
        "ventas_mensuales",
        "top_clientes",
        "top_producto_color",
        "mix_solido_no_solido",
    }


def test_weekly_solid_demand_contract():
    frame = pd.DataFrame(
        {
            "week_start": pd.to_datetime(["2024-01-01", "2024-01-01", "2024-01-08"]),
            "anio": [2024, 2024, 2024],
            "semana_iso": [1, 1, 2],
            "cliente_analisis": ["cliente a", "cliente b", "cliente a"],
            "producto_color": ["carnation / white", "carnation / red", "carnation / white"],
            "tallos_demanda": [100, 200, 150],
            "ventas_usd": [20.0, 50.0, 30.0],
            "es_confirmado": [True, True, True],
            "es_solido": [True, True, True],
        }
    )
    weekly = build_weekly_solid_demand(frame)
    assert weekly.shape[0] == 2
    assert weekly["tallos"].sum() == 450
