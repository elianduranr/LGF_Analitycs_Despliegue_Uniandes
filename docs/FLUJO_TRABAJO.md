# Flujo de trabajo Elian / Julian

## Alcance de esta version

Este repositorio reducido no intenta reemplazar `lgf_operativo_project`. Toma ese
proyecto como referencia, pero aqui solo se trabajan:

- Ventas generales: volumen, ventas USD, clientes, productos y mezcla SOLIDO.
- Forecast SOLIDO: demanda semanal confirmada y comparacion de modelos con MLflow.

Quedan fuera de alcance por ahora: inventario, comprador, fletes, Cliente 360,
Surtidos/Rainbow/Combo y despliegue completo del dashboard operativo.

## Ramas sugeridas

La rama estable debe ser `main`.

| Rama | Responsable | Uso |
|---|---|---|
| `feature/ventas-generales-elian` | Elian | EDA de negocio, tablas de ventas, diccionario, reporte y visualizaciones. |
| `feature/mlflow-forecast-julian` | Julian | Backtesting, modelos, MLflow, seleccion del modelo y metricas. |
| `feature/documentacion-entrega` | Ambos | Informe, evidencias, instrucciones de ejecucion y cierre de rubrica. |
| `fix/pre-entrega` | Ambos | Correcciones pequenas antes de integrar. |

## Reglas de integracion

1. Crear ramas siempre desde `main`.
2. Hacer commits pequenos y descriptivos.
3. No subir bases historicas completas a Git. Usar DVC para muestras o dejar rutas locales documentadas.
4. Julian registra cada experimento de forecast en MLflow y deja en el reporte por que se escoge un modelo.
5. Elian valida si las salidas tienen sentido para ventas, clientes, producto, color y temporada.
6. Antes de unir a `main`, ejecutar el pipeline al menos con `--skip-forecast`; para cierre de modelo, ejecutar completo.

## Distribucion de responsabilidades

### Elian

Responsable del contexto y la validacion de negocio, las salidas de ventas
generales, los tableros, DVC, el despliegue y la organizacion de evidencias.

### Julian

Responsable del forecast SOLIDO, el backtesting, la comparacion de modelos, las
metricas y el seguimiento de experimentos en MLflow.

### Integracion y revision

Las ramas de trabajo se revisan antes de integrarse en `main`. La revision final
incluye pruebas del paquete y la API, validacion de tableros, revision de
metricas y comprobacion de los soportes de la entrega.
