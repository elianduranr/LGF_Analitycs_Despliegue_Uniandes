# Proyecto despliegue LGF

Proyecto reducido e independiente para la asignatura de despliegue. Usa como
contexto el proyecto operativo grande de LGF, pero aqui el alcance queda
cerrado a dos frentes:

- Ventas generales: lectura de negocio sobre volumen, ventas, clientes,
  productos, colores y mezcla SOLIDO/no SOLIDO.
- Forecast SOLIDO: comparacion de modelos de demanda semanal con registro de
  experimentos en MLflow.

## Integrantes

- Elian Camilo Ricardo Duran Blanco - Codigo 202526064
- Julian Andres Osorio Vergara - Codigo 202524505

## Entregables actuales

- `notebooks/eda_pronostico_demanda_solidos.ipynb`: EDA orientado a demanda y forecast, ejecutado sobre base cruda completa.
- `datos/README_DICCIONARIO_DATOS.md`: diccionario de datos.
- `datos/raw/ventas_facturadas_muestra_2021_2026.csv.dvc`: versionamiento DVC de la muestra.
- `supports/prototipo/`: pantallazos del prototipo existente.
- `supports/soporte_repositorios.md`: soporte Git y DVC.
- `reports/reporte_trabajo_equipo.md`: responsabilidades del equipo.
- `src/lgf_despliegue/`: primera version del codigo reusable.
- `scripts/run_pipeline.py`: ejecutor de ventas generales y forecast con MLflow.
- `app/main.py`: API FastAPI para salud, ventas generales e inferencia baseline.
- `app/dash_ventas.py`: tablero descriptivo de ventas generales.
- `Dockerfile` y `docker-compose.yml`: ejecucion contenedorizada.
- `tox.ini`: ambientes `train`, `test_package`, `test_app` y `run` como en los talleres.
- `docs/FLUJO_TRABAJO.md`: ramas, roles y prompts separados para Elian/Julian.
- `docs/DESPLIEGUE_DATOS_DOCKER.md`: guia de Docker, API y datos en VM.

## Ejecutar

Crear entorno e instalar dependencias:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

Ejecutar solo ventas generales:

```powershell
.\.venv\Scripts\python.exe scripts\run_pipeline.py --skip-forecast
```

Con archivo acumulado unico:

```powershell
.\.venv\Scripts\python.exe scripts\run_pipeline.py --data-path "C:\ruta\a\historic_sales_acum.csv" --skip-forecast
```

Ejecutar ventas generales y comparacion de modelos con MLflow:

```powershell
.\.venv\Scripts\python.exe scripts\run_pipeline.py
```

Las salidas quedan en `outputs/` y los experimentos de MLflow en `mlruns/`.
Ambas carpetas estan ignoradas por Git.

## API y Docker

Flujo tipo talleres:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.\.venv\Scripts\tox.exe run -e test_package
.\.venv\Scripts\tox.exe run -e test_app
.\.venv\Scripts\tox.exe run -e run
```

Ejecucion local de la API:

```powershell
$env:PYTHONPATH="src"
$env:LGF_DATA_DIR="../bases de datos historicas"
.\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8001
```

Ejecucion con Docker:

```powershell
Copy-Item .env.example .env
docker compose up --build
```

Rutas principales:

- `GET /health`
- `GET /ventas/resumen`
- `POST /forecast/solidos`
- `/docs` para Swagger.

La fuente recomendada es un unico acumulado `historic_sales_acum.csv`. Se
configura con `LGF_DATA_PATH`; en Docker Compose se define la carpeta con
`LGF_HOST_DATA_DIR` y el nombre del archivo con `LGF_ACUM_FILE`.

## Dashboard Ventas Generales

```powershell
$env:PYTHONPATH="src"
.\.venv\Scripts\python.exe app\dash_ventas.py --data-path "C:\ruta\a\historic_sales_acum.csv" --host 127.0.0.1 --port 8051
```

En Git Bash:

```bash
bash scripts/run_dash_ventas.sh
```

Por defecto usa el puerto `8052`. Para cambiar datos o puerto:

```bash
export LGF_DATA_PATH="/c/ruta/a/historic_sales_acum.csv"
export LGF_DASH_PORT=8053
bash scripts/run_dash_ventas.sh
```

Luego abrir:

```text
http://127.0.0.1:8051
```

## Dashboard Forecast SOLIDO

Primero ejecutar entrenamiento/evaluacion para generar `outputs/forecast/` y
registrar experimentos en MLflow:

```powershell
$env:PYTHONPATH="src"
$env:LGF_DATA_PATH="C:\ruta\a\historic_sales_acum.csv"
.\.venv\Scripts\python.exe scripts\train_pipeline.py
```

Luego abrir el tablero de forecast:

```powershell
$env:LGF_DATA_PATH="C:\ruta\a\historic_sales_acum.csv"
.\scripts\run_dash_forecast.ps1
```

Por defecto usa `http://127.0.0.1:8053`. El tablero lee las metricas, backtesting
y predicciones futuras desde `outputs/forecast/`; si aun no existen, muestra la
serie semanal SOLIDO para orientar el entrenamiento.

## Versionamiento de modelos

El modulo de forecast registra en MLflow:

- Modelo probado.
- Parametros principales.
- Backtesting por ventanas temporales.
- MAE, RMSE y WAPE por fold y promedio.
- Artefacto del modelo cuando aplica.
- Archivos CSV de evaluacion en `outputs/forecast/`.

El modelo seleccionado se marca en `outputs/forecast/evaluacion_modelos.csv` con
`modelo_seleccionado = True`. Ese criterio debe explicarse en el informe final:
no basta con decir cual gano, hay que justificarlo por error, estabilidad y
lectura de negocio.

## Nota de datos

El notebook usa las bases crudas locales 2021-2026 ubicadas en
`../bases de datos historicas/` para el analisis completo:

- `ventas_facturadas_2021.csv`
- `ventas_facturadas_2022.csv`
- `ventas_facturadas_2023.csv`
- `ventas_facturadas_2024.csv`
- `ventas_facturadas_2025.csv`
- `ventas_facturadas_2026.csv`

Estas bases completas estan ignoradas por Git. La muestra
`datos/raw/ventas_facturadas_muestra_2021_2026.csv` se maneja con DVC para poder
compartir una parte de los datos sin subir toda la base cruda.

## Ramas de trabajo

La guia completa esta en `docs/FLUJO_TRABAJO.md`. Resumen:

- `main`: rama estable.
- `feature/ventas-generales-elian`: negocio, ventas, EDA, diccionario e informe.
- `feature/mlflow-forecast-julian`: modelos, metricas, MLflow y seleccion.
- `feature/documentacion-entrega`: cierre de reporte y evidencias.

