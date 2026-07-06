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
- `docs/FLUJO_TRABAJO.md`: ramas, roles y prompts separados para Elian/Julian.

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

Ejecutar ventas generales y comparacion de modelos con MLflow:

```powershell
.\.venv\Scripts\python.exe scripts\run_pipeline.py
```

Las salidas quedan en `outputs/` y los experimentos de MLflow en `mlruns/`.
Ambas carpetas estan ignoradas por Git.

## Versionamiento de modelos

El modulo de forecast registra en MLflow:

- Modelo probado.
- Parametros principales.
- MAE, RMSE y WAPE.
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

