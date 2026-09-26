# Nombres y apellidos: Nils Georgia Chavez Vilchez
# Código de matrícula: 2024200493L
# Tema N.º 10: Morosidad y calidad de cartera del sistema bancario peruano frente al ciclo económico
# Fecha de extracción: 2026-09-25

"""
02_scraping_web.py

SEGUNDA VÍA DE EXTRACCIÓN: NO UTILIZADA EN LA UNIDAD I.

De acuerdo con la consigna de Finanzas I, en la Unidad I se exige
al menos una vía automatizada de extracción, preferentemente mediante
API. La segunda vía de extracción es opcional.

Para esta investigación se utiliza como vía automatizada la API oficial
de BCRPData, implementada en 01_extraccion_api.py.

La serie de inflación (IPC de Lima Metropolitana, variación porcentual
a 12 meses, código PN01273PM) también se obtiene mediante dicha API y,
por tanto, se incorpora directamente en 01_extraccion_api.py.

Este archivo se conserva para respetar la estructura de la carpeta
/codigo solicitada en la consigna, pero NO participa en la construcción
de la base de datos correspondiente a la Unidad I.

Flujo reproducible utilizado:

    01_extraccion_api.py
            ↓
    03_limpieza_datos.py
            ↓
    04_analisis.py

Para la Unidad II deberá incorporarse una segunda vía independiente
mediante web scraping o descarga programática, conforme a la consigna.
"""


def main():
    print("=" * 70)
    print("02_scraping_web.py")
    print("Segunda vía de extracción no utilizada en la Unidad I.")
    print("La extracción de datos se realiza mediante 01_extraccion_api.py.")
    print("Continuar con 03_limpieza_datos.py.")
    print("=" * 70)


if __name__ == "__main__":
    main()