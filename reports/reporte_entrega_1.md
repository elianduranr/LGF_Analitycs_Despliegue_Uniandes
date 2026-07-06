# Reporte entrega 1

## Integrantes

- Elian Camilo Ricardo Duran Blanco - Codigo 202526064
- Julian Andres Osorio Vergara - Codigo 202524505

## Alcance

El analisis se rehizo con los archivos historicos locales ubicados en `../bases de datos historicas/`. La muestra de `datos/raw/` queda solo para DVC y pruebas rapidas; no reemplaza la base completa.

El EDA se orienta al problema de compras y planeacion: identificar clientes, productos, colores y combinaciones producto-color que explican la demanda SOLIDO, revisar concentracion y detectar variables utiles para una siguiente fase de modelado.

## Fuentes

| Archivo | Filas | Fechas | Tallos confirmados | Tallos SOLIDO | Ventas USD |
|---|---:|---|---:|---:|---:|
| ventas_facturadas_2021.csv | 216.006 | 2021-01-04 a 2021-12-31 | 79.976.591 | 31.965.577 | US$ 16.824.988 |
| ventas_facturadas_2022.csv | 262.883 | 2022-01-03 a 2022-12-30 | 86.036.681 | 29.127.427 | US$ 19.484.073 |
| ventas_facturadas_2023.csv | 328.260 | 2023-01-02 a 2023-12-30 | 97.823.717 | 34.320.204 | US$ 22.222.564 |
| ventas_facturadas_2024.csv | 343.009 | 2024-01-02 a 2024-12-28 | 99.853.090 | 37.449.249 | US$ 22.804.042 |
| ventas_facturadas_2025.csv | 369.997 | 2024-12-30 a 2025-12-27 | 104.906.659 | 41.271.775 | US$ 24.448.792 |
| ventas_facturadas_2026.csv | 165.299 | 2025-12-29 a 2026-05-16 | 52.815.519 | 19.186.389 | US$ 13.983.910 |

## Hallazgos del EDA

- La base cruda analizada contiene 1.685.454 lineas entre 2021-01-04 y 2026-05-16, con 521.412.257 tallos confirmados y US$ 119.768.370 en ventas.
- El subconjunto SOLIDO suma 193.320.621 tallos, equivalente al 37.1% del volumen confirmado. No conviene modelarlo como una sola serie, porque producto y color cambian bastante el comportamiento.
- El cliente consolidado con mayor volumen SOLIDO es Arabella Flowers BV con 39.675.743 tallos. Este peso se debe tener presente al validar resultados, porque puede mover el total.
- El color lider es white con 28.945.917 tallos. Color y producto-color deben revisarse aparte, no solo como totales generales.
- La combinacion producto-color mas relevante es carnation / white con 19.401.066 tallos. Por eso se dejan tablas especificas de producto-color.
- Los campos con nulos muy altos son codempaque y subcliente. Se dejan en el diccionario, pero no se recomiendan para el primer modelo.
- Se generaron salidas adicionales para cliente, pais, producto, color, producto-color, finca, flete, grado, empaque, cumplimiento pedido-confirmado, precio por tallo y variabilidad semanal.

## Estado del modelo

El modelo que aparece hoy en la herramienta se toma como modelo base. Sirve para revisar la vista de forecast y hacer una primera comparacion, pero todavia no se ha probado contra otros modelos ni se ha ajustado en serio.

La siguiente fase es probar modelos, comparar resultados y dejar guardada cada version. Las metricas actuales no cierran el proyecto; solo muestran desde donde empieza el trabajo de modelado.

## Tablas principales

### Clientes SOLIDO

| Cliente consolidado | Tallos SOLIDO |
|---|---:|
| Arabella Flowers BV | 39.675.743 |
| Bart Kwiaty Polska Sp. z o.o.Sp.K. | 14.434.975 |
| Pphu Arkadiusz Bylinski | 9.686.400 |
| Pinasco USA Bouquet LLC | 7.252.040 |
| Charme Flowers Inc c/o Kaufman Rossin | 6.914.856 |
| Handel Hurtowy Kwiatami Krystyna Pietruch | 6.367.546 |
| Continental Flowers | 6.106.340 |
| Flowerland Olga Galkowska | 5.866.665 |

### Colores SOLIDO

| Color | Tallos SOLIDO |
|---|---:|
| white | 28.945.917 |
| light pink | 24.874.944 |
| red | 23.446.437 |
| hot pink | 15.955.215 |
| green | 12.675.044 |
| orange | 12.551.879 |
| peach | 8.226.439 |
| lavender | 7.985.184 |

### Producto-color SOLIDO

| Producto-color | Tallos SOLIDO |
|---|---:|
| carnation / white | 19.401.066 |
| carnation / red | 16.389.041 |
| minicarnation / light pink | 12.504.548 |
| carnation / light pink | 11.395.960 |
| minicarnation / white | 8.212.929 |
| minicarnation / hot pink | 8.154.272 |
| carnation / orange | 7.683.727 |
| minicarnation / red | 6.692.650 |

## Figuras generadas

- `reports/figures/eda_plus_volumen_anual_solidos.png`
- `reports/figures/eda_plus_top_producto_color.png`
- `reports/figures/eda_plus_matriz_producto_color.png`
- `reports/figures/eda_plus_estacionalidad_colores.png`
- `reports/figures/eda_plus_pareto_clientes.png`
- `reports/figures/eda_plus_volumen_variabilidad_producto_color.png`
