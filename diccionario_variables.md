# Diccionario de variables

Archivo: `datos_procesados/datos_procesados_2024200493L.csv`  
Separador: `;`  
Decimal: `.`  
Codificación: UTF-8

La base procesada corresponde a un panel banco-mes no balanceado con **2 718 observaciones, 15 bancos y 192 meses**, comprendidos entre enero de 2010 y diciembre de 2025.

## Fuente de los datos

Las series utilizadas en la investigación se obtienen mediante **BCRPData – Banco Central de Reserva del Perú**, consultado el **25/09/2026**.

BCRPData constituye la vía de obtención de las series utilizadas. En determinados casos, la fuente primaria de la estadística corresponde a otra institución. En particular, la serie del IPC de Lima Metropolitana utilizada para medir la inflación (`PN01273PM`) tiene como fuente primaria al **Instituto Nacional de Estadística e Informática (INEI)**.

**Endpoint de extracción:**

`https://estadisticas.bcrp.gob.pe/estadisticas/series/api/{CODIGO}/csv/2010-01-01/2025-12-31`

## Variables

| Variable | Definición | Unidad | Frecuencia | Código BCRP / origen |
|---|---|---|---|---|
| `Id` | Identificador correlativo de la observación. No constituye una variable sustantiva. | Identificador | Mensual | Generada en `03_limpieza_datos.py` |
| `fecha` | Primer día del mes correspondiente a la observación. Se utiliza como llave temporal para integrar las series. | AAAA-MM-DD | Mensual | Cabecera temporal de las series obtenidas mediante BCRPData |
| `banco` | Empresa bancaria correspondiente a la observación. Se utiliza como identificador de entidad dentro del panel. | Texto | Mensual | Construida a partir de las series bancarias detalladas en la tabla de bancos |
| `atrasada_neta` | **Variable endógena.** Cartera atrasada neta / colocaciones netas de cada empresa bancaria. Al tratarse de una medida neta de provisiones, puede registrar valores negativos cuando las provisiones superan la cartera atrasada. | % | Mensual | `PN07729EM` a `PN07745EM`, según entidad (ver tabla de bancos) |
| `atrasada_neta_sistema` | Cartera atrasada neta / colocaciones netas correspondiente al total de empresas bancarias. Se utiliza como indicador agregado del sistema y no como una entidad adicional del panel. | % | Mensual | `PN07746EM` |
| `pbi` | Producto bruto interno, variación porcentual interanual. Representa la evolución del ciclo económico. | % | Mensual | `PN01728AM` |
| `inflacion` | IPC de Lima Metropolitana, variación porcentual a 12 meses. Representa la variación de los precios respecto al mismo mes del año anterior. | % | Mensual | `PN01273PM` – obtenida mediante BCRPData; fuente primaria: INEI |
| `tasa_activa` | Tasa de interés activa promedio de las empresas bancarias en moneda nacional (TAMN), expresada en términos efectivos anuales. | % anual | Mensual | `PN07807NM` |
| `tasa_pasiva` | Tasa de interés pasiva promedio de las empresas bancarias en moneda nacional (TIPMN), expresada en términos efectivos anuales. | % anual | Mensual | `PN07816NM` |
| `spread` | Diferencial bancario calculado como `tasa_activa - tasa_pasiva`. | Puntos porcentuales | Mensual | Variable derivada en `03_limpieza_datos.py` |
| `cartera_total` | Crédito del sistema bancario al sector privado, registrado a fin de periodo. | Millones de S/ | Mensual | `PN00528MM` |
| `dato_macro_imputado` | Indicador técnico de trazabilidad que identifica si alguna variable macroeconómica del mes presentaba originalmente un valor faltante antes del tratamiento. En la ejecución final todos sus valores son 0. | 0 = no; 1 = sí | Mensual | Generada en `03_limpieza_datos.py` |

## Variables derivadas durante el análisis

Las siguientes variables no forman parte del archivo procesado original. Se generan automáticamente durante la ejecución de `04_analisis.py`.

| Variable | Definición | Cálculo | Uso |
|---|---|---|---|
| `ln_cartera` | Logaritmo natural de la cartera total. | `ln(cartera_total)` | Variable de control en los modelos |
| `pbi_lag3` | PBI rezagado 3 meses. | `pbi.shift(3)` | Análisis de rezagos |
| `pbi_lag6` | PBI rezagado 6 meses. | `pbi.shift(6)` | Análisis de rezagos |
| `pbi_lag12` | PBI rezagado 12 meses. | `pbi.shift(12)` | Análisis de rezagos |
| `d_atrasada` | Primera diferencia de la cartera atrasada neta del sistema. | `atrasada_neta_sistema(t) - atrasada_neta_sistema(t-1)` | Modelo C |
| `d_spread` | Primera diferencia del spread. | `spread(t) - spread(t-1)` | Modelo C |

Estas transformaciones son determinísticas y reproducibles y no modifican `datos_procesados_2024200493L.csv`.

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

### Comportamiento observado alrededor de enero de 2018

Durante la revisión de las series se observa un cambio de nivel simultáneo en varios indicadores de cartera atrasada neta alrededor de enero de 2018.

Los valores publicados por BCRPData se conservan sin modificaciones.

La información disponible no permite atribuir este comportamiento de manera concluyente a una modificación metodológica o a un fenómeno económico específico.

Por este motivo, el cambio se considera únicamente como una característica de la evolución histórica de las series y debe tenerse presente al interpretar los resultados.

No se eliminan observaciones ni se incorpora una variable ficticia para modificar este comportamiento.

### Valores faltantes

El archivo procesado final no presenta valores faltantes.

Las variables macroeconómicas son revisadas previamente para identificar faltantes. `03_limpieza_datos.py` está preparado para aplicar interpolación lineal únicamente cuando existen pocos huecos internos.

No se interpolan valores faltantes ubicados en los extremos de las series.

En la ejecución final:

```text
Valores faltantes finales: 0
Meses macro con alguna imputación: 0
```

Por tanto, no fue necesario aplicar imputación sobre ninguna variable macroeconómica de la base final.

Los bancos que disponen de una historia más corta se mantienen dentro de un **panel no balanceado** y sus periodos no disponibles no son imputados artificialmente.

### Variable técnica `dato_macro_imputado`

La variable `dato_macro_imputado` se conserva como indicador técnico de trazabilidad.

Su interpretación es:

```text
0 = el mes no presentaba valores macroeconómicos faltantes antes del tratamiento.
1 = al menos una variable macroeconómica del mes presentaba originalmente un valor faltante.
```

En la ejecución final todos los registros toman el valor `0`.

Esta variable no participa en las estimaciones econométricas.

### Valores atípicos

Los valores atípicos se identifican mediante el **puntaje z modificado basado en la desviación absoluta mediana (MAD)**, utilizando como criterio:

`|z modificado| > 3,5`

En la ejecución final se identificaron **14 valores atípicos**.

Las observaciones identificadas se registran en `log_ejecucion.txt`, pero **no se eliminan automáticamente**, con el objetivo de conservar los datos reales obtenidos de la fuente.

### Total del sistema

La serie `PN07746EM` corresponde al agregado del sistema bancario.

Se incorpora a la base mediante la variable `atrasada_neta_sistema` y **no se contabiliza como un banco adicional** dentro de las 15 entidades que conforman el panel.

### Panel no balanceado

El panel no es completamente balanceado debido a que algunas entidades presentan una historia disponible más corta.

En particular:

- Cencosud dispone de 80 meses, entre julio de 2012 y febrero de 2019.
- ICBC dispone de 142 meses, desde marzo de 2014 hasta diciembre de 2025.

No se generan observaciones artificiales para completar los periodos en los que la fuente no presenta información.

### Ventana temporal

La ventana utilizada en el proyecto está congelada mediante los siguientes parámetros:

- `FECHA_INICIO = 2010-01-01`
- `FECHA_CORTE = 2025-12-31`

Estos parámetros son utilizados por `01_extraccion_api.py` para realizar la extracción y por `03_limpieza_datos.py` para controlar el periodo de procesamiento.

El rango efectivo de la base final es:

```text
2010-01-01 a 2025-12-01
```

El último registro corresponde a diciembre de 2025 debido a la frecuencia mensual de las series.

La segunda vía de extracción (`02_scraping_web.py`) **no se utiliza en la Unidad I**, por lo que no participa en la construcción de la base procesada.

## Procedencia de las variables

Las variables originales se descargan automáticamente mediante:

`01_extraccion_api.py`

Entre ellas se encuentran:

- `pbi`
- `inflacion`
- `tasa_activa`
- `tasa_pasiva`
- `cartera_total`
- series bancarias utilizadas para `atrasada_neta`
- `atrasada_neta_sistema`

La estructura final del panel y las variables derivadas incluidas directamente en el archivo procesado se generan mediante:

`03_limpieza_datos.py`

Entre ellas:

- `Id`
- `banco`
- `spread`
- `dato_macro_imputado`

Las transformaciones utilizadas únicamente durante el análisis econométrico se generan mediante:

`04_analisis.py`

Entre ellas:

- `ln_cartera`
- `pbi_lag3`
- `pbi_lag6`
- `pbi_lag12`
- `d_atrasada`
- `d_spread`

Finalmente, las tablas, figuras, diagnósticos y estimaciones se generan desde el archivo procesado mediante:

`04_analisis.py`

Por tanto, el flujo utilizado para la Unidad I es:

```text
01_extraccion_api.py
        ↓
datos_crudos/
        ↓
03_limpieza_datos.py
        ↓
datos_procesados/datos_procesados_2024200493L.csv
        ↓
04_analisis.py
        ↓
salidas/
```