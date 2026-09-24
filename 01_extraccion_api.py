# Nombres y apellidos: Nils Georgia Chavez Vilchez
# Código de matrícula: 2024200493L
# Tema: Morosidad y calidad de cartera del sistema bancario peruano frente al ciclo económico
# Fecha de extracción: 2026-09-24

import requests
from pathlib import Path
import time
from datetime import datetime

# ============================================================
# PARÁMETROS CONGELADOS (NO CAMBIAR)
# ============================================================
FECHA_INICIO = "2010-01-01"
FECHA_CORTE = "2025-12-31"

# Series del BCRP - VARIABLES MACROECONÓMICAS
SERIES_MACRO = {
    "pbi": "PN01728AM",
    "tasa_activa": "PN07807NM",
    "tasa_pasiva": "PN07816NM",
    "cartera_total": "PN00528MM"
}

# Series del BCRP - MOROSIDAD POR BANCO (15 bancos)
BANCOS = {
    "BCP": "PN07729EM",
    "Interbank": "PN07730EM",
    "Scotiabank": "PN07732EM",
    "Continental": "PN07733EM",
    "Comercio": "PN07734EM",
    "Financiero": "PN07735EM",
    "BanBif": "PN07736EM",
    "MiBanco": "PN07737EM",
    "GNB": "PN07738EM",
    "Falabella": "PN07739EM",
    "Santander": "PN07740EM",
    "Ripley": "PN07741EM",
    "Azteca": "PN07742EM",
    "ICBC": "PN07744EM",
    "Total_Sistema": "PN07746EM"
}

URL_BASE = "https://estadisticas.bcrp.gob.pe/estadisticas/series/api"

def extraer_serie_bcrp(codigo, inicio, fin):
    url = f"{URL_BASE}/{codigo}/csv/{inicio}/{fin}"
    headers = {"User-Agent": "EstudianteUNCP-FinanzasI/1.0 (2024200493L)"}
    
    try:
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        
        Path("datos_crudos").mkdir(exist_ok=True)
        ruta = Path(f"datos_crudos/bcrp_{codigo}_crudo.csv")
        ruta.write_text(response.text, encoding="utf-8")
        
        print(f"[OK] {codigo} -> {ruta} | HTTP {response.status_code}")
        time.sleep(1)
        return ruta
    except Exception as e:
        print(f"[ERROR] {codigo}: {e}")
        return None

if __name__ == "__main__":
    print("=" * 70)
    print("EXTRACCIÓN BCRP - API")
    print(f"Periodo: {FECHA_INICIO} a {FECHA_CORTE}")
    print(f"Bancos: {len(BANCOS)}")
    print(f"Observaciones esperadas: {len(BANCOS)} × 252 meses ≈ {len(BANCOS)*252}")
    print("=" * 70)
    
    log_ejecucion = []
    total_series = len(SERIES_MACRO) + len(BANCOS)
    serie_actual = 0
    
    print("\n--- SERIES MACRO ---")
    for nombre, codigo in SERIES_MACRO.items():
        serie_actual += 1
        print(f"[{serie_actual}/{total_series}] {nombre} ({codigo})...")
        ruta = extraer_serie_bcrp(codigo, FECHA_INICIO, FECHA_CORTE)
        log_ejecucion.append(f"{datetime.now()} | {nombre} | {codigo} | {'OK' if ruta else 'ERROR'}")
    
    print("\n--- MOROSIDAD POR BANCO ---")
    for banco, codigo in BANCOS.items():
        serie_actual += 1
        print(f"[{serie_actual}/{total_series}] {banco} ({codigo})...")
        ruta = extraer_serie_bcrp(codigo, FECHA_INICIO, FECHA_CORTE)
        log_ejecucion.append(f"{datetime.now()} | morosidad_{banco} | {codigo} | {'OK' if ruta else 'ERROR'}")
    
    Path("log_ejecucion.txt").write_text("\n".join(log_ejecucion), encoding="utf-8")
    print("\nEXTRACCIÓN COMPLETADA")