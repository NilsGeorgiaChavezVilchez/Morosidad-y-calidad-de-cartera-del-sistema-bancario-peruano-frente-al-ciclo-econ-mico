# Nombres y apellidos: Nils Georgia Chavez Vilchez
# Código de matrícula: 2024200493L
# Tema N.º 10: Morosidad y calidad de cartera del sistema bancario peruano frente al ciclo económico
# Fecha de extracción: 2026-09-24

"""
Limpieza y construcción del panel banco-mes.

Entrada : datos_crudos/bcrp_<CODIGO>_crudo.csv (salida sin editar de 01 y 02)
Salida  : datos_procesados/datos_procesados_2024200493L.csv (separador ';', decimal '.')
          hash_sha256.txt (hash SHA-256 del archivo procesado)
Llave común de unión: 'fecha' (primer día del mes) para las series macro y 'banco' + 'fecha' para el panel.
Frecuencia: todas las series son mensuales, por lo que no se requiere armonización de frecuencia.
"""

import hashlib
import re
from datetime import datetime
from pathlib import Path

import pandas as pd

# ============================================================
# PARÁMETROS CONGELADOS (deben coincidir con 01_extraccion_api.py)
# ============================================================
FECHA_INICIO = "2010-01-01"
FECHA_CORTE = "2025-12-31"
CODIGO_MATRICULA = "2024200493L"
UMBRAL_OUTLIER = 3.5   # puntaje z modificado (MAD) por encima del cual se marca un valor atípico

CARPETA_CRUDOS = Path("datos_crudos")
ARCHIVO_SALIDA = Path(f"datos_procesados/datos_procesados_{CODIGO_MATRICULA}.csv")
ARCHIVO_LOG = Path("log_ejecucion.txt")

# Series macro: nombre de variable -> código BCRP
SERIES_MACRO = {
    "pbi": "PN01728AM",
    "inflacion": "PN01273PM",
    "tasa_activa": "PN07807NM",
    "tasa_pasiva": "PN07816NM",
    "cartera_total": "PN00528MM",
}

# Series por banco (cartera atrasada neta / colocaciones netas, %)
BANCOS = {
    "BCP": "PN07729EM", "Interbank": "PN07730EM", "Scotiabank": "PN07732EM",
    "Continental": "PN07733EM", "Comercio": "PN07734EM", "Financiero": "PN07735EM",
    "BanBif": "PN07736EM", "MiBanco": "PN07737EM", "GNB": "PN07738EM",
    "Falabella": "PN07739EM", "Santander": "PN07740EM", "Ripley": "PN07741EM",
    "Azteca": "PN07742EM", "Cencosud": "PN07744EM", "ICBC": "PN07745EM",
}
SERIE_SISTEMA = "PN07746EM"   # Total empresas bancarias (agregado, se usa como variable, no como banco)

MESES = {"Ene": "01", "Feb": "02", "Mar": "03", "Abr": "04", "May": "05", "Jun": "06",
         "Jul": "07", "Ago": "08", "Set": "09", "Sep": "09", "Oct": "10", "Nov": "11", "Dic": "12"}


def convertir_fecha(fecha_str):
    """Convierte 'Jul.2019' en la fecha '2019-07-01' (primer día del mes)."""
    partes = fecha_str.split(".")
    if len(partes) != 2 or partes[0] not in MESES:
        raise ValueError(f"Formato de fecha inválido: {fecha_str}")
    return f"{partes[1]}-{MESES[partes[0]]}-01"


def parsear_csv_bcrp(codigo):
    """
    Lee el crudo del BCRP (registros separados por <br>, formato "Mes.Año","valor").
    Devuelve (DataFrame con 'fecha' y 'valor', número de registros descartados por valor no numérico).
    """
    ruta = CARPETA_CRUDOS / f"bcrp_{codigo}_crudo.csv"
    contenido = ruta.read_text(encoding="utf-8", errors="replace")
    fechas, valores, descartados = [], [], 0
    for registro in contenido.split("<br>")[1:]:          # el primer registro es la cabecera
        m = re.match(r'\s*"([^"]+)"\s*,\s*"([^"]*)"', registro)
        if not m:
            continue
        fecha_str, valor_str = m.groups()
        try:
            fecha = convertir_fecha(fecha_str)
        except ValueError:
            descartados += 1
            continue
        # Faltantes: el BCRP marca los meses sin dato con 'n.d.' o vacío -> se dejan como NaN
        valor = pd.to_numeric(valor_str.replace(",", "."), errors="coerce")
        fechas.append(fecha)
        valores.append(valor)
    df = pd.DataFrame({"fecha": pd.to_datetime(fechas), "valor": valores})
    return df, descartados


def filtrar_ventana(df):
    """Restringe la serie a la ventana congelada FECHA_INICIO - FECHA_CORTE."""
    return df[(df["fecha"] >= FECHA_INICIO) & (df["fecha"] <= FECHA_CORTE)].copy()


def calcular_hash_sha256(ruta):
    """Hash SHA-256 del archivo procesado (numeral 2.4.5)."""
    h = hashlib.sha256()
    with open(ruta, "rb") as f:
        for bloque in iter(lambda: f.read(4096), b""):
            h.update(bloque)
    return h.hexdigest()


def registrar(mensaje):
    """Imprime en consola y agrega la línea al log_ejecucion.txt."""
    print(mensaje)
    with open(ARCHIVO_LOG, "a", encoding="utf-8") as f:
        f.write(mensaje + "\n")


def marca_tiempo():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


if __name__ == "__main__":
    registrar("=" * 70)
    registrar(f"{marca_tiempo()} | 03_limpieza_datos | Panel banco-mes {FECHA_INICIO} a {FECHA_CORTE}")
    registrar("=" * 70)
    Path("datos_procesados").mkdir(exist_ok=True)

    # ------------------------------------------------------------
    # 1. Series macro: se unen por 'fecha' (unión interna: solo meses con todas las variables)
    # ------------------------------------------------------------
    df_macro = None
    for nombre, codigo in SERIES_MACRO.items():
        df, malos = parsear_csv_bcrp(codigo)
        df = filtrar_ventana(df).rename(columns={"valor": nombre})
        faltantes = int(df[nombre].isna().sum())
        registrar(f"  {nombre} ({codigo}): {len(df)} meses, {faltantes} faltantes, {malos} registros ilegibles")
        df_macro = df if df_macro is None else df_macro.merge(df, on="fecha", how="inner")

    # Tratamiento de faltantes macro: se interpola linealmente solo huecos internos (nunca extremos)
    columnas_macro = list(SERIES_MACRO)
    faltantes_macro = int(df_macro[columnas_macro].isna().sum().sum())
    if faltantes_macro:
        df_macro[columnas_macro] = df_macro[columnas_macro].interpolate(method="linear", limit_area="inside")
        registrar(f"  Faltantes macro interpolados (huecos internos): {faltantes_macro}")
    df_macro["spread"] = df_macro["tasa_activa"] - df_macro["tasa_pasiva"]   # spread bancario en p.p.

    # ------------------------------------------------------------
    # 2. Cartera atrasada neta del sistema (agregado) por fecha
    # ------------------------------------------------------------
    df_sis, _ = parsear_csv_bcrp(SERIE_SISTEMA)
    df_sis = filtrar_ventana(df_sis).rename(columns={"valor": "atrasada_neta_sistema"})

    # ------------------------------------------------------------
    # 3. Panel por banco (bancos con historia incompleta se conservan sin imputar: panel no balanceado)
    # ------------------------------------------------------------
    paneles = []
    for banco, codigo in BANCOS.items():
        df, malos = parsear_csv_bcrp(codigo)
        df = filtrar_ventana(df).rename(columns={"valor": "atrasada_neta"})
        n_antes = len(df)
        df = df.dropna(subset=["atrasada_neta"])     # meses sin dato del banco no se imputan
        df["banco"] = banco
        registrar(f"  {banco} ({codigo}): {len(df)} meses con dato ({n_antes - len(df)} faltantes eliminados), "
                  f"{df['fecha'].min().date()} a {df['fecha'].max().date()}")
        paneles.append(df)
    panel = pd.concat(paneles, ignore_index=True)

    # ------------------------------------------------------------
    # 4. Unión por la llave común 'fecha'
    # ------------------------------------------------------------
    panel = panel.merge(df_sis, on="fecha", how="left").merge(df_macro, on="fecha", how="inner")
    panel = panel.sort_values(["banco", "fecha"]).reset_index(drop=True)

    # ------------------------------------------------------------
    # 5. Valores atípicos: se detectan con puntaje z modificado (MAD) por banco.
    #    NO se eliminan: corresponden a episodios reales (p. ej. shock COVID-19 en 2020) y son evidencia primaria.
    # ------------------------------------------------------------
    mediana = panel.groupby("banco")["atrasada_neta"].transform("median")
    mad = (panel["atrasada_neta"] - mediana).abs().groupby(panel["banco"]).transform("median")
    z_mod = 0.6745 * (panel["atrasada_neta"] - mediana) / mad.replace(0, float("nan"))
    n_out = int((z_mod.abs() > UMBRAL_OUTLIER).sum())
    registrar(f"  Valores atípicos marcados (|z modificado| > {UMBRAL_OUTLIER}): {n_out} de {len(panel)}; se conservan")

    # ------------------------------------------------------------
    # 6. Orden final de columnas y guardado
    # ------------------------------------------------------------
    panel = panel[["fecha", "banco", "atrasada_neta", "atrasada_neta_sistema", "pbi", "inflacion",
                   "tasa_activa", "tasa_pasiva", "spread", "cartera_total"]]
    panel.insert(0, "Id", range(1, len(panel) + 1))
    panel["fecha"] = panel["fecha"].dt.strftime("%Y-%m-%d")

    # lineterminator fijo: el hash no debe depender del sistema operativo
    panel.to_csv(ARCHIVO_SALIDA, index=False, sep=";", decimal=".", encoding="utf-8", lineterminator="\n")

    hash_sha256 = calcular_hash_sha256(ARCHIVO_SALIDA)
    Path("hash_sha256.txt").write_text(hash_sha256 + "\n", encoding="utf-8")

    registrar("-" * 70)
    registrar(f"{marca_tiempo()} | 03_limpieza_datos | Archivo: {ARCHIVO_SALIDA}")
    registrar(f"  Observaciones: {len(panel)} | Bancos: {panel['banco'].nunique()} | Meses: {panel['fecha'].nunique()}")
    registrar(f"  Rango: {panel['fecha'].min()} a {panel['fecha'].max()} | Columnas: {list(panel.columns)}")
    registrar(f"  Valores faltantes en el archivo final: {int(panel.isna().sum().sum())}")
    registrar(f"  SHA-256: {hash_sha256}")
    registrar(f"  Cumple mínimos: obs >= 1000: {len(panel) >= 1000} | variables sustantivas >= 4: True (8)")
