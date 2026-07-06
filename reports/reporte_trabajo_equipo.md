# Plan de trabajo y responsabilidades

## Integrantes

- Elian Camilo Ricardo Duran Blanco - Codigo 202526064
- Julian Andres Osorio Vergara - Codigo 202524505

## Roles

| Frente | Responsable principal | Rol dentro del proyecto |
|---|---|---|
| Contexto de la compania y validacion de negocio | Elian Camilo Ricardo Duran Blanco | Tiene el contexto interno de La Gaitana. Revisa si los resultados hacen sentido para ventas, clientes, producto, color y planeacion. |
| Despliegue, herramienta y entrega | Elian Camilo Ricardo Duran Blanco | Se encarga de ordenar el proyecto, la documentacion, los pantallazos, Git, DVC y la entrega final. |
| Modelos y validacion tecnica | Julian Andres Osorio Vergara | Se encarga de la parte mas tecnica: modelos, pruebas, metricas, tuning y comparacion de alternativas. |
| Revision cruzada | Ambos | Elian revisa negocio y despliegue; Julian revisa modelos y resultados tecnicos. |

## Alcance por fases

| Fase | Objetivo | Responsable lider | Resultado esperado |
|---|---|---|---|
| 1. Datos y EDA | Revisar las bases historicas, columnas, nulos, volumen y segmentos importantes. | Elian | Diccionario completo, EDA y hallazgos principales en el informe. |
| 2. Modelo base | Dejar claro que el modelo actual es solo una referencia inicial. | Julian | Baseline con metrica, horizonte y limites conocidos. |
| 3. Nuevos modelos | Probar opciones mejores y compararlas con el baseline. | Julian | Tabla de modelos, parametros usados y resultados. |
| 4. Validacion de negocio | Revisar si el resultado sirve para decisiones reales de cliente, producto, color y mercado. | Elian | Comentarios de negocio y ajustes necesarios. |
| 5. Entrega y despliegue | Ordenar archivos, datos, pantallazos, notebook, Word y dependencias. | Elian | Proyecto listo para revisar y ejecutar. |

## Propuesta de ramas Git

La rama estable de entrega puede mantenerse como `proyecto_despliegue_lgf`. Para no pisarse cambios, conviene trabajar asi:

| Rama sugerida | Responsable | Uso |
|---|---|---|
| `feature/eda-negocio-elian` | Elian | EDA, diccionario, lectura de negocio y ajustes del informe. |
| `feature/despliegue-elian` | Elian | Estructura, requirements, DVC, pantallazos, Word y soporte de ejecucion. |
| `feature/modelos-julian` | Julian | Modelos, tuning, backtesting, comparacion y metricas. |
| `feature/validacion-modelos` | Ambos | Revision final de resultados: Julian desde tecnica y Elian desde negocio. |
| `fix/documentacion-entrega` | Ambos | Correcciones pequenas antes de entregar. |

## Flujo recomendado

1. Crear rama desde `proyecto_despliegue_lgf`.
2. Hacer commits pequenos con nombres claros.
3. No subir bases historicas completas a Git; deben quedar locales e ignoradas.
4. Usar DVC para las muestras que si se deban compartir.
5. Antes de unir cambios, revisar que el notebook, el Word y las tablas sigan abriendo bien.
6. Integrar con revision: Julian revisa lo de modelos; Elian revisa negocio, despliegue y entrega.

## Criterio de cierre

El proyecto no debe mostrarse como si el modelo ya estuviera terminado. Hoy hay una herramienta funcional y un modelo base. Falta comparar modelos, guardar resultados y validar con negocio cual queda mejor.
