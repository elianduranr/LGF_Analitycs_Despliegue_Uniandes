# Estado de ramas y pendientes - Entrega 2

Fecha de revision: 2026-07-07

## Ramas que intervienen

| Rama | Responsable | Estado | Aporte principal |
|---|---|---|---|
| `main` | Equipo | Rama estable de integracion | Contiene el proyecto reducido funcional: paquete Python, API FastAPI, tableros Dash, Docker, DVC, pruebas y documentacion base. |
| `feature/ventas-generales-elian` | Elian | Integrada previamente en `main` | Visualizador y salidas descriptivas de ventas generales: ventas anuales/mensuales, clientes, producto-color y mezcla SOLIDO/no SOLIDO. |
| `feature/documentacion-entrega` | Equipo | Integrada previamente en `main` | README, flujo de trabajo, documentos del proyecto, rubrica, enunciados y soportes. |
| `feature/mlflow-forecast-julian` | Julian | Integrada en `main` el 2026-07-07 | Forecast SOLIDO con backtesting, comparacion de modelos, metricas, registro MLflow y tablero de forecast. |
| `origin/proyecto_despliegue_lgf` | Equipo | Rama remota historica/base | Apunta al mismo avance remoto que `origin/main` antes de integrar el ultimo forecast. |

## Merge realizado

Se actualizo el repositorio interno `proyecto_despliegue` con:

```powershell
git fetch origin --prune
git merge --no-ff origin/feature/mlflow-forecast-julian -m "Integrar forecast MLflow"
```

El merge agrego o actualizo:

- `app/dash_forecast.py`
- `scripts/run_dash_forecast.ps1`
- `src/lgf_despliegue/forecast.py`
- `src/lgf_despliegue/inference.py`
- `app/dash_ventas.py`
- `README.md`

## Validacion local

Validado con entorno virtual Python 3.12:

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```

Resultado: 3 pruebas pasaron.

Tambien se valido:

- Importacion de dependencias clave: pandas, scikit-learn, FastAPI, MLflow y Dash.
- Importacion de `lgf_despliegue.forecast` y `app.main`.
- Importacion y construccion de dashboards `LGF Forecast SOLIDO` y `LGF Ventas Generales`.
- Compilacion de `app`, `src` y `scripts`.
- Construccion del paquete con `python -m build`.
- Validacion tox del paquete: `tox run -e test_package` paso con 2 pruebas.
- Validacion tox de la API: `tox run -e test_app` paso correctamente.
- Prueba local de API con Uvicorn: `GET http://127.0.0.1:8001/health` respondio `{"status":"ok", ...}`.
- Validacion Docker local: pendiente porque el comando `docker` no esta instalado o no esta disponible en el PATH de esta maquina.

Entrenamiento real ejecutado con el acumulado historico:

```powershell
$env:PYTHONPATH="src"
$env:LGF_DATA_PATH="C:\Proyectos_gaitana\Proyecto_despliegue\bases de datos historicas\historic_sales_acum.csv"
$env:LGF_OUTPUT_DIR="outputs"
$env:MLFLOW_TRACKING_URI="mlruns"
.\.venv\Scripts\python.exe scripts\train_pipeline.py
```

Resultado: entrenamiento/evaluacion finalizado correctamente. Se generaron salidas en `outputs/forecast/` y corridas locales en `mlruns/`.

Resumen del modelo seleccionado:

| Modelo seleccionado | MAE promedio | RMSE promedio | WAPE promedio | Folds |
|---|---:|---:|---:|---:|
| `random_forest_semanal` | 114164.42 | 137962.90 | 0.12999 | 4 |

Notas tecnicas:

- Se quito `jupyter` de las dependencias obligatorias de despliegue para evitar fallas de instalacion por rutas largas en Windows. Los notebooks siguen en el repositorio, pero Jupyter no debe bloquear API, Docker, pruebas ni tablero.
- Se agrego configuracion de `pytest` para que `python -m pytest` encuentre automaticamente el paquete en `src/`.
- Se ignoran artefactos generados: `build/`, `dist/` y `*.egg-info/`.
- Se corrigio la deteccion de SOLIDO para aceptar `solido`, `sólido` y `solid`; el acumulado historico usa valores como `sólido por variedad`.
- Se corrigio el tracking URI local de MLflow en Windows para usar URI `file:///...` cuando se configura una ruta local como `mlruns`.

## Lo que ya cubre el proyecto frente a la entrega 2

- Modelos desarrollados: el modulo de forecast compara baseline, modelo lineal y modelos de arboles para demanda semanal SOLIDO.
- Evaluacion: backtesting temporal, MAE, RMSE y WAPE por fold y promedio.
- MLflow: registro de corridas, parametros, metricas, tags y artefactos CSV.
- Tablero: ventas generales y forecast SOLIDO con resultados de evaluacion/prediccion.
- API: FastAPI con `/health`, `/ventas/resumen` y `/forecast/solidos`.
- Empaquetamiento: `pyproject.toml`, `tox.ini`, pruebas y build de paquete.
- Docker: `Dockerfile` y `docker-compose.yml`.
- DVC: muestra versionada y documentacion de datos.
- Trabajo en equipo: `reports/reporte_trabajo_equipo.md` y ramas separadas por responsable.

## Pendientes para entregar con buena probabilidad de nota

Prioridad alta:

1. Levantar MLflow en EC2 y correr el entrenamiento alla. El enunciado pide pantallazos donde se vea usuario/IP de EC2 y la IP en MLflow. Esta evidencia no se puede completar solo localmente.

2. Tomar pantallazos de MLflow en EC2:

   - Consola AWS con instancia activa, usuario e IP visible.
   - Conexion SSH a la instancia.
   - Servidor MLflow corriendo.
   - Interfaz MLflow con experimentos del proyecto.
   - Comparacion de modelos con metricas.

3. Probar tablero forecast con salidas reales:

   ```powershell
   $env:LGF_DATA_PATH="C:\ruta\a\historic_sales_acum.csv"
   .\scripts\run_dash_forecast.ps1
   ```

   Tomar pantallazos del tablero mostrando predicciones del modelo.

4. Completar el reporte de maximo 10 paginas de entrega 2:

   - Resumen del problema, pregunta de negocio, alcance y datos.
   - Cambios frente a entrega 1.
   - Modelos desarrollados y evaluacion.
   - Observaciones y conclusiones de modelos.
   - Descripcion del tablero y funcionalidad.

Prioridad media:

5. Actualizar conclusiones de negocio, porque la rubrica de entrega 1 pidio mas profundidad explicativa sobre el negocio de flores.

6. Reforzar alcance del proyecto en el reporte: dejar claro que el alcance actual es ventas generales y forecast de demanda SOLIDO, no toda la operacion LGF.

7. Revisar el diccionario de datos en el reporte final y mencionar variables que el profesor marco como importantes: capuchon, comida, receta, tipo de pedido, moneda y valor de venta.

8. Guardar evidencia de:

   ```powershell
   .\.venv\Scripts\tox.exe run -e test_package
   .\.venv\Scripts\tox.exe run -e test_app
   .\.venv\Scripts\tox.exe run -e run
   ```

9. Probar Docker en una maquina con Docker disponible:

   ```powershell
   docker compose up --build
   ```

   Tomar pantallazo de API en `/docs` o `/health`.

Prioridad baja:

10. Subir a GitHub el `main` integrado cuando se confirme que la evidencia esta lista:

   ```powershell
   git push origin main
   ```

11. Verificar en GitHub que se vean commits de Elian y Julian en ramas/PRs o historial.

12. Mantener EC2 con MLflow detenida, no terminada, como pide el enunciado.
