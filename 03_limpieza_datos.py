# Nombres y apellidos: Nils Georgia Chavez Vilchez
# Código de matrícula: 2024200493L
# Tema: Morosidad y calidad de cartera del sistema bancario peruano frente al ciclo económico
# Fecha de extracción: 2026-09-24

import pandas as pd
from pathlib import Path
import re
import hashlib

def parsear_csv_bcrp(ruta_archivo):
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
    meses = {'Ene':'01','Feb':'02','Mar':'03','Abr':'04','May':'05','Jun':'06',
             'Jul':'07','Ago':'08','Sep':'09','Oct':'10','Nov':'11','Dic':'12'}
    partes = fecha_str.split('.')
    return f"{partes[1]}-{meses.get(partes[0],'01')}-30"

def calcular_hash_sha256(ruta):
    sha256_hash = hashlib.sha256()
    with open(ruta, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

if __name__ == "__main__":
    print("=" * 70)
    print("LIMPIEZA Y CONSTRUCCIÓN DEL PANEL")
    print("15 bancos × 240 meses (2005-2025)")
    print("=" * 70)
    
    Path("datos_procesados").mkdir(exist_ok=True)
    Path("salidas").mkdir(exist_ok=True)
    
    # 1. Series macro
    print("\n--- SERIES MACRO ---")
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
    
    df_macro['spread'] = df_macro['tasa_activa'] - df_macro['tasa_pasiva']
    print("  ✓ Spread calculado")
    
    # 2. Morosidad por banco
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
    
    # 3. Construir panel
    print("\n--- CONSTRUYENDO PANEL ---")
    df_panel = pd.concat(dataframes_bancos, ignore_index=True)
    df_panel = df_panel.merge(df_macro, on='fecha', how='left')
    df_panel = df_panel.sort_values(['banco', 'fecha']).reset_index(drop=True)
    
    # 4. Guardar
    codigo_matricula = "2024200493L"
    nombre_archivo = f"datos_procesados/datos_procesados_{codigo_matricula}.csv"
    df_panel.to_csv(nombre_archivo, index=False)
    
    print(f"\n✓ Archivo: {nombre_archivo}")
    print(f"✓ Observaciones: {len(df_panel)}")
    print(f"✓ Bancos: {df_panel['banco'].nunique()}")
    print(f"✓ Periodos: {df_panel['fecha'].nunique()}")
    print(f"✓ Columnas: {list(df_panel.columns)}")
    
    # 5. Hash
    hash_sha256 = calcular_hash_sha256(nombre_archivo)
    Path("hash_sha256.txt").write_text(hash_sha256, encoding="utf-8")
    print(f"\n✓ Hash SHA-256: {hash_sha256}")
    
    print("\n" + "=" * 70)
    print("LIMPIEZA COMPLETADA")
    print("=" * 70)