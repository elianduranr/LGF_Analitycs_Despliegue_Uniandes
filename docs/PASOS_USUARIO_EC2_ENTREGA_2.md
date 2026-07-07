# Pasos que faltan para cerrar la Entrega 2

Este archivo resume solo las acciones que requieren tu intervencion manual: AWS, navegador, pantallazos y reporte final.

## 1. Evidencia obligatoria en EC2 con MLflow

El enunciado pide pantallazos de experimentos registrados en MLflow en una maquina AWS EC2. Debe verse el usuario/IP de la maquina EC2 y la IP en MLflow.

### Pantallazos que debes tomar

1. Consola de AWS EC2 con la instancia encendida, usuario de AWS Academy visible e IP publica visible.
2. Terminal conectado por SSH a la instancia.
3. Ambiente virtual activo en EC2.
4. Servidor MLflow corriendo en EC2.
5. Navegador con MLflow abierto usando `http://IP_PUBLICA:8050`.
6. Experimento `lgf_forecast_solidos` con corridas visibles.
7. Comparacion de modelos en MLflow mostrando metricas como `mae`, `rmse` y `wape`.

No termines la instancia al final. El enunciado pide mantenerla detenida, no terminada.

## 2. Comandos recomendados en EC2

En Ubuntu 24.04:

```bash
sudo apt update
sudo apt install -y python3-pip python3.12-venv git
git clone https://github.com/elianduranr/LGF_Analitycs_Despliegue_Uniandes.git
cd LGF_Analitycs_Despliegue_Uniandes
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements-dev.txt
```

Si vas a correr con el acumulado real, copia `historic_sales_acum.csv` a una carpeta de la instancia, por ejemplo:

```bash
mkdir -p data_ec2
```

Luego ejecuta el entrenamiento:

```bash
export PYTHONPATH=src
export LGF_DATA_PATH=/home/ubuntu/LGF_Analitycs_Despliegue_Uniandes/data_ec2/historic_sales_acum.csv
export LGF_OUTPUT_DIR=outputs
export MLFLOW_TRACKING_URI=mlruns
python scripts/train_pipeline.py
```

Levanta MLflow:

```bash
mlflow server -h 0.0.0.0 -p 8050 --backend-store-uri ./mlruns --default-artifact-root ./mlruns
```

En AWS Security Group abre el puerto `8050` para poder entrar desde el navegador:

```text
http://IP_PUBLICA:8050
```

## 3. Evidencia del tablero

En local o EC2, despues de generar `outputs/forecast/`, abre el dashboard forecast:

```powershell
$env:PYTHONPATH="src"
$env:LGF_DATA_PATH="C:\Proyectos_gaitana\Proyecto_despliegue\bases de datos historicas\historic_sales_acum.csv"
$env:LGF_OUTPUT_DIR="outputs"
.\scripts\run_dash_forecast.ps1
```

Pantallazos sugeridos:

- Tarjetas de metricas: modelo seleccionado, WAPE, RMSE, horizonte.
- Grafica de comparacion de modelos.
- Grafica de backtesting real vs prediccion.
- Forecast futuro SOLIDO.

## 4. Evidencia de API

Localmente ya se probo `/health`, pero para entrega conviene un pantallazo de Swagger:

```powershell
$env:PYTHONPATH="src"
$env:LGF_DATA_PATH="C:\Proyectos_gaitana\Proyecto_despliegue\bases de datos historicas\historic_sales_acum.csv"
.\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8001
```

Abrir:

```text
http://127.0.0.1:8001/docs
```

Pantallazos sugeridos:

- `/health` ejecutado.
- `/forecast/solidos` ejecutado con respuesta satisfactoria.

## 5. Evidencia Docker

En esta maquina no se encontro el comando `docker`. Esta prueba debe hacerse en una maquina con Docker Desktop o en EC2 si Docker esta instalado.

```powershell
docker compose up --build
```

Abrir:

```text
http://127.0.0.1:8001/docs
```

## 6. Reporte final

El reporte debe tener maximo 10 paginas. Orden recomendado:

1. Resumen del problema, contexto, pregunta de negocio, alcance y datos.
2. Cambios frente a entrega 1.
3. Modelos desarrollados: baselines, Ridge, Random Forest, HGB.
4. Evaluacion: backtesting temporal, MAE, RMSE, WAPE.
5. Seleccion: `random_forest_semanal` por menor WAPE promedio.
6. Observaciones de negocio: demanda SOLIDO semanal, estacionalidad, estabilidad del error y uso para planeacion.
7. Tablero: ventas generales, comparacion de modelos, backtesting y forecast futuro.
8. Evidencias: GitHub, MLflow EC2, API, tablero, Docker.
9. Trabajo en equipo: Elian y Julian con tareas y commits.

## 7. Estado del repo

El repo remoto ya quedo actualizado:

- `origin/main`
- `origin/proyecto_despliegue_lgf`

Ultimo commit integrado:

```text
639f65e Validar integracion entrega 2
```
