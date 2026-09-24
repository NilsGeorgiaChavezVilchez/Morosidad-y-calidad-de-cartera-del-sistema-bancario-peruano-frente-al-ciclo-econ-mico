# Diccionario de variables

Archivo: `datos_procesados/datos_procesados_2024200493L.csv` (separador `;`, decimal `.`, codificación UTF-8).
Panel banco-mes no balanceado: 2 718 observaciones, 15 bancos, 192 meses (2010-01 a 2025-12).
Fuente única de todas las variables: **BCRPData – Banco Central de Reserva del Perú** (https://estadisticas.bcrp.gob.pe), fecha de consulta 24/09/2026.
Endpoint: `https://estadisticas.bcrp.gob.pe/estadisticas/series/api/{CODIGO}/csv/2010-01-01/2025-12-31`

| Variable | Definición | Unidad | Frecuencia | Código BCRP / origen |
|---|---|---|---|---|
| `Id` | Identificador correlativo de la observación (no sustantiva) | – | – | Generada en `03_limpieza_datos.py` |
| `fecha` | Primer día del mes de la observación (llave común de unión) | AAAA-MM-DD | Mensual | Cabecera "Mes.Año" del BCRP |
| `banco` | Empresa bancaria (llave de entidad) | texto | – | Ver tabla de bancos |
| `atrasada_neta` | **Variable endógena.** Cartera atrasada neta / colocaciones netas del banco. Es una medida **neta de provisiones**: es negativa cuando las provisiones superan la cartera atrasada (no es un error de datos) | % | Mensual | `PN07729EM`…`PN07745EM` (ver tabla) |
| `atrasada_neta_sistema` | Misma razón para el total de empresas bancarias (agregado del sistema) | % | Mensual | `PN07746EM` |
| `pbi` | Producto bruto interno, variación porcentual interanual | % | Mensual | `PN01728AM` |
| `inflacion` | IPC de Lima Metropolitana, variación porcentual a 12 meses | % | Mensual | `PN01273PM` |
| `tasa_activa` | Tasa de interés activa promedio de las empresas bancarias en moneda nacional (TAMN), términos efectivos anuales | % anual | Mensual | `PN07807NM` |
| `tasa_pasiva` | Tasa de interés pasiva promedio de las empresas bancarias en moneda nacional (TIPMN), términos efectivos anuales | % anual | Mensual | `PN07816NM` |
| `spread` | Diferencial bancario = `tasa_activa` − `tasa_pasiva` (variable derivada) | puntos porcentuales | Mensual | Calculada en `03_limpieza_datos.py` |
| `cartera_total` | Crédito del sistema bancario al sector privado, fin de periodo | millones de S/ | Mensual | `PN00528MM` |

## Bancos y códigos (cartera atrasada neta / colocaciones netas)

| Banco | Código | Meses con dato | Observación |
|---|---|---|---|
| BCP | PN07729EM | 192 | – |
| Interbank | PN07730EM | 192 | – |
| Scotiabank | PN07732EM | 192 | – |
| Continental | PN07733EM | 192 | – |
| Comercio | PN07734EM | 192 | – |
| Financiero | PN07735EM | 192 | – |
| BanBif | PN07736EM | 192 | – |
| MiBanco | PN07737EM | 192 | – |
| GNB | PN07738EM | 192 | – |
| Falabella | PN07739EM | 192 | – |
| Santander | PN07740EM | 192 | – |
| Ripley | PN07741EM | 192 | – |
| Azteca | PN07742EM | 192 | Presenta valores extremos (mín. −26,5; máx. 22,7) |
| Cencosud | PN07744EM | 80 | Solo 2012-07 a 2019-02 (el banco operó en ese lapso); no se imputa |
| ICBC | PN07745EM | 142 | Solo desde 2014-03; no se imputa |
| Total sistema | PN07746EM | 192 | Agregado; va como columna `atrasada_neta_sistema`, no como banco |

## Notas de tratamiento

- **Quiebre de la serie en enero de 2018:** todos los bancos saltan a la vez entre dic-2017 y ene-2018 (p. ej. BCP de −0,21 % a 3,02 %; sistema de −0,25 % a 3,1 %). Es un cambio de definición o metodología en la fuente y no un shock económico. El dato crudo no se edita; `04_analisis.py` lo controla con la variable ficticia `post2018` (constante `FECHA_QUIEBRE`) y la figura 1 lo marca. Debe declararse como limitación en el artículo.
- **Faltantes:** no hay valores faltantes en el archivo final. Los bancos con historia corta se conservan como panel no balanceado, sin imputar.
- **Atípicos:** se detectan con puntaje z modificado (MAD > 3,5) por banco; se registran en el log y **se conservan**, porque corresponden a episodios reales.
- **Ventana:** `FECHA_INICIO = 2010-01-01` y `FECHA_CORTE = 2025-12-31`, declaradas como constantes en `01`, `02` y `03`.
