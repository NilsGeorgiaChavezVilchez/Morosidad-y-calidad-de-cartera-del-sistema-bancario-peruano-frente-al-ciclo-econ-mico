# Diccionario de variables

Archivo: `datos_procesados/datos_procesados_2024200493L.csv`  
Separador: `;`  
Decimal: `.`  
Codificación: UTF-8

La base procesada corresponde a un panel banco-mes no balanceado con **2 718 observaciones, 15 bancos y 192 meses**, comprendidos entre enero de 2010 y diciembre de 2025.

## Fuente de los datos

Las series utilizadas en la investigación se obtienen mediante **BCRPData – Banco Central de Reserva del Perú**, consultado el **24/09/2026**.

BCRPData constituye la vía de obtención de las series utilizadas. En determinados casos, la fuente primaria de la estadística corresponde a otra institución. En particular, la serie del IPC de Lima Metropolitana utilizada para medir la inflación (`PN01273PM`) tiene como fuente primaria al **Instituto Nacional de Estadística e Informática (INEI)**.

**Endpoint de extracción:**

`https://estadisticas.bcrp.gob.pe/estadisticas/series/api/{CODIGO}/csv/2010-01-01/2025-12-31`

## Variables

| Variable | Definición | Unidad | Frecuencia | Código BCRP / origen |
|---|---|---|---|---|
| `Id` | Identificador correlativo de la observación. No constituye una variable sustantiva. | – | – | Generada en `03_limpieza_datos.py` |
| `fecha` | Primer día del mes correspondiente a la observación. Se utiliza como llave temporal para integrar las series. | AAAA-MM-DD | Mensual | Cabecera temporal de las series obtenidas mediante BCRPData |
| `banco` | Empresa bancaria correspondiente a la observación. Se utiliza como identificador de entidad dentro del panel. | Texto | – | Construida a partir de las series bancarias detalladas en la tabla de bancos |
| `atrasada_neta` | **Variable endógena.** Cartera atrasada neta / colocaciones netas de cada empresa bancaria. Al tratarse de una medida neta de provisiones, puede registrar valores negativos cuando las provisiones superan la cartera atrasada. | % | Mensual | `PN07729EM` a `PN07745EM`, según entidad (ver tabla de bancos) |
| `atrasada_neta_sistema` | Cartera atrasada neta / colocaciones netas correspondiente al total de empresas bancarias. Se utiliza como indicador agregado del sistema y no como una entidad adicional del panel. | % | Mensual | `PN07746EM` |
| `pbi` | Producto bruto interno, variación porcentual interanual. Representa la evolución del ciclo económico. | % | Mensual | `PN01728AM` |
| `inflacion` | IPC de Lima Metropolitana, variación porcentual a 12 meses. Representa la variación de los precios respecto al mismo mes del año anterior. | % | Mensual | `PN01273PM` – obtenida mediante BCRPData; fuente primaria: INEI |
| `tasa_activa` | Tasa de interés activa promedio de las empresas bancarias en moneda nacional (TAMN), expresada en términos efectivos anuales. | % anual | Mensual | `PN07807NM` |
| `tasa_pasiva` | Tasa de interés pasiva promedio de las empresas bancarias en moneda nacional (TIPMN), expresada en términos efectivos anuales. | % anual | Mensual | `PN07816NM` |
| `spread` | Diferencial bancario calculado como `tasa_activa - tasa_pasiva`. | Puntos porcentuales | Mensual | Variable derivada en `03_limpieza_datos.py` |
| `cartera_total` | Crédito del sistema bancario al sector privado, registrado a fin de periodo. | Millones de S/ | Mensual | `PN00528MM` |

## Bancos y códigos de cartera atrasada neta / colocaciones netas

| Banco | Código | Meses con dato | Observación |
|---|---|---:|---|
| BCP | `PN07729EM` | 192 | – |
| Interbank | `PN07730EM` | 192 | – |
| Scotiabank | `PN07732EM` | 192 | – |
| Continental | `PN07733EM` | 192 | – |
| Comercio | `PN07734EM` | 192 | – |
| Financiero | `PN07735EM` | 192 | – |
| BanBif | `PN07736EM` | 192 | – |
| MiBanco | `PN07737EM` | 192 | – |
| GNB | `PN07738EM` | 192 | – |
| Falabella | `PN07739EM` | 192 | – |
| Santander | `PN07740EM` | 192 | – |
| Ripley | `PN07741EM` | 192 | – |
| Azteca | `PN07742EM` | 192 | Presenta valores extremos dentro del periodo analizado (mín. −26,5; máx. 22,7) |
| Cencosud | `PN07744EM` | 80 | Disponible entre 2012-07 y 2019-02; no se imputan periodos sin observación |
| ICBC | `PN07745EM` | 142 | Disponible desde 2014-03; no se imputan periodos anteriores |
| Total sistema | `PN07746EM` | 192 | Agregado del sistema; se incorpora como `atrasada_neta_sistema` y no como un banco adicional |

## Notas de tratamiento

### Posible quiebre estructural en enero de 2018

Se observa un salto simultáneo en las series de varios bancos entre diciembre de 2017 y enero de 2018. Por ejemplo, en los datos utilizados se observa un cambio aproximado de −0,21 % a 3,02 % para BCP y de −0,25 % a 3,1 % para el total del sistema.

Este comportamiento se considera un **posible quiebre estructural**. La información disponible en la base, por sí sola, no permite atribuir de manera concluyente su causa a un cambio metodológico o a un fenómeno económico específico, por lo que su interpretación debe contrastarse con la documentación de la fuente.

Los datos crudos se conservan sin modificación. `04_analisis.py` incorpora la variable ficticia `post2018`, definida mediante la constante `FECHA_QUIEBRE`, para controlar estadísticamente este posible cambio estructural. Asimismo, la figura correspondiente identifica temporalmente el punto de quiebre.

Esta característica se considera una limitación al interpretar los resultados.

### Valores faltantes

El archivo procesado final no presenta valores faltantes.

Los bancos que disponen de una historia más corta se mantienen dentro de un **panel no balanceado** y sus periodos no disponibles no son imputados artificialmente.

### Valores atípicos

Los valores atípicos se identifican mediante el **puntaje z modificado basado en la desviación absoluta mediana (MAD)**, utilizando como criterio:

`|z modificado| > 3,5`

Las observaciones identificadas se registran en `log_ejecucion.txt`, pero **no se eliminan automáticamente**, con el objetivo de conservar los datos reales obtenidos de la fuente.

### Total del sistema

La serie `PN07746EM` corresponde al agregado del sistema bancario.

Se incorpora a la base mediante la variable `atrasada_neta_sistema` y **no se contabiliza como un banco adicional** dentro de las 15 entidades que conforman el panel.

### Ventana temporal

La ventana utilizada en el proyecto está congelada mediante los siguientes parámetros:

- `FECHA_INICIO = 2010-01-01`
- `FECHA_CORTE = 2025-12-31`

Estos parámetros son utilizados por `01_extraccion_api.py` para realizar la extracción y por `03_limpieza_datos.py` para controlar el periodo de procesamiento.

La segunda vía de extracción (`02_scraping_web.py`) **no se utiliza en la Unidad I**, por lo que no participa en la construcción de la base procesada.

## Procedencia de las variables

Las variables originales se descargan automáticamente mediante:

`01_extraccion_api.py`

Las variables derivadas y la estructura final del panel se generan mediante:

`03_limpieza_datos.py`

Finalmente, las tablas, figuras y estimaciones se generan desde el archivo procesado mediante:

`04_analisis.py`

Por tanto, el flujo utilizado para la Unidad I es:

```text
01_extraccion_api.py
        ↓
datos_crudos/
        ↓
03_limpieza_datos.py
        ↓
datos_procesados_2024200493L.csv
        ↓
04_analisis.py
        ↓
salidas/
```