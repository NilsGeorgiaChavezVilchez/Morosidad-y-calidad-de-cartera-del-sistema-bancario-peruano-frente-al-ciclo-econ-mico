# Nombres y apellidos: Nils Georgia Chavez Vilchez
# Código de matrícula: 2024200493L
# Tema: Morosidad y calidad de cartera del sistema bancario peruano frente al ciclo económico
# Fecha de extracción: 2026-09-24

import pandas as pd
from pathlib import Path
import re
import hashlib

# ============================================================
# FUNCIONES DE PROCESAMIENTO
# ============================================================
def parsear_csv_bcrp(ruta_archivo):
    """
    Parsea el CSV crudo del BCRP que viene en formato horizontal con <br>.
    Retorna un DataFrame con columnas 'fecha' y 'valor'.
    """
    contenido = Path(ruta_archivo).read_text(encoding="utf-8").strip()
    registros = re.split(r'<br>', contenido)
    
    fechas, valores = [], []
    for registro in registros:
        registro = registro.strip()
        if not registro:
            continue
        
        match = re.search(r'"([^"]+)".*?"([^"]+)"', registro)
        if match:
            fecha_str, valor_str = match.group(1), match.group(2)
            try:
                fecha = convertir_fecha(fecha_str)
                fechas.append(fecha)
                valor_str = valor_str.replace(',', '.')
                valores.append(float(valor_str))
            except:
                continue
    
    return pd.DataFrame({'fecha': fechas, 'valor': valores})

def convertir_fecha(fecha_str):
    """Convierte 'Jul.2019' a '2019-07-30'."""
    meses = {'Ene':'01','Feb':'02','Mar':'03','Abr':'04','May':'05','Jun':'06',
             'Jul':'07','Ago':'08','Sep':'09','Oct':'10','Nov':'11','Dic':'12'}
    partes = fecha_str.split('.')
    if len(partes) != 2:
        raise ValueError(f"Formato de fecha inválido: {fecha_str}")
    return f"{partes[1]}-{meses.get(partes[0],'01')}-30"

def calcular_hash_sha256(ruta):
    """Calcula hash SHA-256 (numeral 2.4.5)."""
    sha256_hash = hashlib.sha256()
    with open(ruta, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

# ============================================================
# PROCESO PRINCIPAL DE LIMPIEZA
# ============================================================
if __name__ == "__main__":
    print("=" * 70)
    print("LIMPIEZA Y CONSTRUCCIÓN DEL PANEL")
    print("Periodo: 2005-2025 (20 años)")
    print("=" * 70)
    
    Path("datos_procesados").mkdir(exist_ok=True)
    Path("salidas").mkdir(exist_ok=True)
    
    # ============================================================
    # 1. SERIES MACROECONÓMICAS
    # ============================================================
    print("\n--- SERIES MACROECONÓMICAS ---")
    SERIES_MACRO = {
        "pbi": "datos_crudos/bcrp_PN01728AM_crudo.csv",
        "tasa_activa": "datos_crudos/bcrp_PN07807NM_crudo.csv",
        "tasa_pasiva": "datos_crudos/bcrp_PN07816NM_crudo.csv",
        "cartera_total": "datos_crudos/bcrp_PN00528MM_crudo.csv"
    }
    
    df_macro = None
    for nombre, ruta in SERIES_MACRO.items():
        print(f"Procesando {nombre}...")
        df = parsear_csv_bcrp(ruta).rename(columns={'valor': nombre})
        if df_macro is None:
            df_macro = df[['fecha']].copy()
        df_macro = df_macro.merge(df, on='fecha', how='inner')
        print(f"  ✓ {len(df)} observaciones")
    
    # Calcular spread
    df_macro['spread'] = df_macro['tasa_activa'] - df_macro['tasa_pasiva']
    print("  ✓ Spread calculado: tasa_activa - tasa_pasiva")
    
    # ============================================================
    # 2. MOROSIDAD POR BANCO (15 BANCOS)
    # ============================================================
    print("\n--- MOROSIDAD POR BANCO (15 BANCOS) ---")
    BANCOS = {
        "BCP": "PN07729EM", "Interbank": "PN07730EM", "Scotiabank": "PN07732EM",
        "Continental": "PN07733EM", "Comercio": "PN07734EM", "Financiero": "PN07735EM",
        "BanBif": "PN07736EM", "MiBanco": "PN07737EM", "GNB": "PN07738EM",
        "Falabella": "PN07739EM", "Santander": "PN07740EM", "Ripley": "PN07741EM",
        "Azteca": "PN07742EM", "ICBC": "PN07744EM", "Total_Sistema": "PN07746EM"
    }
    
    dataframes_bancos = []
    for banco, codigo in BANCOS.items():
        ruta = f"datos_crudos/bcrp_{codigo}_crudo.csv"
        print(f"Procesando {banco}...")
        df = parsear_csv_bcrp(ruta)
        df = df.rename(columns={'valor': 'morosidad'})
        df['banco'] = banco
        dataframes_bancos.append(df)
        print(f"  ✓ {len(df)} observaciones")
    
    # ============================================================
    # 3. CONSTRUIR PANEL DE DATOS
    # ============================================================
    print("\n--- CONSTRUYENDO PANEL DE DATOS ---")
    df_panel = pd.concat(dataframes_bancos, ignore_index=True)
    df_panel = df_panel.merge(df_macro, on='fecha', how='left')
    df_panel = df_panel.sort_values(['banco', 'fecha']).reset_index(drop=True)
    
        # ============================================================
    # 4. REORDENAR COLUMNAS (orden solicitado)
    # ============================================================
    print("\n--- REORDENANDO COLUMNAS ---")
    
    # Orden final:
    # 1. Id (identificador de observación)
    # 2. fecha (identificador temporal)
    # 3. banco (identificador de entidad)
    # 4. morosidad (VARIABLE ENDÓGENA - la que se explica)
    # 5. pbi, tasa_activa, tasa_pasiva, cartera_total, spread (VARIABLES EXÓGENAS)
    
    df_panel = df_panel[['fecha', 'banco', 'morosidad', 'pbi', 'tasa_activa', 
                         'tasa_pasiva', 'cartera_total', 'spread']].copy()
    
    # Agregar columna ID al inicio
    df_panel.insert(0, 'Id', range(1, len(df_panel) + 1))
    
    print(f"  ✓ Orden final: Id | fecha | banco | ENDÓGENA(morosidad) | EXÓGENAS(pbi, tasa_activa, tasa_pasiva, cartera_total, spread)")
    print(f"  ✓ Columnas reordenadas: {list(df_panel.columns)}")
    print(f"  ✓ Columna ID agregada (1 a {len(df_panel)})")

    # ============================================================
    # 5. GUARDAR ARCHIVO PROCESADO (con separador ; para Excel)
    # ============================================================
    print("\n--- GUARDANDO ARCHIVO ---")
    codigo_matricula = "2024200493L"
    nombre_archivo = f"datos_procesados/datos_procesados_{codigo_matricula}.csv"
    
    # Guardar con separador ; para que Excel lo abra bien separado
    df_panel.to_csv(nombre_archivo, index=False, sep=';', decimal=',')
    
    print(f"\n✓ Archivo guardado: {nombre_archivo}")
    print(f"✓ Separador: punto y coma (;)")
    print(f"✓ Total de observaciones: {len(df_panel)}")
    print(f"✓ Bancos: {df_panel['banco'].nunique()}")
    print(f"✓ Periodos: {df_panel['fecha'].nunique()}")
    print(f"✓ Rango de fechas: {df_panel['fecha'].min()} a {df_panel['fecha'].max()}")
    print(f"✓ Columnas: {list(df_panel.columns)}")
    
    # ============================================================
    # 6. CALCULAR HASH SHA-256
    # ============================================================
    print("\n--- CALCULANDO HASH SHA-256 ---")
    hash_sha256 = calcular_hash_sha256(nombre_archivo)
    Path("hash_sha256.txt").write_text(hash_sha256, encoding="utf-8")
    print(f"✓ Hash SHA-256: {hash_sha256}")
    
    # ============================================================
    # 7. RESUMEN FINAL
    # ============================================================
    print("\n" + "=" * 70)
    print("RESUMEN FINAL")
    print("=" * 70)
    print(f"Observaciones totales: {len(df_panel)}")
    print(f"Cumple mínimo 1,000: {'SÍ ✓' if len(df_panel) >= 1000 else 'NO ✗'}")
    print(f"Variables sustantivas: 6 (morosidad, pbi, tasa_activa, tasa_pasiva, cartera_total, spread)")
    print(f"Cumple mínimo 4: SÍ ✓")
    print(f"Bancos: {df_panel['banco'].nunique()}")
    print(f"Periodo real: {df_panel['fecha'].min()} a {df_panel['fecha'].max()}")
    print("=" * 70)
    
    # Mostrar las primeras 10 filas para verificación
    print("\n--- PRIMERAS 10 FILAS DEL PANEL ---")
    print(df_panel.head(10).to_string(index=False))