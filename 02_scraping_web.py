# Nombres y apellidos: Nils Georgia Chavez Vilchez
# Código de matrícula: 2024200493L
# Tema: Morosidad y calidad de cartera del sistema bancario peruano frente al ciclo económico
# Fecha de extracción: 2026-09-24

"""
VÍA COMPLEMENTARIA (descarga programática) - opcional en la Unidad I (numeral 2.4.1).

IMPORTANTE (honestidad metodológica): este script NO hace rastreo de HTML. Descarga por código una
serie adicional (IPC de Lima Metropolitana) desde el mismo portal oficial del BCRP. Se declara como
vía complementaria y no como segunda vía de scraping; para la Unidad II se requeriría un rastreo o
descarga programática de otro portal (p. ej. SBS o INEI).

Antes de descargar, el script consulta el robots.txt del portal y respeta pausa de 1 s y User-Agent.
Salida: datos_crudos/bcrp_PN01273PM_crudo.csv (sin editar) y líneas agregadas a log_ejecucion.txt.
"""

import os
import re
import time
from datetime import datetime
from pathlib import Path

import requests

# ============================================================
# PARÁMETROS CONGELADOS (deben coincidir con 01_extraccion_api.py)
# ============================================================
FECHA_INICIO = "2010-01-01"
FECHA_CORTE = "2025-12-31"

URL_PORTAL = "https://estadisticas.bcrp.gob.pe"
URL_BASE = f"{URL_PORTAL}/estadisticas/series/api"
CARPETA_CRUDOS = Path("datos_crudos")
ARCHIVO_LOG = Path("log_ejecucion.txt")

USER_AGENT = os.environ.get("USER_AGENT_SCRAPER", "EstudianteUNCP-FinanzasI/1.0 (2024200493L)")
PAUSA_SEGUNDOS = 1
REINTENTOS = 3

# IPC de Lima Metropolitana, variación % a 12 meses (inflación)
SERIE_COMPLEMENTARIA = {
    "inflacion": "PN01273PM"
}


def registrar(mensaje):
    """Imprime en consola y agrega la línea al log_ejecucion.txt (sin sobrescribir el log de 01)."""
    print(mensaje)
    with open(ARCHIVO_LOG, "a", encoding="utf-8") as f:
        f.write(mensaje + "\n")


def revisar_robots(headers):
    """Consulta /robots.txt y registra qué respondió el portal (numeral 2.4.8)."""
    url = f"{URL_PORTAL}/robots.txt"
    try:
        r = requests.get(url, headers=headers, timeout=30)
        prohibe = r.status_code == 200 and re.search(r"(?im)^\s*Disallow:\s*/estadisticas", r.text) is not None
        ahora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        registrar(f"{ahora} | 02_scraping_web | robots.txt | HTTP {r.status_code} | "
                  f"{'RUTA PROHIBIDA' if prohibe else 'sin restricción para /estadisticas'} | {url}")
        time.sleep(PAUSA_SEGUNDOS)
        return not prohibe
    except requests.RequestException as e:
        registrar(f"[AVISO] No se pudo leer robots.txt ({e}); se continúa con pausa y User-Agent")
        return True


def descargar_serie(nombre, codigo, inicio, fin, headers):
    """Descarga la serie y guarda la respuesta sin editar. Devuelve True si fue exitosa."""
    url = f"{URL_BASE}/{codigo}/csv/{inicio}/{fin}"
    estado, http, filas = "ERROR", "-", 0
    for intento in range(1, REINTENTOS + 1):
        try:
            r = requests.get(url, headers=headers, timeout=30)
            http = r.status_code
            r.raise_for_status()
            texto = r.content.decode("utf-8", errors="replace")
            if not texto.startswith("Mes/"):
                raise ValueError("La respuesta no tiene formato de serie BCRP")
            filas = len(re.findall(r'<br>"', texto))
            CARPETA_CRUDOS.mkdir(exist_ok=True)
            (CARPETA_CRUDOS / f"bcrp_{codigo}_crudo.csv").write_bytes(r.content)
            estado = "OK"
            break
        except (requests.RequestException, ValueError) as e:
            estado = f"ERROR ({type(e).__name__}: {e})"
            time.sleep(PAUSA_SEGUNDOS * intento)
    ahora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    registrar(f"{ahora} | 02_scraping_web | {codigo} | {nombre} | HTTP {http} | filas={filas} | {estado} | {url}")
    time.sleep(PAUSA_SEGUNDOS)
    return estado == "OK"


if __name__ == "__main__":
    registrar("=" * 70)
    registrar("DESCARGA PROGRAMÁTICA COMPLEMENTARIA (opcional en Unidad I)")
    registrar(f"Ventana congelada: {FECHA_INICIO} a {FECHA_CORTE}")
    registrar("=" * 70)
    cabeceras = {"User-Agent": USER_AGENT}
    if revisar_robots(cabeceras):
        for nombre, codigo in SERIE_COMPLEMENTARIA.items():
            descargar_serie(nombre, codigo, FECHA_INICIO, FECHA_CORTE, cabeceras)
    else:
        registrar("[ABORTADO] robots.txt prohíbe la ruta; documentar en incidencias_fuente.md (numeral 2.4.3)")
    registrar("COMPLETADO")
