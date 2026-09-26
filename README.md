# Morosidad y calidad de cartera del sistema bancario peruano frente al ciclo económico

**Objetivo:** analizar la relación entre el ciclo económico y la calidad de cartera del sistema bancario peruano durante el periodo 2010–2025.

## Datos del estudiante

| Campo | Detalle |
|---|---|
| Nombres y apellidos | Nils Georgia Chavez Vilchez |
| Código de matrícula | 2024200493L |
| Asignatura | Finanzas I (055D) – Unidad I – 2026-II |
| Universidad | Universidad Nacional del Centro del Perú – Escuela Profesional de Economía |
| Docente | Dr. Ciro Iván Machacuay Meza |
| Tema | N.º 10: Morosidad y calidad de cartera del sistema bancario peruano frente al ciclo económico |
| Repositorio | https://github.com/NilsGeorgiaChavezVilchez/Morosidad-y-calidad-de-cartera-del-sistema-bancario-peruano-frente-al-ciclo-econ-mico |

---

## Fuente y endpoint

La base se construye mediante extracción automatizada desde **BCRPData**, del Banco Central de Reserva del Perú.

**Fecha de extracción:** 24/09/2026.

**Endpoint general:**

```text
https://estadisticas.bcrp.gob.pe/estadisticas/series/api/{CODIGO}/csv/2010-01-01/2025-12-31
```

Series macroeconómicas utilizadas:

| Variable | Código BCRP |
|---|---|
| PBI | PN01728AM |
| Inflación | PN01273PM |
| Tasa activa | PN07807NM |
| Tasa pasiva | PN07816NM |
| Crédito total | PN00528MM |

También se descargan 15 series de cartera atrasada neta por banco y una serie agregada del sistema bancario.

`02_scraping_web.py` no participa en la construcción de la base de la Unidad I, debido a que la segunda vía automatizada es opcional en esta unidad.

---

## Parámetros congelados

```text
FECHA_INICIO = 2010-01-01
FECHA_CORTE = 2025-12-31
```

No se utilizan fechas dinámicas.

Periodo efectivo de la base:

```text
enero de 2010 a diciembre de 2025
```

---

## Orden de ejecución

Instalar dependencias:

```bash
pip install -r requirements.txt
```

Ejecutar:

```bash
python 01_extraccion_api.py
python 03_limpieza_datos.py
python 04_analisis.py
```

Funciones:

- `01_extraccion_api.py`: descarga y guarda los archivos crudos.
- `02_scraping_web.py`: segunda vía no utilizada en la Unidad I.
- `03_limpieza_datos.py`: limpia, integra y genera la base procesada.
- `04_analisis.py`: genera estimaciones, tablas, diagnósticos y figuras en `salidas/`.

---

## Base procesada

Archivo final:

```text
datos_procesados/datos_procesados_2024200493L.csv
```

Resultado final:

```text
Observaciones: 2718
Bancos: 15
Meses: 192
Rango: 2010-01-01 a 2025-12-01
Valores faltantes finales: 0
Meses macro con alguna imputación: 0
Valores atípicos identificados: 14
Variables sustantivas: 8
```

Columnas:

```text
Id
fecha
banco
atrasada_neta
atrasada_neta_sistema
pbi
inflacion
tasa_activa
tasa_pasiva
spread
cartera_total
dato_macro_imputado
```

Las definiciones, unidades, frecuencias y códigos de las variables se encuentran en:

```text
diccionario_variables.md
```

---

## Tratamiento de datos

Los archivos crudos se conservan sin edición manual.

Las variables macroeconómicas pueden interpolarse linealmente únicamente cuando existen pocos faltantes internos. No se interpolan extremos ni faltantes bancarios.

En la ejecución final no fue necesario realizar imputaciones macroeconómicas.

Los valores atípicos se identifican mediante:

```text
|z modificado| > 3.5
```

utilizando MAD. Se identificaron 14 valores, pero no se eliminaron ni modificaron.

El panel es no balanceado porque algunas entidades presentan series más cortas.

---

## Variables derivadas

`03_limpieza_datos.py` construye:

```text
spread = tasa_activa - tasa_pasiva
```

`04_analisis.py` genera para el análisis:

```text
ln_cartera
pbi_lag3
pbi_lag6
pbi_lag12
d_atrasada
d_spread
```

Estas transformaciones se crean durante el análisis y no modifican la base procesada original.

---

## Análisis realizado

`04_analisis.py` genera:

- estadísticos descriptivos;
- matriz de correlaciones;
- correlaciones de Pearson y p-valores;
- correlación parcial;
- PBI contemporáneo y rezagos de 3, 6 y 12 meses;
- Modelo A para el total del sistema;
- Modelo B de panel con efectos fijos por banco;
- Modelo C de robustez de corto plazo;
- VIF;
- Breusch-Pagan;
- Breusch-Godfrey;
- Jarque-Bera;
- pruebas ADF en niveles y primeras diferencias;
- diagnóstico ADF de residuos;
- ocho figuras.

### Modelo A

```text
atrasada_neta_sistema
~ pbi + inflacion + spread + ln_cartera
```

Errores estándar HAC Newey-West con 12 rezagos.

### Modelo B

```text
atrasada_neta
~ pbi + inflacion + spread + ln_cartera + C(banco)
```

Errores estándar agrupados por banco.

### Modelo C

```text
d_atrasada
~ pbi + inflacion + d_spread + ln_cartera
```

Se utiliza como especificación de robustez de corto plazo.

---

## Estacionariedad

Las pruebas ADF indicaron que:

- `atrasada_neta_sistema`: no estacionaria en niveles;
- `spread`: no estacionaria en niveles;
- `pbi`: estacionaria;
- `inflacion`: estacionaria al 5 %;
- `ln_cartera`: estacionaria.

En primeras diferencias:

- `d_atrasada`: estacionaria;
- `d_spread`: estacionaria.

Las diferencias se generan únicamente dentro de `04_analisis.py`.

---

## Salidas

La carpeta `salidas/` contiene las tablas, diagnósticos, regresiones y ocho figuras generadas automáticamente desde la base procesada.

Entre ellas:

```text
estadisticos_descriptivos.csv
matriz_correlaciones.csv
correlaciones_pearson_pvalores.csv
correlaciones_pbi_rezagos.csv
correlacion_parcial.csv
tabla_por_banco.csv
modelos_pbi_rezagos.csv
diagnostico_vif.csv
diagnostico_breusch_pagan.csv
diagnostico_breusch_godfrey.csv
diagnostico_jarque_bera.csv
pruebas_adf.csv
pruebas_adf_diferencias.csv
diagnostico_adf_residuos.csv
modelo_robustez_diferencias.csv
regresion_morosidad.txt
```

Figuras:

```text
figura_01_morosidad_vs_pbi.png
figura_02_tasas_y_spread.png
figura_03_cartera_creditos.png
figura_04_heatmap_correlaciones.png
figura_05_regresion_morosidad_pbi.png
figura_06_distribucion_por_banco.png
figura_07_correlaciones_pbi_rezagos.png
figura_08_cambio_morosidad_vs_pbi.png
```

---

## Integridad y reproducibilidad

SHA-256 del archivo procesado:

```text
f4c97a840b37602261d66b2ce445410ed58c674e8f621eb333e665ea68c8203b
```

El mismo valor se guarda en:

```text
hash_sha256.txt
```

El archivo `log_ejecucion.txt` registra fecha y hora, códigos HTTP, número de filas descargadas y resultados principales del procesamiento.

La API no requiere clave privada. `.env.example` documenta:

```text
USER_AGENT_SCRAPER=EstudianteUNCP-FinanzasI/1.0 (2024200493L)
```

Las versiones exactas de las librerías se encuentran en `requirements.txt`.

---

## Estructura principal del proyecto

```text
datos_crudos/
datos_procesados/
salidas/
01_extraccion_api.py
02_scraping_web.py
03_limpieza_datos.py
04_analisis.py
diccionario_variables.md
README.md
requirements.txt
.env.example
log_ejecucion.txt
hash_sha256.txt
```

---

## Repositorio

```text
https://github.com/NilsGeorgiaChavezVilchez/Morosidad-y-calidad-de-cartera-del-sistema-bancario-peruano-frente-al-ciclo-econ-mico
```

El historial debe conservar al menos tres commits realizados en fechas distintas.

---

## Fuente

Banco Central de Reserva del Perú. (2026). *BCRPData: Series estadísticas* [Base de datos]. Recuperado el 24 de setiembre de 2026 de https://estadisticas.bcrp.gob.pe/estadisticas/series/