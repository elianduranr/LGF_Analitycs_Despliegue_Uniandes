from __future__ import annotations

from functools import lru_cache

from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, Field

from lgf_despliegue.config import load_config
from lgf_despliegue.data import load_sales_source
from lgf_despliegue.inference import baseline_solid_forecast
from lgf_despliegue.sales import build_general_sales_outputs


class HealthResponse(BaseModel):
    status: str
    data_dir: str
    data_path: str | None
    mlflow_tracking_uri: str


class ForecastRequest(BaseModel):
    horizon_weeks: int = Field(default=8, ge=1, le=26)
    lookback_weeks: int = Field(default=8, ge=2, le=52)


@lru_cache(maxsize=1)
def get_config():
    return load_config()


app = FastAPI(
    title="LGF Proyecto Despliegue API",
    version="0.1.0",
    description="API para ventas generales y forecast SOLIDO del proyecto reducido LGF.",
)


@app.get("/", include_in_schema=False)
def root() -> dict[str, str]:
    return {"service": "LGF Proyecto Despliegue API", "docs": "/docs"}


@app.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    config = get_config()
    return HealthResponse(
        status="ok",
        data_dir=str(config.data_dir),
        data_path=str(config.data_path) if config.data_path else None,
        mlflow_tracking_uri=config.mlflow_tracking_uri,
    )


@app.get("/ventas/resumen")
def ventas_resumen(top_n: int = Query(default=10, ge=1, le=50)) -> dict:
    config = get_config()
    try:
        sales = load_sales_source(data_path=config.data_path, data_dir=config.data_dir)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"No fue posible leer datos: {exc}") from exc

    outputs = build_general_sales_outputs(sales)
    annual = outputs["ventas_anuales"].to_dict(orient="records")
    clients = outputs["top_clientes"].head(top_n).to_dict(orient="records")
    product_color = outputs["top_producto_color"].head(top_n).to_dict(orient="records")
    solid_mix = outputs["mix_solido_no_solido"].to_dict(orient="records")
    return {
        "ventas_anuales": annual,
        "top_clientes": clients,
        "top_producto_color": product_color,
        "mix_solido_no_solido": solid_mix,
    }


@app.post("/forecast/solidos")
def forecast_solidos(request: ForecastRequest) -> dict:
    config = get_config()
    try:
        return baseline_solid_forecast(
            str(config.data_dir),
            data_path=str(config.data_path) if config.data_path else None,
            horizon_weeks=request.horizon_weeks,
            lookback_weeks=request.lookback_weeks,
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"No fue posible generar forecast: {exc}") from exc
