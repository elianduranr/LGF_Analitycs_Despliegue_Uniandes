# Diccionario de datos

Base versionada para la entrega:

- `raw/ventas_facturadas_muestra_2021_2026.csv`

La muestra proviene de las bases historicas locales ubicadas en
`../../bases de datos historicas/`, desde `ventas_facturadas_2021.csv` hasta
`ventas_facturadas_2026.csv`. El EDA completo se calcula sobre la base cruda;
la muestra se mantiene con DVC para reproducibilidad liviana.

## Lectura analitica

- Variable objetivo: `tallos_confirmados`.
- Foco de pronostico: lineas SOLIDO identificadas en `tipo_empaque`, `empaque` y `tipo_orden_empaque`.
- Segmentacion principal: tiempo, cliente, pais, producto, color y producto-color.
- Control financiero: `ventas_usd`, `VALORTOTAL`, `NomMoneda`, `USD/EUR` y `USD/GBP`.

## Campos

| Campo | Dominio | Tipo | Uso | Nulos | Ejemplos |
|---|---|---|---|---:|---|
| NomCompania | dimension | categorico/texto | Compania que factura o registra la venta. | 0.0% | Arabella Flowers B.V.; Charme Flowers Inc c/o Kaufman Rossin; Global Goods N°1 |
| semana | tiempo | numerico | Semana calendario reportada en la fuente. | 0.0% | 1; 2; 3 |
| DIA | tiempo | numerico | Dia del mes asociado a la fecha de venta. | 0.0% | 4; 6; 7 |
| fecha | tiempo | fecha | Fecha de la linea facturada; base para series de demanda. | 0.0% | 2021-01-04; 2021-01-06; 2021-01-07 |
| cod_cliente | cliente | numerico | Codigo operativo del cliente o sucursal. | 0.0% | 730; 732; 791 |
| cliente | cliente | categorico/texto | Nombre del cliente o sucursal. | 0.0% | IFT Naaldwijk BV; A. Noort Bloemenexport BV; Viaflor BV |
| grupo | cliente | categorico/texto | Agrupacion comercial del cliente cuando existe. | 15.1% | Ninguno; Kendal Floral Supply,Co LLC; Ahold Financial |
| subcliente | cliente | categorico/texto | Subcliente o detalle comercial secundario. | 100.0% |  |
| tipo_venta | comercial | categorico/texto | Clasificacion tributaria/comercial de la venta. | 0.0% | exportación exentos dólares F; exportación exentos euros F; exportación exentos libras F |
| tipo_orden_empaque | operacion | categorico/texto | Tipo operativo de orden o empaque; identifica solidos, surtidos y adicionales. | 7.3% | Adicional; Muestra; Fija |
| pedido | operacion | numerico | Numero de pedido. | 0.0% | 75706; 75705; 75707 |
| invoice | comercial | numerico | Numero de factura. | 0.0% | 00001157; 00001158; 00001156 |
| tipo_empaque | operacion | categorico/texto | Tipo de empaque reportado por la fuente. | 0.0% | Combo; Sólido Por Variedad; Rainbow |
| empaque | operacion | categorico/texto | Descripcion del empaque o receta. | 0.0% | Combo Carn / Mini; Carnation sel bicolor burgundy Fredy; Carnation sel bicolor purple Kino |
| grado | producto | categorico/texto | Calibre o grado del tallo. | 0.0% | fcy; sel; 60 cm |
| caja_id | operacion | numerico | Identificador de caja cuando esta disponible. | 43.2% | RO; KX11; CUSTOMER CZ703 |
| color | producto | categorico/texto | Color comercial de la flor. | 0.0% | white; bicolor burgundy; bicolor purple |
| variedad | producto | categorico/texto | Variedad especifica dentro de producto/color. | 0.0% | moonlight; fredy; kino |
| PIEZASEQUVALENTES | operacion | numerico | Piezas equivalentes de la linea. | 0.0% | 0.5; 3.0; 1.0 |
| FULLESEQUIVALENTES | operacion | numerico | Fulles equivalentes de la linea. | 0.0% | 0.125; 0.75; 0.25 |
| TYPEOFPACKAGE | operacion | categorico/texto | Tipo de paquete original. | 0.0% | Box |
| tipo_caja | operacion | categorico/texto | Tipo de caja comercial. | 0.0% | QB; HB; FB |
| TIPOCORTE | operacion | categorico/texto | Tipo de corte reportado. | 3.9% | Corte 3; Corte 2; CORTE 01 |
| VALORUNITARIO | financiero | numerico | Precio unitario en moneda de registro. | 0.0% | 0.001; 0.235; 0.245 |
| MARCACAJA | operacion | categorico/texto | Marca de caja. | 0.0% | QB Gaitana (071 BGN); Arabella; Folder 8B Chicu |
| producto | producto | categorico/texto | Producto o flor comercial. | 0.0% | carnation; minicarnation; solomio |
| AGENCIACARGA | logistica | categorico/texto | Agencia de carga/logistica. | 0.0% | Kuehne Nagel SAS; K&M Handling Colombia SAS; Interandina |
| pais | mercado | categorico/texto | Pais destino. | 0.0% | The Netherlands; Czech Republic; Germany |
| ciudad | mercado | categorico/texto | Ciudad destino. | 0.0% | Vlaardingen; Rijnsburg; Prague |
| RXCAJA | operacion | numerico | Ramos por caja. | 0.0% | 5; 10; 20 |
| fulles | operacion | numerico | Fulles asociados a la caja. | 0.0% | 0.25; 0.75; 0.5 |
| equivalencia | operacion | numerico | Factor de equivalencia operativo. | 0.0% | 4.0; 2.0; 1.0 |
| flor_emp | operacion | numerico | Flores por empaque. | 0.0% | 100; 600; 200 |
| tallos_x_ramo | operacion | numerico | Tallos por ramo. | 0.0% | 20; 10; 2 |
| ramos_pedidos | demanda | numerico | Ramos solicitados. | 0.0% | 5; 30; 10 |
| RXCAJADETALLE | operacion | numerico | Detalle de ramos por caja. | 0.0% | 20; 10; 2 |
| ramos_confirmados | demanda | numerico | Ramos confirmados. | 0.0% | 5; 30; 10 |
| po | comercial | categorico/texto | Orden de compra del cliente cuando existe. | 51.8% | EST; STANDING; 345818 |
| id_caja | operacion | numerico | Identificador alterno de caja. | 43.2% | RO; KX11; CUSTOMER CZ703 |
| Version_1 | operacion | numerico | Version de estructura/empaque. | 0.0% | 0; 1; 3 |
| OBSERVACIONESEMPAQUE | operacion | categorico/texto | Observaciones del empaque. | 79.7% | CUSTOMER CZ703; cal air jan-08; Prime truck friday jan-08 |
| tipo_precio | financiero | categorico/texto | Base de precio usada en la linea. | 0.0% | Tallos; Ramos |
| TXRAMO | operacion | numerico | Tallos por ramo reportado en texto/fuente. | 0.0% | 20; 10; 2 |
| comida | operacion | categorico/texto | Alimento o componente adicional. | 71.1% | Food - floralife Express 10 g; Food - chrysal Clear U. 5 g; Food - chrysal Albertson 5 g |
| capuchon | operacion | categorico/texto | Capuchon o material de empaque. | 12.9% | SL-bio micro Gaitana cla (30*12*60); SL-bio micro Gaitana mini (25*8*45); SL -Bio micro Arabella clavel |
| mes | tiempo | numerico | Mes calendario. | 0.0% | 1; 2; 3 |
| tipo_orden | operacion | categorico/texto | Estado operacional general de la orden. | 0.0% | Pedido; Fija; Regular |
| estado | operacion | categorico/texto | Estado de confirmacion/facturacion. | 0.0% | Confirmado |
| vendedor | comercial | categorico/texto | Responsable comercial. | 0.0% | Frans Buzek; Ninguno; Stephen Gaunt |
| receta | operacion | categorico/texto | Indicador o codigo de receta. | 0.0% | 0 |
| bulkbouquet | operacion | categorico/texto | Clasificacion bulk/bouquet. | 0.0% | BULK |
| codempaque | operacion | numerico | Codigo de empaque. | 100.0% |  |
| pull_date | auditoria | fecha | Fecha de extraccion de la fuente. | 75.6% | 08/13/2020; 01/20/2021; 01/24/2021 |
| GuiaMaster | logistica | categorico/texto | Guia master/logistica. | 0.3% | 074-41992731; 074-41993151; 074-41993280 |
| serial | auditoria | numerico | Serial de la linea. | 0.0% | 268842; 268839; 268821 |
| abrev_finca | origen | categorico/texto | Abreviatura de finca. | 0.0% | GF; AR |
| finca | origen | categorico/texto | Finca de origen. | 0.0% | GAITANA; Arabella; Latin |
| NomMoneda | financiero | categorico/texto | Moneda original. | 0.0% | DOLARES |
| cod_cliente_consolidado | cliente | numerico | Codigo de cliente consolidado. | 0.0% | 794; 1999; 30542 |
| cliente_consolidado | cliente | categorico/texto | Cliente consolidado. | 0.0% | Arabella Flowers BV; Charme Flowers Inc c/o Kaufman Rossin; Pinasco y/o Global Goods No 1 Ltd £ |
| Var Code | producto | categorico/texto | Codigo de variedad. | 7.7% | moonlight; fredy; kino |
| AÑO | tiempo | numerico | Ano calendario. | 0.0% | 2021; 2022; 2023 |
| AÑO_SEMANA | tiempo | categorico/texto | Llave ano-semana ISO. | 0.0% | 2021-W01; 2021-W02; 2021-W03 |
| USD/EUR | financiero | numerico | Tasa usada para convertir EUR a USD. | 0.0% | 0.8165865050914168; 0.8114116940653349; 0.815075639019301 |
| USD/GBP | financiero | numerico | Tasa usada para convertir GBP a USD. | 0.0% | 0.7371152258521052; 0.7350184857149157; 0.7374033079912397 |
| Tipo_Flete | logistica | categorico/texto | Condicion de flete. | 0.5% | DEL; FOB; CIF |
| piezas | operacion | numerico | Piezas de la linea. | 0.0% | 1; 3; 2 |
| tallos_total | demanda | numerico | Tallos totales calculados. | 0.0% | 100; 600; 200 |
| tallos_pedidos | demanda | numerico | Tallos solicitados. | 0.0% | 100; 600; 200 |
| tallos_confirmados | demanda | numerico | Tallos confirmados/facturados; variable objetivo principal. | 0.0% | 100; 600; 200 |
| VALORTOTAL | financiero | numerico | Valor total en moneda de origen o registro. | 0.0% | 0.1; 141.0; 47.0 |
| ventas_usd | financiero | numerico | Valor de venta convertido a USD. | 0.0% | 0.1; 172.67001; 57.55667 |
