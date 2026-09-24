# Nombres y apellidos: Nils Georgia Chavez Vilchez
# Código de matrícula: 2024200493L
# Tema: Morosidad y calidad de cartera del sistema bancario peruano frente al ciclo económico
# Fecha de extracción: 2026-09-24

"""
Estimaciones, tablas y figuras del artículo, generadas SOLO a partir del archivo procesado.

Variable endógena: atrasada_neta = cartera atrasada neta / colocaciones netas (%), por banco y mes.
  (Es una medida NETA de provisiones: es negativa cuando las provisiones superan la cartera atrasada.)
Variables exógenas: pbi (var. % interanual), inflacion (var. % 12 meses), spread (p.p.), cartera_total (millones S/).

Salidas en /salidas: 6 figuras (.png), 4 tablas (.csv) y regresion_morosidad.txt.
"""

from datetime import datetime
from pathlib import Path

import warnings
import matplotlib
warnings.filterwarnings("ignore", message="covariance of constraints")   # aviso inocuo: pocos grupos (15) para el test F agrupado
matplotlib.use("Agg")   # backend sin ventana: los gráficos solo se guardan en archivo
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
import statsmodels.formula.api as smf

CODIGO_MATRICULA = "2024200493L"
RUTA_DATOS = Path(f"datos_procesados/datos_procesados_{CODIGO_MATRICULA}.csv")
CARPETA_SALIDAS = Path("salidas")
ARCHIVO_LOG = Path("log_ejecucion.txt")
CARPETA_SALIDAS.mkdir(exist_ok=True)

# Quiebre estructural de la serie fuente: en ene-2018 TODOS los bancos saltan a la vez (p. ej. BCP -0,21 -> 3,02),
# lo que indica un cambio de definición/metodología en el BCRP y no un shock económico. Se controla con una ficticia.
FECHA_QUIEBRE = "2018-01-01"

# ============================================================
# 1. Carga de datos
# ============================================================
df = pd.read_csv(RUTA_DATOS, sep=";", parse_dates=["fecha"])
df = df.sort_values(["banco", "fecha"]).reset_index(drop=True)
periodo = f"{df['fecha'].min().year}-{df['fecha'].max().year}"

# Serie mensual única (variables macro y del sistema): una fila por fecha
mensual = (df.drop_duplicates("fecha")
             [["fecha", "atrasada_neta_sistema", "pbi", "inflacion", "tasa_activa",
               "tasa_pasiva", "spread", "cartera_total"]]
             .sort_values("fecha").reset_index(drop=True))

print("=" * 70)
print(f"ANÁLISIS | {len(df)} observaciones | {df['banco'].nunique()} bancos | {periodo}")
print("=" * 70)

# ============================================================
# 2. Tablas descriptivas
# ============================================================
# Tabla 1: estadísticos descriptivos del panel completo
df.drop(columns="Id").describe().to_csv(CARPETA_SALIDAS / "estadisticos_descriptivos.csv")

# Tabla 2: matriz de correlaciones (serie mensual, evita repetir las variables macro por banco)
variables = ["atrasada_neta_sistema", "pbi", "inflacion", "tasa_activa", "tasa_pasiva", "spread", "cartera_total"]
matriz_corr = mensual[variables].corr()
matriz_corr.to_csv(CARPETA_SALIDAS / "matriz_correlaciones.csv")

# Tabla 3: resumen de variables (macro sobre la serie mensual; banco sobre el panel)
def resumen(nombre, serie):
    return {"Variable": nombre, "N": int(serie.count()), "Media": serie.mean(),
            "Desv. Est.": serie.std(), "Mínimo": serie.min(), "Máximo": serie.max()}

tabla_resumen = pd.DataFrame([
    resumen("Cartera atrasada neta por banco (%)", df["atrasada_neta"]),
    resumen("Cartera atrasada neta del sistema (%)", mensual["atrasada_neta_sistema"]),
    resumen("PBI (var. % interanual)", mensual["pbi"]),
    resumen("Inflación (var. % 12 meses)", mensual["inflacion"]),
    resumen("Tasa activa MN (%)", mensual["tasa_activa"]),
    resumen("Tasa pasiva MN (%)", mensual["tasa_pasiva"]),
    resumen("Spread (p.p.)", mensual["spread"]),
    resumen("Crédito total (millones S/)", mensual["cartera_total"]),
])
tabla_resumen.to_csv(CARPETA_SALIDAS / "tabla_resumen_variables.csv", index=False, sep=";", decimal=",")

# Tabla 4: cartera atrasada neta por banco (panel no balanceado)
tabla_bancos = (df.groupby("banco")["atrasada_neta"]
                  .agg(meses="count", media="mean", desv_est="std", minimo="min", maximo="max")
                  .round(3).sort_values("media", ascending=False))
tabla_bancos.to_csv(CARPETA_SALIDAS / "tabla_por_banco.csv")
print("\nTabla por banco:\n", tabla_bancos)

# ============================================================
# 3. Figuras
# ============================================================
# Figura 1: cartera atrasada neta del sistema vs PBI
fig, ax1 = plt.subplots(figsize=(12, 6))
ax1.plot(mensual["fecha"], mensual["atrasada_neta_sistema"], color="tab:red", linewidth=2)
ax1.set_xlabel("Fecha")
ax1.set_ylabel("Cartera atrasada neta del sistema (%)", color="tab:red")
ax1.axvline(pd.Timestamp(FECHA_QUIEBRE), color="gray", linestyle=":", linewidth=1.5)
ax1.text(pd.Timestamp(FECHA_QUIEBRE), ax1.get_ylim()[0], " Quiebre de la serie (ene-2018)", va="bottom", fontsize=9, color="gray")
ax1.grid(True, alpha=0.3)
ax2 = ax1.twinx()
ax2.plot(mensual["fecha"], mensual["pbi"], color="tab:blue", linewidth=1.5, linestyle="--")
ax2.set_ylabel("PBI (var. % interanual)", color="tab:blue")
plt.title(f"Cartera atrasada neta del sistema bancario vs PBI - Perú {periodo}", fontsize=13, fontweight="bold")
fig.tight_layout()
plt.savefig(CARPETA_SALIDAS / "figura_01_morosidad_vs_pbi.png", dpi=300, bbox_inches="tight")
plt.close()

# Figura 2: tasas, spread e inflación
fig, ax = plt.subplots(figsize=(12, 6))
ax.plot(mensual["fecha"], mensual["tasa_activa"], linewidth=2, label="Tasa activa MN", color="blue")
ax.plot(mensual["fecha"], mensual["tasa_pasiva"], linewidth=2, label="Tasa pasiva MN", color="green")
ax.plot(mensual["fecha"], mensual["spread"], linewidth=2, label="Spread", color="red", linestyle="--")
ax.plot(mensual["fecha"], mensual["inflacion"], linewidth=1.5, label="Inflación (12 meses)", color="black", linestyle=":")
ax.set_xlabel("Fecha")
ax.set_ylabel("Porcentaje")
ax.set_title(f"Tasas de interés, spread e inflación - Perú {periodo}", fontsize=13, fontweight="bold")
ax.legend()
ax.grid(True, alpha=0.3)
plt.savefig(CARPETA_SALIDAS / "figura_02_tasas_y_spread.png", dpi=300, bbox_inches="tight")
plt.close()

# Figura 3: crédito total del sistema bancario
fig, ax = plt.subplots(figsize=(12, 6))
ax.plot(mensual["fecha"], mensual["cartera_total"], linewidth=2, color="purple")
ax.fill_between(mensual["fecha"], mensual["cartera_total"], alpha=0.3, color="purple")
ax.set_xlabel("Fecha")
ax.set_ylabel("Crédito al sector privado (millones S/)")
ax.set_title(f"Crédito del sistema bancario al sector privado - Perú {periodo}", fontsize=13, fontweight="bold")
ax.grid(True, alpha=0.3)
plt.savefig(CARPETA_SALIDAS / "figura_03_cartera_creditos.png", dpi=300, bbox_inches="tight")
plt.close()

# Figura 4: mapa de calor de correlaciones
fig, ax = plt.subplots(figsize=(10, 8))
sns.heatmap(matriz_corr, annot=True, cmap="coolwarm", center=0, fmt=".2f", square=True,
            linewidths=0.5, ax=ax, cbar_kws={"shrink": 0.8})
plt.title("Matriz de correlaciones (serie mensual)", fontsize=13, fontweight="bold")
plt.tight_layout()
plt.savefig(CARPETA_SALIDAS / "figura_04_heatmap_correlaciones.png", dpi=300, bbox_inches="tight")
plt.close()

# ============================================================
# 4. Modelos de regresión
# ============================================================
# Modelo A: serie de tiempo del sistema, errores robustos HAC (Newey-West, 12 rezagos)
mensual["ln_cartera"] = np.log(mensual["cartera_total"])
mensual["post2018"] = (mensual["fecha"] >= FECHA_QUIEBRE).astype(int)
modelo_a = smf.ols("atrasada_neta_sistema ~ pbi + inflacion + spread + ln_cartera + post2018", data=mensual)\
              .fit(cov_type="HAC", cov_kwds={"maxlags": 12})

# Modelo B: panel con efectos fijos por banco y errores agrupados por banco (2 718 observaciones)
df["ln_cartera"] = np.log(df["cartera_total"])
df["post2018"] = (df["fecha"] >= FECHA_QUIEBRE).astype(int)
modelo_b = smf.ols("atrasada_neta ~ pbi + inflacion + spread + ln_cartera + post2018 + C(banco)", data=df)\
              .fit(cov_type="cluster", cov_kwds={"groups": pd.factorize(df["banco"])[0]})

with open(CARPETA_SALIDAS / "regresion_morosidad.txt", "w", encoding="utf-8") as f:
    f.write("MODELO A: serie de tiempo del sistema (errores HAC Newey-West, 12 rezagos)\n")
    f.write(modelo_a.summary().as_text())
    f.write("\n\n\nMODELO B: panel con efectos fijos por banco (errores agrupados por banco)\n")
    f.write(modelo_b.summary().as_text())
print(modelo_a.summary())
print(f"\nModelo B: N={int(modelo_b.nobs)}, R2={modelo_b.rsquared:.3f}")
print(modelo_b.params[["pbi", "inflacion", "spread", "ln_cartera", "post2018"]].round(4))

# Figura 5: dispersión PBI vs cartera atrasada neta del sistema con recta MCO simple
simple = smf.ols("atrasada_neta_sistema ~ pbi", data=mensual).fit()
fig, ax = plt.subplots(figsize=(10, 6))
ax.scatter(mensual["pbi"], mensual["atrasada_neta_sistema"], alpha=0.6, s=40, color="blue", label="Meses")
orden = mensual["pbi"].sort_values().index
ax.plot(mensual.loc[orden, "pbi"], simple.fittedvalues[orden], "r-", linewidth=2, label="Recta MCO")
ax.set_xlabel("PBI (var. % interanual)")
ax.set_ylabel("Cartera atrasada neta del sistema (%)")
ax.set_title("Ciclo económico (PBI) y cartera atrasada neta del sistema", fontsize=13, fontweight="bold")
ax.text(0.05, 0.95, f"y = {simple.params['Intercept']:.3f} {simple.params['pbi']:+.3f}·PBI\nR² = {simple.rsquared:.3f}",
        transform=ax.transAxes, va="top", bbox=dict(boxstyle="round", facecolor="wheat", alpha=0.5))
ax.legend(loc="lower right")
ax.grid(True, alpha=0.3)
plt.savefig(CARPETA_SALIDAS / "figura_05_regresion_morosidad_pbi.png", dpi=300, bbox_inches="tight")
plt.close()

# Figura 6: cartera atrasada neta por banco (distribución)
fig, ax = plt.subplots(figsize=(12, 6))
orden_bancos = tabla_bancos.index.tolist()
sns.boxplot(data=df, x="banco", y="atrasada_neta", order=orden_bancos, ax=ax, color="lightsteelblue")
ax.axhline(0, color="gray", linewidth=1, linestyle="--")
ax.set_xlabel("Banco")
ax.set_ylabel("Cartera atrasada neta / colocaciones netas (%)")
ax.set_title(f"Distribución por banco - Perú {periodo}", fontsize=13, fontweight="bold")
plt.xticks(rotation=45, ha="right")
plt.tight_layout()
plt.savefig(CARPETA_SALIDAS / "figura_06_distribucion_por_banco.png", dpi=300, bbox_inches="tight")
plt.close()

with open(ARCHIVO_LOG, "a", encoding="utf-8") as f:
    f.write(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | 04_analisis | 6 figuras, 4 tablas y regresiones "
            f"generadas en /salidas a partir de {RUTA_DATOS.name}\n")
print("\nANÁLISIS COMPLETADO: resultados en /salidas")
