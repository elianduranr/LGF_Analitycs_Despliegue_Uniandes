# Despliegue, contenedores y datos

## Objetivo para Entrega 2

La entrega pide modelos versionados en MLflow, una API para servir inferencias,
un tablero que consuma esa API y despliegue con Docker. Para que Elian y Julian
trabajen igual, el proyecto debe depender de variables de entorno y no de rutas
personales.

## Estructura propuesta

- `src/lgf_despliegue/`: paquete Python del proyecto.
- `app/main.py`: API FastAPI.
- `scripts/run_pipeline.py`: entrenamiento/evaluacion por consola.
- `scripts/train_pipeline.py`: entrada equivalente al `train_pipeline.py` del taller.
- `Dockerfile`: imagen de la API.
- `docker-compose.yml`: ejecucion local o en VM con volumen de datos.
- `tox.ini`: ambientes `train`, `test_package`, `test_app` y `run`, siguiendo el enfoque de talleres.
- `requirements.txt`: dependencias de ejecucion.
- `requirements-dev.txt`: pruebas, tox y build.

## Flujo tipo talleres

El flujo recomendado es el mismo patron trabajado en empaquetamiento y API:

```bash
tox run -e train
tox run -e test_package
tox run -e test_app
tox run -e run
```

Equivalencias:

| Taller | En este proyecto |
|---|---|
| `train_pipeline.py` | `scripts/train_pipeline.py` |
| `predict.py` | `src/lgf_despliegue/inference.py` |
| `test_package` | `tests/test_prediction.py` |
| `test_app` | `tests/test_api_contract.py` |
| `run` | `uvicorn app.main:app --host 0.0.0.0 --port 8001` |
| `VERSION` | `VERSION` |

Docker no reemplaza este flujo: lo envuelve para desplegar la API de la misma
forma en local y en la maquina virtual.

## Ejecucion local sin Docker

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
$env:PYTHONPATH="src"
$env:LGF_DATA_DIR="../bases de datos historicas"
.\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8001
```

API:

- `GET http://127.0.0.1:8001/health`
- `GET http://127.0.0.1:8001/ventas/resumen`
- `POST http://127.0.0.1:8001/forecast/solidos`
- Swagger: `http://127.0.0.1:8001/docs`

## Ejecucion local con Docker

Crear `.env` desde `.env.example` y ajustar `LGF_HOST_DATA_DIR`:

```powershell
Copy-Item .env.example .env
docker compose up --build
```

El contenedor monta la carpeta local de datos en `/data`. La aplicacion lee
`LGF_DATA_PATH=/data/historic_sales_acum.csv`, por eso el codigo no cambia entre
maquinas.

## Datos en la maquina virtual

Opcion recomendada para la entrega:

1. Crear carpeta persistente en la VM:

```bash
sudo mkdir -p /opt/lgf/data
sudo chown -R ubuntu:ubuntu /opt/lgf
```

2. Copiar el acumulado desde local a la VM:

```powershell
scp -i llave.pem "C:\ruta\a\historic_sales_acum.csv" ubuntu@IP:/opt/lgf/data/
```

3. En la VM, crear `.env`:

```bash
LGF_HOST_DATA_DIR=/opt/lgf/data
LGF_ACUM_FILE=historic_sales_acum.csv
LGF_DATA_DIR=/data
LGF_DATA_PATH=/data/historic_sales_acum.csv
LGF_OUTPUT_DIR=/app/outputs
MLFLOW_TRACKING_URI=file:/app/mlruns
```

4. Ejecutar:

```bash
docker compose up --build
```

5. Abrir puerto `8001` en el Security Group de EC2 y probar:

```text
http://IP_PUBLICA:8001/docs
```

## Alternativas de datos

- DVC remoto: conveniente si quieren versionar muestras o datasets medianos y
  ejecutar `dvc pull` en la VM.
- S3: mejor opcion si la base completa crece o no quieren copiar archivos por
  SCP. La VM obtiene permisos con IAM Role y descarga a `/opt/lgf/data`.
- Volumen EBS: buena opcion si la VM se recrea, porque los datos quedan en un
  disco persistente que se vuelve a montar.

Para esta entrega, `SCP + /opt/lgf/data + docker volume mount` es lo mas simple
y suficiente.
