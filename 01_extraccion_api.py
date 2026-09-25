# Nombres y apellidos: Nils Georgia Chavez Vilchez
# Código de matrícula: 2024200493L
# Tema N.º 10: Morosidad y calidad de cartera del sistema bancario peruano frente al ciclo económico
# Fecha de extracción: 2026-09-24

"""
VÍA 1 (API): consumo de la API de BCRPData (Banco Central de Reserva del Perú).

Endpoint : https://estadisticas.bcrp.gob.pe/estadisticas/series/api/{CODIGO}/csv/{INICIO}/{FIN}
Salida   : un archivo crudo por serie en datos_crudos/ (bytes exactos de la respuesta, sin editar)
Log      : log_ejecucion.txt (fecha y hora, código HTTP, número de filas, estado)

Orden de ejecución del proyecto: 01 -> 03 -> 04 (ver README.md).
"""

import os
import re
import time
from datetime import datetime
from pathlib import Path

import requests

# ============================================================
# PARÁMETROS CONGELADOS (constantes; NO usar fechas dinámicas tipo "hoy")
# ============================================================
FECHA_INICIO = "2010-01-01"
FECHA_CORTE = "2025-12-31"

URL_BASE = "https://estadisticas.bcrp.gob.pe/estadisticas/series/api"
CARPETA_CRUDOS = Path("datos_crudos")
ARCHIVO_LOG = Path("log_ejecucion.txt")

# User-Agent identificable; el contacto se puede sobrescribir con la variable de entorno
# USER_AGENT_SCRAPER (ver .env.example). La API del BCRP no requiere clave.
USER_AGENT = os.environ.get("USER_AGENT_SCRAPER", "EstudianteUNCP-FinanzasI/1.0 (2024200493L)")
PAUSA_SEGUNDOS = 1      # pausa mínima entre solicitudes (numeral 2.4.8)
REINTENTOS = 3          # reintentos ante fallas de red o respuestas no válidas

# Series macroeconómicas del BCRP (frecuencia mensual)
SERIES_MACRO = {
    "pbi": "PN01728AM",
    "inflacion": "PN01273PM",
    "tasa_activa": "PN07807NM",
    "tasa_pasiva": "PN07816NM",
    "cartera_total": "PN00528MM"
}

# Series de cartera atrasada neta / colocaciones netas (%) por empresa bancaria
# (verificadas contra el catálogo del BCRP: el código PN07744EM es Cencosud y PN07745EM es ICBC)
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
    "Cencosud": "PN07744EM",
    "ICBC": "PN07745EM",
    "Total_Sistema": "PN07746EM"   # agregado de empresas bancarias (no es un banco individual)
}


def registrar(mensaje):
    """Imprime en consola y agrega la línea al log_ejecucion.txt."""
    print(mensaje)
    with open(ARCHIVO_LOG, "a", encoding="utf-8") as f:
        f.write(mensaje + "\n")


def extraer_serie_bcrp(nombre, codigo, inicio, fin):
    """
    Descarga una serie del BCRP y guarda la respuesta TAL COMO SALE de la fuente.
    Devuelve True si la serie se guardó correctamente.
    """
    url = f"{URL_BASE}/{codigo}/csv/{inicio}/{fin}"
    headers = {"User-Agent": USER_AGENT}
    estado, http, filas = "ERROR", "-", 0

    for intento in range(1, REINTENTOS + 1):
        try:
            respuesta = requests.get(url, headers=headers, timeout=30)
            http = respuesta.status_code
            respuesta.raise_for_status()
            texto = respuesta.content.decode("utf-8", errors="replace")
            # Una respuesta válida empieza con la cabecera "Mes/Año"; si no, el portal devolvió HTML de error
            if not texto.startswith("Mes/"):
                raise ValueError("La respuesta no tiene formato de serie BCRP")
            filas = len(re.findall(r'<br>"', texto))
            CARPETA_CRUDOS.mkdir(exist_ok=True)
            # write_bytes conserva exactamente lo que envió la fuente (dato crudo = evidencia primaria)
            (CARPETA_CRUDOS / f"bcrp_{codigo}_crudo.csv").write_bytes(respuesta.content)
            estado = "OK"
            break
        except (requests.RequestException, ValueError) as e:
            estado = f"ERROR ({type(e).__name__}: {e})"
            time.sleep(PAUSA_SEGUNDOS * intento)

    ahora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    registrar(f"{ahora} | 01_extraccion_api | {codigo} | {nombre} | HTTP {http} | filas={filas} | {estado} | {url}")
    time.sleep(PAUSA_SEGUNDOS)
    return estado == "OK"


if __name__ == "__main__":
    ARCHIVO_LOG.write_text("", encoding="utf-8")   # el 01 inicia el log; los demás scripts agregan líneas
    registrar("=" * 70)
    registrar("EXTRACCIÓN BCRP - VÍA 1: API")
    registrar(f"Ventana congelada: {FECHA_INICIO} a {FECHA_CORTE}")
    registrar(f"Series macro: {len(SERIES_MACRO)} | Series por banco: {len(BANCOS)}")
    registrar("=" * 70)

    exitos, total = 0, len(SERIES_MACRO) + len(BANCOS)

    registrar("--- SERIES MACRO ---")
    for nombre, codigo in SERIES_MACRO.items():
        exitos += extraer_serie_bcrp(nombre, codigo, FECHA_INICIO, FECHA_CORTE)

    registrar("--- CARTERA ATRASADA NETA POR BANCO ---")
    for banco, codigo in BANCOS.items():
        exitos += extraer_serie_bcrp(f"atrasada_neta_{banco}", codigo, FECHA_INICIO, FECHA_CORTE)

    registrar(f"EXTRACCIÓN COMPLETADA: {exitos}/{total} series descargadas")
