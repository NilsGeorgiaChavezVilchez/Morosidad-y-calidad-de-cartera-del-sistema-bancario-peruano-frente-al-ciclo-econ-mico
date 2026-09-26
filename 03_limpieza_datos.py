# Nombres y apellidos: Nils Georgia Chavez Vilchez
# Código de matrícula: 2024200493L
# Tema N.º 10: Morosidad y calidad de cartera del sistema bancario peruano frente al ciclo económico
# Fecha de extracción: 2026-09-24

"""
03_limpieza_datos.py

Limpieza y construcción del panel banco-mes.

UNIDAD I:
La base utilizada en esta unidad se construye exclusivamente a partir
de los archivos crudos generados por 01_extraccion_api.py mediante
la API oficial de BCRPData.

02_scraping_web.py no participa en la construcción de la base de la
Unidad I, debido a que la segunda vía automatizada es opcional.

Entrada:
    datos_crudos/bcrp_<CODIGO>_crudo.csv
    Archivos guardados sin editar por 01_extraccion_api.py.

Salida:
    datos_procesados/datos_procesados_2024200493L.csv
    hash_sha256.txt

Llaves de unión:
    - fecha: series macroeconómicas y agregado del sistema.
    - banco + fecha: estructura del panel bancario.

Frecuencia:
    Mensual.

Tratamiento:
    - Los faltantes macroeconómicos internos pueden interpolarse
      linealmente cuando son pocos.
    - No se interpolan faltantes ubicados en los extremos.
    - Los faltantes de las series bancarias no se imputan.
    - Los valores atípicos se identifican mediante MAD, pero no
      se eliminan ni modifican automáticamente.
"""

import hashlib
import re
from datetime import datetime
from pathlib import Path

import pandas as pd


# ============================================================
# 1. PARÁMETROS CONGELADOS
# ============================================================

FECHA_INICIO = "2010-01-01"
FECHA_CORTE = "2025-12-31"

CODIGO_MATRICULA = "2024200493L"

# Puntaje z modificado basado en MAD.
UMBRAL_OUTLIER = 3.5


# ============================================================
# 2. RUTAS DEL PROYECTO
# ============================================================

# ============================================================
# 2. RUTAS DEL PROYECTO
# ============================================================

# Los scripts y las carpetas datos_crudos, datos_procesados
# y salidas se encuentran dentro de la misma carpeta del proyecto.
# De esta manera, las rutas no dependen del nombre del usuario
# ni de una ubicación absoluta del computador.

BASE_DIR = Path(__file__).resolve().parent

CARPETA_CRUDOS = BASE_DIR / "datos_crudos"
CARPETA_PROCESADOS = BASE_DIR / "datos_procesados"

ARCHIVO_SALIDA = (
    CARPETA_PROCESADOS
    / f"datos_procesados_{CODIGO_MATRICULA}.csv"
)

ARCHIVO_LOG = BASE_DIR / "log_ejecucion.txt"
ARCHIVO_HASH = BASE_DIR / "hash_sha256.txt"

# ============================================================
# 3. SERIES DEL BCRP
# ============================================================

# Series macroeconómicas:
# nombre utilizado en la base -> código oficial BCRP.
SERIES_MACRO = {
    "pbi": "PN01728AM",
    "inflacion": "PN01273PM",
    "tasa_activa": "PN07807NM",
    "tasa_pasiva": "PN07816NM",
    "cartera_total": "PN00528MM",
}


# Series de cartera atrasada neta / colocaciones netas (%)
# por empresa bancaria.
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
}


# Agregado del sistema bancario.
# No se considera un banco individual dentro del panel.
SERIE_SISTEMA = "PN07746EM"


# Conversión de abreviaturas mensuales utilizadas por BCRP.
MESES = {
    "Ene": "01",
    "Feb": "02",
    "Mar": "03",
    "Abr": "04",
    "May": "05",
    "Jun": "06",
    "Jul": "07",
    "Ago": "08",
    "Set": "09",
    "Sep": "09",
    "Oct": "10",
    "Nov": "11",
    "Dic": "12",
}


# ============================================================
# 4. FUNCIONES AUXILIARES
# ============================================================

def convertir_fecha(fecha_str):
    """
    Convierte una fecha del BCRP como 'Jul.2019'
    en '2019-07-01'.
    """

    partes = fecha_str.split(".")

    if len(partes) != 2 or partes[0] not in MESES:
        raise ValueError(
            f"Formato de fecha inválido: {fecha_str}"
        )

    return (
        f"{partes[1]}-"
        f"{MESES[partes[0]]}-01"
    )


def parsear_csv_bcrp(codigo):
    """
    Lee un archivo crudo descargado desde BCRPData.

    El formato recibido por la API contiene registros separados
    mediante <br> y pares del tipo:

        "Mes.Año","valor"

    Devuelve:
        - DataFrame con columnas fecha y valor.
        - Número de registros descartados por problemas de formato.

    Los valores 'n.d.' o vacíos se convierten en NaN.
    """

    ruta = (
        CARPETA_CRUDOS
        / f"bcrp_{codigo}_crudo.csv"
    )

    if not ruta.exists():
        raise FileNotFoundError(
            f"No se encontró el archivo crudo: {ruta}"
        )

    contenido = ruta.read_text(
        encoding="utf-8",
        errors="replace"
    )

    fechas = []
    valores = []
    descartados = 0

    # El primer bloque corresponde a la cabecera.
    for registro in contenido.split("<br>")[1:]:

        m = re.match(
            r'\s*"([^"]+)"\s*,\s*"([^"]*)"',
            registro
        )

        if not m:
            continue

        fecha_str, valor_str = m.groups()

        try:
            fecha = convertir_fecha(fecha_str)

        except ValueError:
            descartados += 1
            continue

        # Los valores no numéricos, como "n.d.",
        # se conservan temporalmente como NaN.
        valor = pd.to_numeric(
            valor_str.replace(",", "."),
            errors="coerce"
        )

        fechas.append(fecha)
        valores.append(valor)

    df = pd.DataFrame({
        "fecha": pd.to_datetime(fechas),
        "valor": valores
    })

    return df, descartados


def filtrar_ventana(df):
    """
    Restringe una serie a la ventana temporal
    declarada mediante FECHA_INICIO y FECHA_CORTE.
    """

    return df[
        (df["fecha"] >= FECHA_INICIO)
        & (df["fecha"] <= FECHA_CORTE)
    ].copy()


def calcular_hash_sha256(ruta):
    """
    Calcula el hash SHA-256 del archivo procesado.
    """

    h = hashlib.sha256()

    with open(ruta, "rb") as f:

        for bloque in iter(
            lambda: f.read(4096),
            b""
        ):
            h.update(bloque)

    return h.hexdigest()


def registrar(mensaje):
    """
    Muestra el mensaje en consola y lo agrega
    al archivo log_ejecucion.txt.
    """

    print(mensaje)

    with open(
        ARCHIVO_LOG,
        "a",
        encoding="utf-8"
    ) as f:

        f.write(mensaje + "\n")


def marca_tiempo():
    """
    Devuelve la fecha y hora actual para el log.
    """

    return datetime.now().strftime(
        "%Y-%m-%d %H:%M:%S"
    )


# ============================================================
# 5. EJECUCIÓN PRINCIPAL
# ============================================================

if __name__ == "__main__":

    registrar("=" * 70)

    registrar(
        f"{marca_tiempo()} | "
        f"03_limpieza_datos | "
        f"Panel banco-mes "
        f"{FECHA_INICIO} a {FECHA_CORTE}"
    )

    registrar("=" * 70)

    # Crear la carpeta de datos procesados si todavía no existe.
    CARPETA_PROCESADOS.mkdir(
        parents=True,
        exist_ok=True
    )


    # ========================================================
    # 6. CONSTRUCCIÓN DE LAS SERIES MACROECONÓMICAS
    # ========================================================

    registrar(
        "--- SERIES MACROECONÓMICAS ---"
    )

    df_macro = None

    for nombre, codigo in SERIES_MACRO.items():

        df, malos = parsear_csv_bcrp(
            codigo
        )

        df = filtrar_ventana(
            df
        )

        df = df.rename(
            columns={"valor": nombre}
        )

        faltantes = int(
            df[nombre].isna().sum()
        )

        registrar(
            f"  {nombre} ({codigo}): "
            f"{len(df)} meses | "
            f"{faltantes} faltantes | "
            f"{malos} registros ilegibles"
        )

        if df_macro is None:

            df_macro = df

        else:

            df_macro = df_macro.merge(
                df,
                on="fecha",
                how="inner"
            )


    # ========================================================
    # 7. TRATAMIENTO DE VALORES FALTANTES MACROECONÓMICOS
    # ========================================================

    registrar(
        "--- TRATAMIENTO DE FALTANTES MACRO ---"
    )

    columnas_macro = list(
        SERIES_MACRO.keys()
    )

    # Se crea una bandera antes de realizar la interpolación.
    # Vale 1 cuando, para ese mes, al menos una de las variables
    # macroeconómicas estaba originalmente ausente.
    df_macro["dato_macro_imputado"] = (
        df_macro[columnas_macro]
        .isna()
        .any(axis=1)
        .astype(int)
    )

    for columna in columnas_macro:

        n_faltantes_antes = int(
            df_macro[columna]
            .isna()
            .sum()
        )

        if n_faltantes_antes > 0:

            df_macro[columna] = (
                df_macro[columna]
                .interpolate(
                    method="linear",
                    limit_area="inside"
                )
            )

            n_faltantes_despues = int(
                df_macro[columna]
                .isna()
                .sum()
            )

            n_interpolados = (
                n_faltantes_antes
                - n_faltantes_despues
            )

            registrar(
                f"  {columna}: "
                f"{n_faltantes_antes} faltantes detectados | "
                f"{n_interpolados} interpolados | "
                f"{n_faltantes_despues} permanecen sin dato"
            )

        else:

            registrar(
                f"  {columna}: "
                "0 faltantes detectados | "
                "no requiere interpolación"
            )


    # Cantidad total de faltantes que permanecen después
    # del tratamiento.
    faltantes_macro_finales = int(
        df_macro[columnas_macro]
        .isna()
        .sum()
        .sum()
    )

    registrar(
        f"  Total de faltantes macro "
        f"después del tratamiento: "
        f"{faltantes_macro_finales}"
    )

    meses_con_imputacion = int(
        df_macro["dato_macro_imputado"].sum()
    )

    registrar(
        f"  Meses con al menos un dato "
        f"macro originalmente faltante: "
        f"{meses_con_imputacion}"
    )


    # ========================================================
    # 8. CREACIÓN DEL SPREAD BANCARIO
    # ========================================================

    # Diferencia entre la tasa activa y la tasa pasiva.
    # Se expresa en puntos porcentuales.
    df_macro["spread"] = (
        df_macro["tasa_activa"]
        - df_macro["tasa_pasiva"]
    )


    # ========================================================
    # 9. CARTERA ATRASADA NETA DEL SISTEMA
    # ========================================================

    registrar(
        "--- CARTERA ATRASADA NETA DEL SISTEMA ---"
    )

    df_sis, malos_sis = parsear_csv_bcrp(
        SERIE_SISTEMA
    )

    df_sis = filtrar_ventana(
        df_sis
    )

    df_sis = df_sis.rename(
        columns={
            "valor": "atrasada_neta_sistema"
        }
    )

    registrar(
        f"  Sistema ({SERIE_SISTEMA}): "
        f"{len(df_sis)} meses | "
        f"{int(df_sis['atrasada_neta_sistema'].isna().sum())} faltantes | "
        f"{malos_sis} registros ilegibles"
    )


    # ========================================================
    # 10. CONSTRUCCIÓN DEL PANEL POR BANCO
    # ========================================================

    registrar(
        "--- SERIES POR BANCO ---"
    )

    paneles = []

    for banco, codigo in BANCOS.items():

        df, malos = parsear_csv_bcrp(
            codigo
        )

        df = filtrar_ventana(
            df
        )

        df = df.rename(
            columns={
                "valor": "atrasada_neta"
            }
        )

        n_antes = len(df)

        # Los faltantes de cada banco no se imputan.
        # Se conserva un panel no balanceado.
        df = df.dropna(
            subset=["atrasada_neta"]
        ).copy()

        df["banco"] = banco

        n_eliminados = (
            n_antes - len(df)
        )

        if len(df) > 0:

            fecha_min = (
                df["fecha"]
                .min()
                .date()
            )

            fecha_max = (
                df["fecha"]
                .max()
                .date()
            )

            registrar(
                f"  {banco} ({codigo}): "
                f"{len(df)} meses con dato | "
                f"{n_eliminados} meses sin dato eliminados | "
                f"{malos} registros ilegibles | "
                f"{fecha_min} a {fecha_max}"
            )

        else:

            registrar(
                f"  {banco} ({codigo}): "
                "sin observaciones válidas"
            )

        paneles.append(
            df
        )


    panel = pd.concat(
        paneles,
        ignore_index=True
    )


    # ========================================================
    # 11. UNIÓN DE LAS SERIES
    # ========================================================

    registrar(
        "--- UNIÓN DE LA BASE ---"
    )

    panel = panel.merge(
        df_sis,
        on="fecha",
        how="left"
    )

    panel = panel.merge(
        df_macro,
        on="fecha",
        how="inner"
    )

    panel = (
        panel
        .sort_values(
            ["banco", "fecha"]
        )
        .reset_index(drop=True)
    )


    # ========================================================
    # 12. CONTROL DE DUPLICADOS
    # ========================================================

    duplicados = int(
        panel.duplicated(
            subset=[
                "banco",
                "fecha"
            ]
        ).sum()
    )

    registrar(
        f"  Duplicados banco-fecha "
        f"detectados: {duplicados}"
    )

    if duplicados > 0:

        raise ValueError(
            f"Se detectaron {duplicados} "
            "observaciones duplicadas banco-fecha."
        )


    # ========================================================
    # 13. CONTROL DE LA VENTANA TEMPORAL
    # ========================================================

    if panel["fecha"].min() < pd.Timestamp(
        FECHA_INICIO
    ):

        raise ValueError(
            "La base contiene fechas anteriores "
            "a FECHA_INICIO."
        )

    if panel["fecha"].max() > pd.Timestamp(
        FECHA_CORTE
    ):

        raise ValueError(
            "La base contiene fechas posteriores "
            "a FECHA_CORTE."
        )

    registrar(
        "  Ventana temporal verificada correctamente."
    )


    # ========================================================
    # 14. IDENTIFICACIÓN DE VALORES ATÍPICOS
    # ========================================================

    registrar(
        "--- DIAGNÓSTICO DE VALORES ATÍPICOS ---"
    )

    # Los valores atípicos se identifican mediante el
    # puntaje z modificado basado en MAD.
    #
    # El procedimiento es únicamente diagnóstico.
    # No se eliminan ni modifican automáticamente los valores.

    mediana = (
        panel
        .groupby("banco")["atrasada_neta"]
        .transform("median")
    )

    mad = (
        (panel["atrasada_neta"] - mediana)
        .abs()
        .groupby(panel["banco"])
        .transform("median")
    )

    z_mod = (
        0.6745
        * (panel["atrasada_neta"] - mediana)
        / mad.replace(
            0,
            float("nan")
        )
    )

    n_out = int(
        (
            z_mod.abs()
            > UMBRAL_OUTLIER
        ).sum()
    )

    registrar(
        f"  Valores atípicos identificados "
        f"(|z modificado| > {UMBRAL_OUTLIER}): "
        f"{n_out} de {len(panel)} | "
        "se conservan sin modificación"
    )


    # ========================================================
    # 15. REVISIÓN DE VALORES FALTANTES FINALES
    # ========================================================

    registrar(
        "--- REVISIÓN DE FALTANTES FINALES ---"
    )

    faltantes_por_variable = (
        panel
        .isna()
        .sum()
    )

    total_faltantes = int(
        faltantes_por_variable.sum()
    )

    if total_faltantes == 0:

        registrar(
            "  No existen valores faltantes "
            "en la base final."
        )

    else:

        registrar(
            f"  Total de valores faltantes "
            f"en la base final: "
            f"{total_faltantes}"
        )

        for columna, cantidad in (
            faltantes_por_variable.items()
        ):

            if cantidad > 0:

                registrar(
                    f"    {columna}: "
                    f"{int(cantidad)}"
                )


    # ========================================================
    # 16. ORDEN FINAL DE COLUMNAS
    # ========================================================

    panel = panel[
        [
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
            "dato_macro_imputado",
        ]
    ].copy()


    # Identificador secuencial.
    panel.insert(
        0,
        "Id",
        range(
            1,
            len(panel) + 1
        )
    )


    # La fecha se almacena con formato ISO YYYY-MM-DD.
    panel["fecha"] = (
        panel["fecha"]
        .dt.strftime("%Y-%m-%d")
    )


    # ========================================================
    # 17. GUARDADO DEL ARCHIVO PROCESADO
    # ========================================================

    panel.to_csv(
        ARCHIVO_SALIDA,
        index=False,
        sep=";",
        decimal=".",
        encoding="utf-8",
        lineterminator="\n"
    )


    # ========================================================
    # 18. VERIFICACIÓN DEL ARCHIVO GENERADO
    # ========================================================

    if not ARCHIVO_SALIDA.exists():

        raise FileNotFoundError(
            f"No se generó el archivo procesado: "
            f"{ARCHIVO_SALIDA}"
        )

    if ARCHIVO_SALIDA.stat().st_size == 0:

        raise ValueError(
            "El archivo procesado fue generado vacío."
        )


    # ========================================================
    # 19. HASH SHA-256
    # ========================================================

    hash_sha256 = calcular_hash_sha256(
        ARCHIVO_SALIDA
    )

    ARCHIVO_HASH.write_text(
        hash_sha256 + "\n",
        encoding="utf-8"
    )


    # ========================================================
    # 20. REGISTRO FINAL
    # ========================================================

    registrar("-" * 70)

    registrar(
        f"{marca_tiempo()} | "
        f"03_limpieza_datos | "
        f"Archivo: {ARCHIVO_SALIDA.name}"
    )

    registrar(
        f"  Observaciones: {len(panel)} | "
        f"Bancos: {panel['banco'].nunique()} | "
        f"Meses: {panel['fecha'].nunique()}"
    )

    registrar(
        f"  Rango: "
        f"{panel['fecha'].min()} "
        f"a "
        f"{panel['fecha'].max()}"
    )

    registrar(
        f"  Columnas: "
        f"{list(panel.columns)}"
    )

    registrar(
        f"  Valores faltantes finales: "
        f"{int(panel.isna().sum().sum())}"
    )

    registrar(
        f"  Meses macro con alguna imputación: "
        f"{meses_con_imputacion}"
    )

    registrar(
        f"  Valores atípicos identificados: "
        f"{n_out}"
    )

    registrar(
        f"  SHA-256: "
        f"{hash_sha256}"
    )

    registrar(
        f"  Cumple mínimo de observaciones >= 1000: "
        f"{len(panel) >= 1000}"
    )

    registrar(
        "  Variables sustantivas >= 4: "
        "True (8)"
    )

    registrar("=" * 70)

    registrar(
        "03_limpieza_datos.py "
        "COMPLETADO CORRECTAMENTE"
    )

    registrar("=" * 70)