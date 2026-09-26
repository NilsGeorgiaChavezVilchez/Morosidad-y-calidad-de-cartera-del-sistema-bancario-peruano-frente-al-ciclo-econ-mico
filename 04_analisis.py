# Nombres y apellidos: Nils Georgia Chavez Vilchez
# Código de matrícula: 2024200493L
# Tema N.º 10: Morosidad y calidad de cartera del sistema bancario peruano frente al ciclo económico
# Fecha de extracción: 2026-09-24

"""
04_analisis.py

Genera estadísticas, estimaciones, diagnósticos, tablas y figuras
a partir de la base procesada por 03_limpieza_datos.py.

Todas las salidas se guardan automáticamente en /salidas.
"""

# ============================================================
# LIBRERÍAS
# ============================================================

from datetime import datetime
from pathlib import Path
import warnings

import matplotlib

warnings.filterwarnings(
    "ignore",
    message="covariance of constraints"
)

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
import statsmodels.api as sm
import statsmodels.formula.api as smf

from scipy.stats import pearsonr

from statsmodels.stats.diagnostic import (
    het_breuschpagan,
    acorr_breusch_godfrey,
)

from statsmodels.stats.outliers_influence import (
    variance_inflation_factor,
)

from statsmodels.stats.stattools import jarque_bera
from statsmodels.tsa.stattools import adfuller


# ============================================================
# 1. PARÁMETROS Y RUTAS
# ============================================================

# Se utilizan rutas relativas para que el proyecto sea reproducible.

CODIGO_MATRICULA = "2024200493L"

BASE_DIR = Path(__file__).resolve().parent

RUTA_DATOS = (
    BASE_DIR
    / "datos_procesados"
    / f"datos_procesados_{CODIGO_MATRICULA}.csv"
)

CARPETA_SALIDAS = BASE_DIR / "salidas"
ARCHIVO_LOG = BASE_DIR / "log_ejecucion.txt"

CARPETA_SALIDAS.mkdir(
    parents=True,
    exist_ok=True
)


# ============================================================
# 2. FUNCIONES AUXILIARES
# ============================================================

def registrar(mensaje):
    """Muestra un mensaje en consola y lo registra en el log."""

    print(mensaje)

    with open(
        ARCHIVO_LOG,
        "a",
        encoding="utf-8"
    ) as f:
        f.write(mensaje + "\n")


def resumen_variable(nombre, serie):
    """Calcula estadísticos descriptivos básicos."""

    serie = serie.dropna()

    return {
        "Variable": nombre,
        "N": int(serie.count()),
        "Media": serie.mean(),
        "Mediana": serie.median(),
        "Desv. Est.": serie.std(),
        "Mínimo": serie.min(),
        "Máximo": serie.max(),
    }


def correlacion_pearson(x, y):
    """Calcula correlación de Pearson y su p-valor."""

    datos = pd.concat(
        [x, y],
        axis=1
    ).dropna()

    r, p = pearsonr(
        datos.iloc[:, 0],
        datos.iloc[:, 1]
    )

    return r, p, len(datos)


def correlacion_parcial(
    datos,
    variable_x,
    variable_y,
    controles
):
    """Calcula correlación parcial controlando otras variables."""

    columnas = [
        variable_x,
        variable_y
    ] + controles

    temp = datos[columnas].dropna().copy()

    X_controles = sm.add_constant(
        temp[controles],
        has_constant="add"
    )

    modelo_x = sm.OLS(
        temp[variable_x],
        X_controles
    ).fit()

    modelo_y = sm.OLS(
        temp[variable_y],
        X_controles
    ).fit()

    r, p = pearsonr(
        modelo_x.resid,
        modelo_y.resid
    )

    return r, p, len(temp)


def prueba_adf(serie, nombre):
    """
    Ejecuta la prueba Augmented Dickey-Fuller.
    H0: la serie presenta raíz unitaria.
    H1: la serie es estacionaria.
    """

    serie = serie.dropna()

    resultado = adfuller(
        serie,
        autolag="AIC"
    )

    return {
        "Variable": nombre,
        "ADF": resultado[0],
        "p_valor": resultado[1],
        "rezagos": resultado[2],
        "N": resultado[3],
        "critico_1%": resultado[4]["1%"],
        "critico_5%": resultado[4]["5%"],
        "critico_10%": resultado[4]["10%"],
    }


# ============================================================
# 3. CARGA Y VERIFICACIÓN DE DATOS
# ============================================================

# El análisis utiliza únicamente la base procesada.

if not RUTA_DATOS.exists():
    raise FileNotFoundError(
        f"No se encontró la base procesada: {RUTA_DATOS}"
    )


df = pd.read_csv(
    RUTA_DATOS,
    sep=";",
    parse_dates=["fecha"]
)

df = (
    df
    .sort_values(
        ["banco", "fecha"]
    )
    .reset_index(drop=True)
)


columnas_requeridas = [
    "fecha",
    "banco",
    "atrasada_neta",
    "atrasada_neta_sistema",
    "pbi",
    "inflacion",
    "tasa_activa",
    "tasa_pasiva",
    "spread",
    "cartera_total",
]


faltan_columnas = [
    columna
    for columna in columnas_requeridas
    if columna not in df.columns
]


if faltan_columnas:
    raise ValueError(
        f"Faltan columnas necesarias: {faltan_columnas}"
    )


periodo = (
    f"{df['fecha'].min().year}-"
    f"{df['fecha'].max().year}"
)


# Las variables macroeconómicas se repiten por banco.
# Se crea una observación única por mes para el análisis temporal.

mensual = (
    df
    .drop_duplicates("fecha")
    [
        [
            "fecha",
            "atrasada_neta_sistema",
            "pbi",
            "inflacion",
            "tasa_activa",
            "tasa_pasiva",
            "spread",
            "cartera_total",
        ]
    ]
    .sort_values("fecha")
    .reset_index(drop=True)
)


registrar("=" * 70)

registrar(
    f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | "
    f"04_analisis | "
    f"{len(df)} observaciones | "
    f"{df['banco'].nunique()} bancos | "
    f"{periodo}"
)

registrar("=" * 70)


# ============================================================
# 4. TRANSFORMACIONES
# ============================================================

# Se calcula el logaritmo de la cartera total.

if (mensual["cartera_total"] <= 0).any():
    raise ValueError(
        "cartera_total contiene valores <= 0."
    )


mensual["ln_cartera"] = np.log(
    mensual["cartera_total"]
)

df["ln_cartera"] = np.log(
    df["cartera_total"]
)


# Se crean rezagos del PBI para analizar posibles efectos retardados.

mensual["pbi_lag3"] = mensual["pbi"].shift(3)
mensual["pbi_lag6"] = mensual["pbi"].shift(6)
mensual["pbi_lag12"] = mensual["pbi"].shift(12)


# Primeras diferencias de las series no estacionarias en niveles.

mensual["d_atrasada"] = (
    mensual["atrasada_neta_sistema"].diff()
)

mensual["d_spread"] = (
    mensual["spread"].diff()
)


# Los rezagos del PBI se incorporan al panel mediante la fecha.

df = df.merge(
    mensual[
        [
            "fecha",
            "pbi_lag3",
            "pbi_lag6",
            "pbi_lag12",
        ]
    ],
    on="fecha",
    how="left"
)


# ============================================================
# 5. ESTADÍSTICOS DESCRIPTIVOS
# ============================================================

# Resume las principales variables del estudio.

registrar(
    "--- ESTADÍSTICOS DESCRIPTIVOS ---"
)


tabla_descriptivos = pd.DataFrame(
    [
        resumen_variable(
            "Cartera atrasada neta por banco (%)",
            df["atrasada_neta"]
        ),
        resumen_variable(
            "Cartera atrasada neta del sistema (%)",
            mensual["atrasada_neta_sistema"]
        ),
        resumen_variable(
            "PBI",
            mensual["pbi"]
        ),
        resumen_variable(
            "Inflación",
            mensual["inflacion"]
        ),
        resumen_variable(
            "Tasa activa",
            mensual["tasa_activa"]
        ),
        resumen_variable(
            "Tasa pasiva",
            mensual["tasa_pasiva"]
        ),
        resumen_variable(
            "Spread",
            mensual["spread"]
        ),
        resumen_variable(
            "Crédito total",
            mensual["cartera_total"]
        ),
    ]
)


tabla_descriptivos.to_csv(
    CARPETA_SALIDAS
    / "estadisticos_descriptivos.csv",
    index=False,
    sep=";",
    decimal=","
)


# ============================================================
# 6. MATRIZ DE CORRELACIONES
# ============================================================

# Calcula correlaciones sobre la serie mensual única.

variables_corr = [
    "atrasada_neta_sistema",
    "pbi",
    "inflacion",
    "tasa_activa",
    "tasa_pasiva",
    "spread",
    "cartera_total",
]


matriz_corr = mensual[
    variables_corr
].corr(method="pearson")


matriz_corr.to_csv(
    CARPETA_SALIDAS
    / "matriz_correlaciones.csv"
)


# ============================================================
# 7. CORRELACIONES DE PEARSON
# ============================================================

# Calcula la asociación lineal con la morosidad y su p-valor.

registrar(
    "--- CORRELACIONES DE PEARSON ---"
)


resultados_pearson = []


for variable in [
    "pbi",
    "inflacion",
    "tasa_activa",
    "tasa_pasiva",
    "spread",
    "cartera_total",
]:

    r, p, n = correlacion_pearson(
        mensual["atrasada_neta_sistema"],
        mensual[variable]
    )

    resultados_pearson.append(
        {
            "Variable_dependiente":
                "atrasada_neta_sistema",
            "Variable_explicativa":
                variable,
            "Pearson_r":
                r,
            "p_valor":
                p,
            "N":
                n,
        }
    )


tabla_pearson = pd.DataFrame(
    resultados_pearson
)


tabla_pearson.to_csv(
    CARPETA_SALIDAS
    / "correlaciones_pearson_pvalores.csv",
    index=False,
    sep=";",
    decimal=","
)


# ============================================================
# 8. PBI CONTEMPORÁNEO Y REZAGOS
# ============================================================

# Compara el PBI actual con rezagos de 3, 6 y 12 meses.

registrar(
    "--- CORRELACIONES PBI Y REZAGOS ---"
)


resultados_rezagos = []


for variable in [
    "pbi",
    "pbi_lag3",
    "pbi_lag6",
    "pbi_lag12",
]:

    r, p, n = correlacion_pearson(
        mensual["atrasada_neta_sistema"],
        mensual[variable]
    )

    resultados_rezagos.append(
        {
            "PBI": variable,
            "Pearson_r": r,
            "p_valor": p,
            "N": n,
        }
    )


tabla_rezagos = pd.DataFrame(
    resultados_rezagos
)


tabla_rezagos.to_csv(
    CARPETA_SALIDAS
    / "correlaciones_pbi_rezagos.csv",
    index=False,
    sep=";",
    decimal=","
)


# ============================================================
# 9. CORRELACIÓN PARCIAL
# ============================================================

# Evalúa PBI y morosidad controlando inflación, spread y cartera.

registrar(
    "--- CORRELACIÓN PARCIAL ---"
)


r_parcial, p_parcial, n_parcial = (
    correlacion_parcial(
        mensual,
        "atrasada_neta_sistema",
        "pbi",
        [
            "inflacion",
            "spread",
            "ln_cartera",
        ]
    )
)


tabla_correlacion_parcial = pd.DataFrame(
    [
        {
            "Variable_X":
                "atrasada_neta_sistema",
            "Variable_Y":
                "pbi",
            "Controles":
                "inflacion, spread, ln_cartera",
            "Correlacion_parcial":
                r_parcial,
            "p_valor":
                p_parcial,
            "N":
                n_parcial,
        }
    ]
)


tabla_correlacion_parcial.to_csv(
    CARPETA_SALIDAS
    / "correlacion_parcial.csv",
    index=False,
    sep=";",
    decimal=","
)


# ============================================================
# 10. RESUMEN POR BANCO
# ============================================================

# Calcula estadísticas de atrasada_neta para cada entidad.

tabla_bancos = (
    df
    .groupby("banco")["atrasada_neta"]
    .agg(
        meses="count",
        media="mean",
        mediana="median",
        desv_est="std",
        minimo="min",
        maximo="max",
    )
    .round(3)
    .sort_values(
        "media",
        ascending=False
    )
)


tabla_bancos.to_csv(
    CARPETA_SALIDAS
    / "tabla_por_banco.csv"
)


# ============================================================
# 11. MODELO A — TOTAL DEL SISTEMA
# ============================================================

# Estima morosidad en función de PBI, inflación, spread y cartera.
# Utiliza errores HAC Newey-West con 12 rezagos.

registrar(
    "--- MODELO A: SISTEMA BANCARIO ---"
)


modelo_a = smf.ols(
    """
    atrasada_neta_sistema
    ~ pbi
    + inflacion
    + spread
    + ln_cartera
    """,
    data=mensual
).fit(
    cov_type="HAC",
    cov_kwds={
        "maxlags": 12
    }
)


# Modelo MCO auxiliar para las pruebas de diagnóstico.

modelo_a_mco = smf.ols(
    """
    atrasada_neta_sistema
    ~ pbi
    + inflacion
    + spread
    + ln_cartera
    """,
    data=mensual
).fit()


# ============================================================
# 12. MODELOS CON REZAGOS DEL PBI
# ============================================================

# Reestima el modelo con PBI contemporáneo y rezagado.

modelos_rezagos = {}


for nombre, variable in {
    "PBI contemporaneo":
        "pbi",
    "PBI rezago 3 meses":
        "pbi_lag3",
    "PBI rezago 6 meses":
        "pbi_lag6",
    "PBI rezago 12 meses":
        "pbi_lag12",
}.items():

    formula = (
        "atrasada_neta_sistema"
        f" ~ {variable}"
        " + inflacion"
        " + spread"
        " + ln_cartera"
    )

    modelos_rezagos[nombre] = (
        smf.ols(
            formula,
            data=mensual
        )
        .fit(
            cov_type="HAC",
            cov_kwds={
                "maxlags": 12
            }
        )
    )


resumen_modelos_rezagos = []


for nombre, modelo in modelos_rezagos.items():

    variable_pbi = (
        "pbi"
        if nombre == "PBI contemporaneo"
        else {
            "PBI rezago 3 meses":
                "pbi_lag3",
            "PBI rezago 6 meses":
                "pbi_lag6",
            "PBI rezago 12 meses":
                "pbi_lag12",
        }[nombre]
    )

    resumen_modelos_rezagos.append(
        {
            "Modelo": nombre,
            "Variable_PBI": variable_pbi,
            "Coeficiente":
                modelo.params[variable_pbi],
            "Error_estandar":
                modelo.bse[variable_pbi],
            "p_valor":
                modelo.pvalues[variable_pbi],
            "R2":
                modelo.rsquared,
            "N":
                int(modelo.nobs),
        }
    )


pd.DataFrame(
    resumen_modelos_rezagos
).to_csv(
    CARPETA_SALIDAS
    / "modelos_pbi_rezagos.csv",
    index=False,
    sep=";",
    decimal=","
)


# ============================================================
# 13. MODELO B — PANEL CON EFECTOS FIJOS
# ============================================================

# Controla diferencias permanentes entre bancos y utiliza
# errores estándar agrupados por entidad.

registrar(
    "--- MODELO B: PANEL BANCARIO ---"
)


grupos_banco = pd.factorize(
    df["banco"]
)[0]


modelo_b = smf.ols(
    """
    atrasada_neta
    ~ pbi
    + inflacion
    + spread
    + ln_cartera
    + C(banco)
    """,
    data=df
).fit(
    cov_type="cluster",
    cov_kwds={
        "groups":
            grupos_banco
    }
)


# ============================================================
# 14. VIF
# ============================================================

# Evalúa multicolinealidad entre las variables explicativas.

registrar(
    "--- DIAGNÓSTICO VIF ---"
)


variables_vif = [
    "pbi",
    "inflacion",
    "spread",
    "ln_cartera",
]


datos_vif = mensual[
    variables_vif
].dropna().copy()


X_vif = sm.add_constant(
    datos_vif
)


tabla_vif = pd.DataFrame(
    {
        "Variable":
            X_vif.columns,
        "VIF":
            [
                variance_inflation_factor(
                    X_vif.values,
                    i
                )
                for i in range(
                    X_vif.shape[1]
                )
            ],
    }
)


tabla_vif.to_csv(
    CARPETA_SALIDAS
    / "diagnostico_vif.csv",
    index=False,
    sep=";",
    decimal=","
)


# ============================================================
# 15. BREUSCH-PAGAN
# ============================================================

# Evalúa heterocedasticidad.
# H0: la varianza de los errores es constante.

bp = het_breuschpagan(
    modelo_a_mco.resid,
    modelo_a_mco.model.exog
)


tabla_bp = pd.DataFrame(
    [
        {
            "Estadistico_LM": bp[0],
            "p_valor_LM": bp[1],
            "Estadistico_F": bp[2],
            "p_valor_F": bp[3],
        }
    ]
)


tabla_bp.to_csv(
    CARPETA_SALIDAS
    / "diagnostico_breusch_pagan.csv",
    index=False,
    sep=";",
    decimal=","
)


# ============================================================
# 16. BREUSCH-GODFREY
# ============================================================

# Evalúa autocorrelación serial hasta 12 rezagos.
# H0: no existe autocorrelación.

bg = acorr_breusch_godfrey(
    modelo_a_mco,
    nlags=12
)


tabla_bg = pd.DataFrame(
    [
        {
            "Estadistico_LM": bg[0],
            "p_valor_LM": bg[1],
            "Estadistico_F": bg[2],
            "p_valor_F": bg[3],
        }
    ]
)


tabla_bg.to_csv(
    CARPETA_SALIDAS
    / "diagnostico_breusch_godfrey.csv",
    index=False,
    sep=";",
    decimal=","
)


# ============================================================
# 17. JARQUE-BERA
# ============================================================

# Evalúa normalidad de los residuos.
# H0: los residuos siguen una distribución normal.

jb = jarque_bera(
    modelo_a_mco.resid
)


tabla_jb = pd.DataFrame(
    [
        {
            "Jarque_Bera": jb[0],
            "p_valor": jb[1],
            "Asimetria": jb[2],
            "Curtosis": jb[3],
        }
    ]
)


tabla_jb.to_csv(
    CARPETA_SALIDAS
    / "diagnostico_jarque_bera.csv",
    index=False,
    sep=";",
    decimal=","
)


# ============================================================
# 18. PRUEBAS ADF EN NIVELES
# ============================================================

# Evalúa estacionariedad de las principales series.
# H0: la serie presenta raíz unitaria.

registrar(
    "--- PRUEBAS ADF EN NIVELES ---"
)


tabla_adf = pd.DataFrame(
    [
        prueba_adf(
            mensual["atrasada_neta_sistema"],
            "atrasada_neta_sistema"
        ),
        prueba_adf(
            mensual["pbi"],
            "pbi"
        ),
        prueba_adf(
            mensual["inflacion"],
            "inflacion"
        ),
        prueba_adf(
            mensual["spread"],
            "spread"
        ),
        prueba_adf(
            mensual["ln_cartera"],
            "ln_cartera"
        ),
    ]
)


tabla_adf.to_csv(
    CARPETA_SALIDAS
    / "pruebas_adf.csv",
    index=False,
    sep=";",
    decimal=","
)


# ============================================================
# 19. ADF EN PRIMERAS DIFERENCIAS
# ============================================================

# Verifica si las series no estacionarias en niveles se vuelven
# estacionarias después de aplicar una primera diferencia.

registrar(
    "--- PRUEBAS ADF EN PRIMERAS DIFERENCIAS ---"
)


tabla_adf_diferencias = pd.DataFrame(
    [
        prueba_adf(
            mensual["d_atrasada"],
            "d_atrasada"
        ),
        prueba_adf(
            mensual["d_spread"],
            "d_spread"
        ),
    ]
)


tabla_adf_diferencias.to_csv(
    CARPETA_SALIDAS
    / "pruebas_adf_diferencias.csv",
    index=False,
    sep=";",
    decimal=","
)


# ============================================================
# 20. ADF DE LOS RESIDUOS
# ============================================================

# Diagnóstico auxiliar de estacionariedad de los residuos del
# modelo en niveles. No se interpreta como prueba definitiva
# de cointegración.

resultado_adf_residuos = prueba_adf(
    pd.Series(modelo_a_mco.resid),
    "residuos_modelo_niveles"
)


tabla_adf_residuos = pd.DataFrame(
    [
        resultado_adf_residuos
    ]
)


tabla_adf_residuos.to_csv(
    CARPETA_SALIDAS
    / "diagnostico_adf_residuos.csv",
    index=False,
    sep=";",
    decimal=","
)


# ============================================================
# 21. MODELO C — ROBUSTEZ DE CORTO PLAZO
# ============================================================

# La morosidad y el spread entran en primeras diferencias.
# Este modelo analiza la relación de corto plazo.

registrar(
    "--- MODELO C: ROBUSTEZ EN PRIMERAS DIFERENCIAS ---"
)


modelo_c = smf.ols(
    """
    d_atrasada
    ~ pbi
    + inflacion
    + d_spread
    + ln_cartera
    """,
    data=mensual
).fit(
    cov_type="HAC",
    cov_kwds={
        "maxlags": 12
    }
)


tabla_modelo_c = pd.DataFrame(
    {
        "Variable":
            modelo_c.params.index,
        "Coeficiente":
            modelo_c.params.values,
        "Error_estandar":
            modelo_c.bse.values,
        "p_valor":
            modelo_c.pvalues.values,
    }
)


tabla_modelo_c["R2"] = np.nan
tabla_modelo_c["N"] = np.nan

tabla_modelo_c.loc[
    tabla_modelo_c.index[0],
    "R2"
] = modelo_c.rsquared

tabla_modelo_c.loc[
    tabla_modelo_c.index[0],
    "N"
] = int(modelo_c.nobs)


tabla_modelo_c.to_csv(
    CARPETA_SALIDAS
    / "modelo_robustez_diferencias.csv",
    index=False,
    sep=";",
    decimal=","
)


# ============================================================
# 22. RESULTADOS ECONOMÉTRICOS
# ============================================================

# Guarda los modelos completos en un archivo de texto.

with open(
    CARPETA_SALIDAS
    / "regresion_morosidad.txt",
    "w",
    encoding="utf-8"
) as f:

    f.write(
        "MODELO A: TOTAL DEL SISTEMA BANCARIO\n"
    )

    f.write(
        "Errores estándar HAC Newey-West "
        "con 12 rezagos\n\n"
    )

    f.write(
        modelo_a.summary().as_text()
    )

    f.write(
        "\n\n"
        + "=" * 80
        + "\n"
    )

    f.write(
        "MODELOS CON REZAGOS DEL PBI\n"
    )

    for nombre, modelo in modelos_rezagos.items():

        f.write(
            "\n\n"
            + nombre
            + "\n"
        )

        f.write(
            modelo.summary().as_text()
        )

    f.write(
        "\n\n"
        + "=" * 80
        + "\n"
    )

    f.write(
        "MODELO B: PANEL CON EFECTOS FIJOS POR BANCO\n"
    )

    f.write(
        "Errores estándar agrupados por banco\n\n"
    )

    f.write(
        modelo_b.summary().as_text()
    )

    f.write(
        "\n\n"
        + "=" * 80
        + "\n"
    )

    f.write(
        "MODELO C: ROBUSTEZ DE CORTO PLAZO\n"
    )

    f.write(
        "Variable dependiente: primera diferencia de "
        "atrasada_neta_sistema\n"
    )

    f.write(
        "Errores estándar HAC Newey-West "
        "con 12 rezagos\n\n"
    )

    f.write(
        modelo_c.summary().as_text()
    )


# ============================================================
# 23. FIGURA 1 — MOROSIDAD Y PBI
# ============================================================

fig, ax1 = plt.subplots(
    figsize=(12, 6)
)

ax1.plot(
    mensual["fecha"],
    mensual["atrasada_neta_sistema"],
    linewidth=2
)

ax1.set_xlabel("Fecha")

ax1.set_ylabel(
    "Cartera atrasada neta del sistema (%)"
)

ax1.grid(
    True,
    alpha=0.3
)


ax2 = ax1.twinx()

ax2.plot(
    mensual["fecha"],
    mensual["pbi"],
    linewidth=1.5,
    linestyle="--"
)

ax2.set_ylabel(
    "PBI (variación % interanual)"
)


plt.title(
    f"Cartera atrasada neta del sistema y PBI - Perú {periodo}",
    fontsize=13,
    fontweight="bold"
)

fig.tight_layout()

plt.savefig(
    CARPETA_SALIDAS
    / "figura_01_morosidad_vs_pbi.png",
    dpi=300,
    bbox_inches="tight"
)

plt.close()


# ============================================================
# 24. FIGURA 2 — TASAS E INFLACIÓN
# ============================================================

fig, ax = plt.subplots(
    figsize=(12, 6)
)

ax.plot(
    mensual["fecha"],
    mensual["tasa_activa"],
    linewidth=2,
    label="Tasa activa"
)

ax.plot(
    mensual["fecha"],
    mensual["tasa_pasiva"],
    linewidth=2,
    label="Tasa pasiva"
)

ax.plot(
    mensual["fecha"],
    mensual["spread"],
    linewidth=2,
    linestyle="--",
    label="Spread"
)

ax.plot(
    mensual["fecha"],
    mensual["inflacion"],
    linewidth=1.5,
    linestyle=":",
    label="Inflación"
)

ax.set_xlabel("Fecha")
ax.set_ylabel("Porcentaje")

ax.set_title(
    f"Tasas de interés, spread e inflación - Perú {periodo}",
    fontsize=13,
    fontweight="bold"
)

ax.legend()
ax.grid(True, alpha=0.3)

plt.tight_layout()

plt.savefig(
    CARPETA_SALIDAS
    / "figura_02_tasas_y_spread.png",
    dpi=300,
    bbox_inches="tight"
)

plt.close()


# ============================================================
# 25. FIGURA 3 — CRÉDITO TOTAL
# ============================================================

fig, ax = plt.subplots(
    figsize=(12, 6)
)

ax.plot(
    mensual["fecha"],
    mensual["cartera_total"],
    linewidth=2
)

ax.fill_between(
    mensual["fecha"],
    mensual["cartera_total"],
    alpha=0.3
)

ax.set_xlabel("Fecha")

ax.set_ylabel(
    "Crédito total (millones de S/)"
)

ax.set_title(
    f"Evolución del crédito total - Perú {periodo}",
    fontsize=13,
    fontweight="bold"
)

ax.grid(True, alpha=0.3)

plt.tight_layout()

plt.savefig(
    CARPETA_SALIDAS
    / "figura_03_cartera_creditos.png",
    dpi=300,
    bbox_inches="tight"
)

plt.close()


# ============================================================
# 26. FIGURA 4 — MATRIZ DE CORRELACIONES
# ============================================================

fig, ax = plt.subplots(
    figsize=(10, 8)
)

sns.heatmap(
    matriz_corr,
    annot=True,
    center=0,
    fmt=".2f",
    square=True,
    linewidths=0.5,
    ax=ax,
    cbar_kws={
        "shrink": 0.8
    }
)

plt.title(
    "Matriz de correlaciones de la serie mensual",
    fontsize=13,
    fontweight="bold"
)

plt.tight_layout()

plt.savefig(
    CARPETA_SALIDAS
    / "figura_04_heatmap_correlaciones.png",
    dpi=300,
    bbox_inches="tight"
)

plt.close()


# ============================================================
# 27. FIGURA 5 — DISPERSIÓN PBI Y MOROSIDAD EN NIVELES
# ============================================================

# Regresión simple utilizada únicamente como apoyo gráfico.

simple = smf.ols(
    """
    atrasada_neta_sistema
    ~ pbi
    """,
    data=mensual
).fit()


fig, ax = plt.subplots(
    figsize=(10, 6)
)

ax.scatter(
    mensual["pbi"],
    mensual["atrasada_neta_sistema"],
    alpha=0.6,
    s=40,
    label="Meses"
)


orden = (
    mensual["pbi"]
    .sort_values()
    .index
)


ax.plot(
    mensual.loc[
        orden,
        "pbi"
    ],
    simple.fittedvalues.loc[
        orden
    ],
    linewidth=2,
    label="Recta MCO"
)


ax.set_xlabel(
    "PBI (variación % interanual)"
)

ax.set_ylabel(
    "Cartera atrasada neta del sistema (%)"
)

ax.set_title(
    "PBI y cartera atrasada neta del sistema",
    fontsize=13,
    fontweight="bold"
)


ax.text(
    0.05,
    0.95,
    (
        f"Coef. PBI = "
        f"{simple.params['pbi']:.3f}\n"
        f"R² = "
        f"{simple.rsquared:.3f}"
    ),
    transform=ax.transAxes,
    va="top",
    bbox=dict(
        boxstyle="round",
        alpha=0.3
    )
)

ax.legend()
ax.grid(True, alpha=0.3)

plt.tight_layout()

plt.savefig(
    CARPETA_SALIDAS
    / "figura_05_regresion_morosidad_pbi.png",
    dpi=300,
    bbox_inches="tight"
)

plt.close()


# ============================================================
# 28. FIGURA 6 — DISTRIBUCIÓN POR BANCO
# ============================================================

fig, ax = plt.subplots(
    figsize=(12, 6)
)


orden_bancos = (
    tabla_bancos
    .index
    .tolist()
)


sns.boxplot(
    data=df,
    x="banco",
    y="atrasada_neta",
    order=orden_bancos,
    ax=ax
)


ax.axhline(
    0,
    linewidth=1,
    linestyle="--"
)

ax.set_xlabel("Banco")

ax.set_ylabel(
    "Cartera atrasada neta / colocaciones netas (%)"
)

ax.set_title(
    f"Distribución de la cartera atrasada neta por banco - Perú {periodo}",
    fontsize=13,
    fontweight="bold"
)

plt.xticks(
    rotation=45,
    ha="right"
)

plt.tight_layout()

plt.savefig(
    CARPETA_SALIDAS
    / "figura_06_distribucion_por_banco.png",
    dpi=300,
    bbox_inches="tight"
)

plt.close()


# ============================================================
# 29. FIGURA 7 — PBI Y REZAGOS
# ============================================================

# Resume las correlaciones del PBI contemporáneo y rezagado.

fig, ax = plt.subplots(
    figsize=(10, 6)
)

ax.bar(
    tabla_rezagos["PBI"],
    tabla_rezagos["Pearson_r"]
)

ax.axhline(
    0,
    linewidth=1
)

ax.set_xlabel(
    "Horizonte del PBI"
)

ax.set_ylabel(
    "Correlación de Pearson"
)

ax.set_title(
    "Correlación entre cartera atrasada neta y PBI contemporáneo y rezagado",
    fontsize=13,
    fontweight="bold"
)

plt.xticks(
    rotation=20
)

plt.tight_layout()

plt.savefig(
    CARPETA_SALIDAS
    / "figura_07_correlaciones_pbi_rezagos.png",
    dpi=300,
    bbox_inches="tight"
)

plt.close()


# ============================================================
# 30. FIGURA 8 — CAMBIO DE MOROSIDAD Y PBI
# ============================================================

# Representa la relación descriptiva entre el PBI y el cambio
# mensual de la cartera atrasada neta utilizado en el Modelo C.

datos_corto_plazo = mensual[
    [
        "pbi",
        "d_atrasada"
    ]
].dropna().copy()


modelo_simple_c = smf.ols(
    """
    d_atrasada
    ~ pbi
    """,
    data=datos_corto_plazo
).fit()


fig, ax = plt.subplots(
    figsize=(10, 6)
)


ax.scatter(
    datos_corto_plazo["pbi"],
    datos_corto_plazo["d_atrasada"],
    alpha=0.6,
    s=40,
    label="Meses"
)


orden_c = (
    datos_corto_plazo["pbi"]
    .sort_values()
    .index
)


ax.plot(
    datos_corto_plazo.loc[
        orden_c,
        "pbi"
    ],
    modelo_simple_c.fittedvalues.loc[
        orden_c
    ],
    linewidth=2,
    label="Recta MCO"
)


ax.axhline(
    0,
    linewidth=1,
    linestyle="--"
)


ax.set_xlabel(
    "PBI (variación % interanual)"
)

ax.set_ylabel(
    "Cambio mensual de la cartera atrasada neta (p.p.)"
)

ax.set_title(
    "PBI y cambio mensual de la cartera atrasada neta",
    fontsize=13,
    fontweight="bold"
)


ax.text(
    0.05,
    0.95,
    (
        f"Coef. PBI = "
        f"{modelo_simple_c.params['pbi']:.4f}\n"
        f"R² = "
        f"{modelo_simple_c.rsquared:.3f}"
    ),
    transform=ax.transAxes,
    va="top",
    bbox=dict(
        boxstyle="round",
        alpha=0.3
    )
)


ax.legend()
ax.grid(
    True,
    alpha=0.3
)

plt.tight_layout()

plt.savefig(
    CARPETA_SALIDAS
    / "figura_08_cambio_morosidad_vs_pbi.png",
    dpi=300,
    bbox_inches="tight"
)

plt.close()


# ============================================================
# 31. RESULTADOS PRINCIPALES
# ============================================================

# Muestra indicadores básicos para verificar la ejecución.

registrar(
    "--- RESULTADOS PRINCIPALES ---"
)

registrar(
    f"Modelo A | "
    f"N={int(modelo_a.nobs)} | "
    f"R2={modelo_a.rsquared:.4f}"
)

registrar(
    f"Modelo B | "
    f"N={int(modelo_b.nobs)} | "
    f"R2={modelo_b.rsquared:.4f}"
)

registrar(
    f"Modelo C | "
    f"N={int(modelo_c.nobs)} | "
    f"R2={modelo_c.rsquared:.4f}"
)

registrar(
    f"Modelo C | PBI coef="
    f"{modelo_c.params['pbi']:.6f} | "
    f"p={modelo_c.pvalues['pbi']:.6f}"
)

registrar(
    f"Correlación parcial PBI-morosidad | "
    f"r={r_parcial:.4f} | "
    f"p={p_parcial:.6f}"
)

registrar(
    f"Archivos generados en: "
    f"{CARPETA_SALIDAS}"
)


# ============================================================
# 32. FINALIZACIÓN
# ============================================================

# La interpretación económica se desarrolla en el artículo.

registrar("=" * 70)

registrar(
    "04_analisis.py COMPLETADO CORRECTAMENTE"
)

registrar("=" * 70)