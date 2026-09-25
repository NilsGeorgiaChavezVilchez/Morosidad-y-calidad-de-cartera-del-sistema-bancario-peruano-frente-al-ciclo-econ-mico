# Morosidad y calidad de cartera del sistema bancario peruano frente al ciclo económico

**Objetivo:** determinar el efecto del ciclo económico sobre la cartera atrasada de las empresas bancarias del Perú.

## Datos del estudiante

| Campo | Detalle |
|---|---|
| Nombres y apellidos | Nils Georgia Chavez Vilchez |
| Código de matrícula | 2024200493L |
| Asignatura | Finanzas I (055D) – Unidad I – 2026-II – UNCP, Escuela Profesional de Economía |
| Docente | Dr. Ciro Iván Machacuay Meza |
| Tema del temario | Morosidad y calidad de cartera del sistema bancario peruano frente al ciclo económico — **N.º 10** |
| Repositorio | https://github.com/NilsGeorgiaChavezVilchez/Morosidad-y-calidad-de-cartera-del-sistema-bancario-peruano-frente-al-ciclo-econ-mico |

## Fuentes y endpoints

Las series utilizadas se obtienen mediante **BCRPData** (Banco Central de Reserva del Perú), consultadas por API el **24/09/2026**.

En los casos correspondientes, BCRPData reproduce estadísticas cuya fuente primaria es otra institución. Por ejemplo, la serie de IPC utilizada para medir la inflación (`PN01273PM`) tiene como fuente primaria al Instituto Nacional de Estadística e Informática (INEI).

- **Endpoint utilizado:** `https://estadisticas.bcrp.gob.pe/estadisticas/series/api/{CODIGO}/csv/2010-01-01/2025-12-31`

- **Vía utilizada (API) – `01_extraccion_api.py`:** descarga automatizada de 5 series macroeconómicas:
  - PBI: `PN01728AM`
  - Inflación (IPC de Lima Metropolitana, variación % a 12 meses): `PN01273PM`
  - Tasa activa: `PN07807NM`
  - Tasa pasiva: `PN07816NM`
  - Crédito total: `PN00528MM`

  Asimismo, descarga las series de cartera atrasada neta / colocaciones netas por empresa bancaria y la serie correspondiente al total del sistema bancario.

- **Segunda vía – `02_scraping_web.py`:** no utilizada en la Unidad I. De acuerdo con la consigna de la asignatura, la segunda vía de extracción es opcional en esta unidad. El archivo se conserva para mantener la estructura solicitada de `/codigo`, pero no participa en la construcción de la base de datos.

- Los códigos, unidades y definiciones de las variables se encuentran en [`diccionario_variables.md`](diccionario_variables.md).

- La API de BCRPData es pública y **no requiere clave de acceso**. El archivo `.env.example` documenta la variable opcional `USER_AGENT_SCRAPER`.

## Parámetros congelados

Para garantizar la reproducibilidad se utiliza una ventana temporal fija:

- `FECHA_INICIO = 2010-01-01`
- `FECHA_CORTE = 2025-12-31`

Estos parámetros se utilizan en los scripts responsables de la extracción y procesamiento de los datos.

## Orden de ejecución

Instalar primero las dependencias:

```bash
pip install -r requirements.txt
```

Posteriormente ejecutar los scripts en el siguiente orden:

```bash
python 01_extraccion_api.py
python 03_limpieza_datos.py
python 04_analisis.py
```

Función de cada script:

1. `01_extraccion_api.py`: descarga mediante la API de BCRPData los archivos originales y los almacena en `datos_crudos/`.
2. `03_limpieza_datos.py`: tipifica, limpia, integra las series y genera la base final en `datos_procesados/`.
3. `04_analisis.py`: utiliza exclusivamente la base procesada para generar estadísticas, estimaciones, tablas y figuras en `salidas/`.

El archivo `02_scraping_web.py` no forma parte del flujo de ejecución de la Unidad I, debido a que la segunda vía de extracción es opcional.

## Flujo reproducible

```text
BCRPData
    |
    v
01_extraccion_api.py
    |
    v
datos_crudos/
    |
    v
03_limpieza_datos.py
    |
    v
datos_procesados/datos_procesados_2024200493L.csv
    |
    v
04_analisis.py
    |
    v
salidas/
```

## Versiones

Entorno utilizado:

- Python 3.14.0
- requests 2.34.2
- pandas 3.0.6
- numpy 2.5.3
- scipy 1.18.1
- matplotlib 3.11.2
- seaborn 0.13.2
- statsmodels 0.15.0

Las dependencias necesarias para reproducir el proyecto se encuentran en `requirements.txt`.

## Verificación de integridad

El archivo procesado generado es:

`datos_procesados/datos_procesados_2024200493L.csv`

SHA-256 obtenido en la ejecución:

```text
044db6c86e4f8729bb44c7b9f037cc341e6d1c4c0b95cdbc68d8b7c53a9065f1
```

El hash corresponde al archivo procesado generado por `03_limpieza_datos.py` y entregado con el proyecto.

Puede verificarse desde una terminal compatible mediante:

```bash
sha256sum datos_procesados/datos_procesados_2024200493L.csv
```

La ejecución secuencial de `01_extraccion_api.py`, `03_limpieza_datos.py` y `04_analisis.py` permite reproducir el proceso completo de extracción, procesamiento y análisis. Asimismo, `03_limpieza_datos.py` permite regenerar la base procesada a partir de los archivos crudos entregados.

## Contenido del proyecto

| Elemento | Descripción |
|---|---|
| `datos_crudos/` | 21 archivos descargados desde la fuente y conservados sin edición manual |
| `datos_procesados/` | Panel banco-mes con 2 718 observaciones, 15 bancos y 192 meses |
| `datos_procesados_2024200493L.csv` | Base final utilizada para el análisis |
| `salidas/` | Tablas, figuras, matriz de correlaciones y resultados econométricos generados por `04_analisis.py` |
| `log_ejecucion.txt` | Registro de fecha y hora, códigos HTTP, número de filas, estado de las extracciones y ejecución del procesamiento |
| `diccionario_variables.md` | Definición, unidad, frecuencia y fuente de las variables |
| `hash_sha256.txt` | Registro del hash SHA-256 de la base procesada |
| `requirements.txt` | Dependencias necesarias para reproducir el proyecto |
| `.env.example` | Documentación de variables de entorno opcionales |
| `.gitignore` | Archivos excluidos del control de versiones |

## Base procesada

La ejecución de `03_limpieza_datos.py` genera:

- **2 718 observaciones**
- **15 bancos**
- **192 meses**
- **Periodo:** enero de 2010 a diciembre de 2025
- **Valores faltantes en el archivo final:** 0
- **8 variables sustantivas**

Las principales columnas de la base procesada son:

- `fecha`
- `banco`
- `atrasada_neta`
- `atrasada_neta_sistema`
- `pbi`
- `inflacion`
- `tasa_activa`
- `tasa_pasiva`
- `spread`
- `cartera_total`

## Notas metodológicas

### Variable de interés

La variable de interés es la **cartera atrasada neta / colocaciones netas (%)** por empresa bancaria.

La serie utilizada puede registrar valores negativos cuando las provisiones asociadas superan el valor correspondiente de la cartera atrasada. Los datos originales obtenidos de BCRPData se conservan sin modificaciones manuales.

### Inflación

La inflación se representa mediante el **IPC de Lima Metropolitana, variación porcentual a 12 meses**, correspondiente al código `PN01273PM`.

Esta variable mide la variación porcentual del nivel de precios respecto al mismo mes del año anterior.

La serie se obtiene mediante BCRPData y tiene como fuente primaria al INEI.

### Posible quiebre de la serie en enero de 2018

Se observa un salto simultáneo en las series de varios bancos entre diciembre de 2017 y enero de 2018. Por ejemplo, en los datos utilizados se observa un cambio aproximado de −0,21 % a 3,02 % para BCP y de −0,25 % a 3,1 % para el total del sistema.

Este comportamiento se considera un **posible quiebre estructural** y su causa debe contrastarse con la documentación metodológica de la fuente.

Los datos crudos no son modificados para eliminar dicho cambio.

`04_analisis.py` incorpora la variable ficticia `post2018`, definida mediante la constante `FECHA_QUIEBRE`, con el propósito de controlar estadísticamente este posible cambio estructural. La figura correspondiente también identifica temporalmente el punto de quiebre.

Esta situación debe considerarse una limitación al interpretar los resultados.

### Panel no balanceado

El panel no es completamente balanceado debido a que algunas entidades tienen una historia disponible más corta.

Entre ellas:

- Cencosud: 80 meses, desde julio de 2012 hasta febrero de 2019.
- ICBC: 142 meses, desde marzo de 2014.

No se generan observaciones artificiales para completar estos periodos.

### Total del sistema

La serie correspondiente al total del sistema bancario se incorpora como:

`atrasada_neta_sistema`

No se considera como un banco adicional dentro del panel.

### Valores atípicos

Los valores atípicos se identifican mediante el criterio:

`|z modificado| > 3,5`

Los valores detectados se marcan para fines de diagnóstico, pero **no se eliminan automáticamente**, con el objetivo de conservar las observaciones reales de la fuente.

### Modelos

El análisis incluye dos especificaciones principales:

- **Modelo A:** análisis de serie de tiempo del total del sistema bancario con errores HAC.
- **Modelo B:** modelo de panel con efectos fijos por banco y errores agrupados.

Las estimaciones se generan automáticamente mediante `04_analisis.py` a partir de la base ubicada en `datos_procesados/`.

## Acceso automatizado a la fuente

La extracción utiliza únicamente información pública disponible mediante la API de BCRPData.

El script incorpora:

- User-Agent identificable.
- Pausa de 1 segundo entre solicitudes.
- Reintentos ante fallas de conexión.
- Registro del código HTTP.
- Registro del número de filas obtenidas.
- Conservación de los archivos crudos sin edición manual.

Estas medidas permiten documentar y reproducir el proceso de obtención de los datos.

## Cita de la fuente (APA 7)

Banco Central de Reserva del Perú. (2026). *BCRPData: Series estadísticas mensuales* [Base de datos]. Recuperado el 24 de setiembre de 2026 de https://estadisticas.bcrp.gob.pe/estadisticas/series/