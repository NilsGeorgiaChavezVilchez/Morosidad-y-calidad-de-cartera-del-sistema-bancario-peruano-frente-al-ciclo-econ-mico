# Nombres y apellidos: Nils Georgia Chavez Vilchez
# Código de matrícula: 2024200493L
# Tema: Morosidad y calidad de cartera del sistema bancario peruano frente al ciclo económico
# Fecha de extracción: 2026-09-24

"""
NOTA: Según el numeral 2.4.1 del sílabo, en la Unidad I solo se requiere 
una vía automatizada obligatoria (API). La segunda vía (scraping SBS) es opcional.
Este script está preparado para la Unidad II.
"""

import requests
from pathlib import Path
import time
from datetime import datetime

FECHA_INICIO = "2010-01-01"
FECHA_CORTE = "2025-12-31"

# Serie adicional del BCRP como vía 2 opcional (descarga programática)
SERIE_ADICIONAL = {
    "ipc": "PN01714AM"
}

URL_BASE = "https://estadisticas.bcrp.gob.pe/estadisticas/series/api"

def descargar_serie(codigo, inicio, fin):
    url = f"{URL_BASE}/{codigo}/csv/{inicio}/{fin}"
    headers = {"User-Agent": "EstudianteUNCP-FinanzasI/1.0 (2024200493L)"}
    
    try:
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        Path("datos_crudos").mkdir(exist_ok=True)
        ruta = Path(f"datos_crudos/bcrp_{codigo}_crudo.csv")
        ruta.write_text(response.text, encoding="utf-8")
        print(f"[OK] {codigo} -> {ruta}")
        time.sleep(1)
        return ruta
    except Exception as e:
        print(f"[ERROR] {codigo}: {e}")
        return None

if __name__ == "__main__":
    print("DESCARGA PROGRAMÁTICA - VÍA 2 (OPCIONAL UNIDAD I)")
    for nombre, codigo in SERIE_ADICIONAL.items():
        print(f"Descargando: {nombre} ({codigo})...")
        descargar_serie(codigo, FECHA_INICIO, FECHA_CORTE)
    print("COMPLETADO")