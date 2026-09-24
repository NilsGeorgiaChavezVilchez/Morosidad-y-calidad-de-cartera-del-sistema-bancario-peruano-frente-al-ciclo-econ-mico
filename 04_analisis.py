# Nombres y apellidos: Nils Georgia Chavez Vilchez
# Código de matrícula: 2024200493L
# Tema: Morosidad y calidad de cartera del sistema bancario peruano frente al ciclo económico
# Fecha de extracción: 2026-09-24

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
import statsmodels.api as sm
from statsmodels.regression.linear_model import OLS

Path("salidas").mkdir(exist_ok=True)

codigo_matricula = "2024200493L"
ruta_datos = f"datos_procesados/datos_procesados_{codigo_matricula}.csv"
df = pd.read_csv(ruta_datos)

df['fecha'] = pd.to_datetime(df['fecha'])
df = df.sort_values(['banco', 'fecha']).reset_index(drop=True)

print("=" * 70)
print("ANÁLISIS ESTADÍSTICO")
print(f"Datos: {len(df)} observaciones")
print(f"Periodo: {df['fecha'].min().date()} a {df['fecha'].max().date()}")
print(f"Bancos: {df['banco'].nunique()}")
print("=" * 70)

# 1. Estadísticos descriptivos
estadisticos = df.describe()
estadisticos.to_csv("salidas/estadisticos_descriptivos.csv")
print("\nEstadísticos descriptivos:")
print(estadisticos.round(2))

# 2. Matriz de correlaciones
variables_numericas = df.select_dtypes(include=[np.number]).columns
matriz_corr = df[variables_numericas].corr()
matriz_corr.to_csv("salidas/matriz_correlaciones.csv")
print("\nMatriz de correlaciones:")
print(matriz_corr.round(3))

# 3. Datos agregados por fecha
df_agregado = df.groupby('fecha').agg({
    'morosidad': 'mean',
    'pbi': 'first',
    'tasa_activa': 'first',
    'tasa_pasiva': 'first',
    'spread': 'first',
    'cartera_total': 'first'
}).reset_index()

# 4. Figura 1: Morosidad vs PBI
fig, ax1 = plt.subplots(figsize=(12, 6))
color = 'tab:red'
ax1.set_xlabel('Fecha')
ax1.set_ylabel('Morosidad (%)', color=color)
ax1.plot(df_agregado['fecha'], df_agregado['morosidad'], color=color, linewidth=2, label='Morosidad')
ax1.tick_params(axis='y', labelcolor=color)
ax1.grid(True, alpha=0.3)

ax2 = ax1.twinx()
color = 'tab:blue'
ax2.set_ylabel('PBI (var. % interanual)', color=color)
ax2.plot(df_agregado['fecha'], df_agregado['pbi'], color=color, linewidth=2, linestyle='--', label='PBI')
ax2.tick_params(axis='y', labelcolor=color)

plt.title('Morosidad del Sistema Bancario vs Ciclo Económico (PBI)\nPerú 2005-2025', fontsize=14, fontweight='bold')
fig.tight_layout()
plt.savefig("salidas/figura_01_morosidad_vs_pbi.png", dpi=300, bbox_inches='tight')
plt.close()
print("\n[OK] Figura 1: morosidad_vs_pbi.png")

# 5. Figura 2: Tasas y Spread
fig, ax = plt.subplots(figsize=(12, 6))
ax.plot(df_agregado['fecha'], df_agregado['tasa_activa'], linewidth=2, label='Tasa Activa', color='blue')
ax.plot(df_agregado['fecha'], df_agregado['tasa_pasiva'], linewidth=2, label='Tasa Pasiva', color='green')
ax.plot(df_agregado['fecha'], df_agregado['spread'], linewidth=2, label='Spread', color='red', linestyle='--')
ax.set_xlabel('Fecha')
ax.set_ylabel('Tasa de Interés (%)')
ax.set_title('Evolución de Tasas de Interés y Spread Bancario\nPerú 2005-2025', fontsize=14, fontweight='bold')
ax.legend()
ax.grid(True, alpha=0.3)
plt.savefig("salidas/figura_02_tasas_y_spread.png", dpi=300, bbox_inches='tight')
plt.close()
print("[OK] Figura 2: tasas_y_spread.png")

# 6. Figura 3: Cartera de Créditos
fig, ax = plt.subplots(figsize=(12, 6))
ax.plot(df_agregado['fecha'], df_agregado['cartera_total'], linewidth=2, color='purple')
ax.fill_between(df_agregado['fecha'], df_agregado['cartera_total'], alpha=0.3)
ax.set_xlabel('Fecha')
ax.set_ylabel('Cartera de Créditos (millones S/)')
ax.set_title('Evolución de la Cartera de Créditos del Sistema Bancario\nPerú 2005-2025', fontsize=14, fontweight='bold')
ax.grid(True, alpha=0.3)
plt.savefig("salidas/figura_03_cartera_creditos.png", dpi=300, bbox_inches='tight')
plt.close()
print("[OK] Figura 3: cartera_creditos.png")

# 7. Figura 4: Heatmap de Correlaciones
fig, ax = plt.subplots(figsize=(10, 8))
variables_heatmap = ['morosidad', 'pbi', 'tasa_activa', 'tasa_pasiva', 'spread', 'cartera_total']
matriz_corr_heatmap = df_agregado[variables_heatmap].corr()
sns.heatmap(matriz_corr_heatmap, annot=True, cmap='coolwarm', center=0, 
            fmt='.3f', square=True, linewidths=0.5, ax=ax, cbar_kws={"shrink": 0.8})
plt.title('Matriz de Correlaciones - Variables del Sistema Bancario', fontsize=14, fontweight='bold')
plt.tight_layout()
plt.savefig("salidas/figura_04_heatmap_correlaciones.png", dpi=300, bbox_inches='tight')
plt.close()
print("[OK] Figura 4: heatmap_correlaciones.png")

# 8. Regresión: Morosidad = f(PBI, Spread, Cartera)
print("\n" + "=" * 70)
print("MODELO DE REGRESIÓN: Morosidad = f(PBI, Spread, Cartera)")
print("=" * 70)

X = df_agregado[['pbi', 'spread', 'cartera_total']]
y = df_agregado['morosidad']
X = sm.add_constant(X)
modelo = OLS(y, X).fit()

print(modelo.summary())
with open("salidas/regresion_morosidad.txt", 'w', encoding='utf-8') as f:
    f.write(modelo.summary().as_text())
print("\n[OK] Regresión guardada: regresion_morosidad.txt")

# 9. Figura 5: Dispersión Morosidad vs PBI
fig, ax = plt.subplots(figsize=(10, 6))
ax.scatter(df_agregado['pbi'], df_agregado['morosidad'], alpha=0.6, s=50, color='blue', label='Observaciones')
ax.plot(df_agregado['pbi'], modelo.fittedvalues, 'r-', linewidth=2, label='Línea de regresión')
ax.set_xlabel('PBI (var. % interanual)', fontsize=12)
ax.set_ylabel('Morosidad (%)', fontsize=12)
ax.set_title('Relación entre Ciclo Económico (PBI) y Morosidad Bancaria', fontsize=14, fontweight='bold')
ax.legend()
ax.grid(True, alpha=0.3)
ecuacion = f"Morosidad = {modelo.params['const']:.3f} {modelo.params['pbi']:+.3f}×PBI\nR² = {modelo.rsquared:.4f}"
ax.text(0.05, 0.95, ecuacion, transform=ax.transAxes, fontsize=11, 
        verticalalignment='top', bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
plt.savefig("salidas/figura_05_regresion_morosidad_pbi.png", dpi=300, bbox_inches='tight')
plt.close()
print("[OK] Figura 5: regresion_morosidad_pbi.png")

# 10. Tabla resumen
tabla_resumen = pd.DataFrame({
    'Variable': ['Morosidad', 'PBI', 'Tasa Activa', 'Tasa Pasiva', 'Spread', 'Cartera Total'],
    'Media': [df['morosidad'].mean(), df['pbi'].mean(), df['tasa_activa'].mean(), 
              df['tasa_pasiva'].mean(), df['spread'].mean(), df['cartera_total'].mean()],
    'Desv. Est.': [df['morosidad'].std(), df['pbi'].std(), df['tasa_activa'].std(),
                   df['tasa_pasiva'].std(), df['spread'].std(), df['cartera_total'].std()],
    'Mínimo': [df['morosidad'].min(), df['pbi'].min(), df['tasa_activa'].min(),
               df['tasa_pasiva'].min(), df['spread'].min(), df['cartera_total'].min()],
    'Máximo': [df['morosidad'].max(), df['pbi'].max(), df['tasa_activa'].max(),
               df['tasa_pasiva'].max(), df['spread'].max(), df['cartera_total'].max()]
})
tabla_resumen.to_csv("salidas/tabla_resumen_variables.csv", index=False, decimal=',', sep=';')
print("\n[OK] Tabla resumen guardada: tabla_resumen_variables.csv")

print("\n" + "=" * 70)
print("ANÁLISIS COMPLETADO")
print("=" * 70)