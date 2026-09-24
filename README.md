# Morosidad y calidad de cartera del sistema bancario peruano frente al ciclo económico

**Objetivo:** determinar el efecto del ciclo económico sobre la cartera atrasada de las empresas bancarias del Perú.

## Datos del estudiante

| Campo | Detalle |
|---|---|
| Nombres y apellidos | Nils Georgia Chavez Vilchez |
| Código de matrícula | 2024200493L |
| Asignatura | Finanzas I (055D) – Unidad I – 2026-II – UNCP, Escuela Profesional de Economía |
| Docente | Dr. Ciro Iván Machacuay Meza |
| Tema del temario | Morosidad y calidad de cartera del sistema bancario peruano frente al ciclo económico — **N.º de tema: COMPLETAR** |
| Repositorio | https://github.com/NilsGeorgiaChavezVilchez/Morosidad-y-calidad-de-cartera-del-sistema-bancario-peruano-frente-al-ciclo-econ-mico |

## Fuentes y endpoints

Todas las series provienen de **BCRPData** (Banco Central de Reserva del Perú), consultadas por API el **24/09/2026**.

- Endpoint: `https://estadisticas.bcrp.gob.pe/estadisticas/series/api/{CODIGO}/csv/2010-01-01/2025-12-31`
- **Vía 1 (API) – `01_extraccion_api.py`:** 4 series macro (PBI `PN01728AM`, tasa activa `PN07807NM`, tasa pasiva `PN07816NM`, crédito total `PN00528MM`) y 16 series de cartera atrasada neta / colocaciones netas (15 bancos + total del sistema, `PN07729EM`…`PN07746EM`).
- **Vía complementaria – `02_scraping_web.py`:** IPC de Lima Metropolitana, var. % 12 meses (`PN01273PM`), con revisión previa de `robots.txt`. Es una descarga programática del mismo portal, **no un rastreo de HTML**; en la Unidad I esta segunda vía es opcional y no se presenta como scraping.
- Los códigos, unidades y definiciones de cada variable están en [`diccionario_variables.md`](diccionario_variables.md).
- La API es pública: **no requiere clave**. Ver `.env.example` (solo variable opcional `USER_AGENT_SCRAPER`).

**Parámetros congelados:** `FECHA_INICIO = 2010-01-01`, `FECHA_CORTE = 2025-12-31`, declarados como constantes en los scripts `01`, `02` y `03`.

## Orden de ejecución

```bash
pip install -r requirements.txt
python 01_extraccion_api.py      # crudos en datos_crudos/ y log_ejecucion.txt (lo reinicia)
python 02_scraping_web.py        # serie complementaria (IPC); agrega líneas al log
python 03_limpieza_datos.py      # panel en datos_procesados/ y hash_sha256.txt
python 04_analisis.py            # tablas y figuras en salidas/
```

Ejecutar desde la carpeta raíz del proyecto (todas las rutas son relativas).

## Versiones

Python 3.14.0 · requests 2.34.2 · pandas 3.0.6 · numpy 2.5.3 · scipy 1.18.1 · matplotlib 3.11.2 · seaborn 0.13.2 · statsmodels 0.15.0 (ver `requirements.txt`).

## Verificación de integridad

Hash SHA-256 de `datos_procesados/datos_procesados_2024200493L.csv`:

```
044db6c86e4f8729bb44c7b9f037cc341e6d1c4c0b95cdbc68d8b7c53a9065f1
```

Se declara sobre el archivo entregado (no sobre una reejecución posterior). Verificación en consola: `sha256sum datos_procesados/datos_procesados_2024200493L.csv`. La reejecución de `03` y `04` sobre los crudos entregados reproduce este mismo hash.

## Contenido del proyecto

| Elemento | Descripción |
|---|---|
| `datos_crudos/` | 21 archivos tal como los devuelve la fuente (sin editar) |
| `datos_procesados/` | Panel banco-mes: 2 718 observaciones, 15 bancos, 192 meses, 11 columnas (8 sustantivas) |
| `salidas/` | 6 figuras, 4 tablas y `regresion_morosidad.txt` generadas por `04_analisis.py` |
| `log_ejecucion.txt` | Fecha y hora, código HTTP, filas y estado de cada extracción, más resumen de `03` y `04` |
| `diccionario_variables.md` | Definición, unidad, frecuencia y fuente de cada variable |

## Notas metodológicas

- **Variable endógena:** cartera atrasada neta / colocaciones netas (%). Es neta de provisiones, por lo que puede ser negativa (provisiones > cartera atrasada). El BCRPData no publica en estas familias de series la razón bruta por banco.
- **Quiebre de la serie en enero de 2018:** todos los bancos saltan a la vez entre dic-2017 y ene-2018 (p. ej. BCP de −0,21 % a 3,02 %; sistema de −0,25 % a 3,1 %). Es un cambio de definición o metodología en la fuente y no un shock económico. El dato crudo no se edita; `04_analisis.py` lo controla con la variable ficticia `post2018` (constante `FECHA_QUIEBRE`) y la figura 1 lo marca. Debe declararse como limitación en el artículo.
- **Panel no balanceado:** Cencosud (80 meses, 2012-07 a 2019-02) e ICBC (142 meses, desde 2014-03) tienen historia corta; no se imputan.
- **Total del sistema:** va como columna `atrasada_neta_sistema`, no como un banco más.
- **Atípicos:** se marcan (z modificado > 3,5) y se conservan; no se eliminan datos reales.
- **Modelos:** (A) serie de tiempo del sistema con errores HAC; (B) panel con efectos fijos por banco y errores agrupados.
- **Ética del rastreo:** solo información pública, pausa de 1 s entre solicitudes y User-Agent identificable.

## Cita de la fuente (APA 7)

Banco Central de Reserva del Perú. (2026). *BCRPData: Series estadísticas mensuales* [Base de datos]. Recuperado el 24 de setiembre de 2026 de https://estadisticas.bcrp.gob.pe/estadisticas/series/
