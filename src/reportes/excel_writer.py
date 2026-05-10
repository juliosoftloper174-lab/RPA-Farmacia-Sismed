from pathlib import Path
import polars as pl

EXCEL_PATH = "movimientos.xlsx"


def guardar_movimientos(rows: list[dict]):

    nuevo_df = pl.DataFrame(rows)

    if Path(EXCEL_PATH).exists():

        df_actual = pl.read_excel(EXCEL_PATH)

        df_final = pl.concat([df_actual, nuevo_df])

    else:

        df_final = nuevo_df

    df_final.write_excel(EXCEL_PATH)


def obtener_siguiente_numero_procesado() -> int:

    if not Path(EXCEL_PATH).exists():
        return 1

    df = pl.read_excel(EXCEL_PATH)

    if df.height == 0:
        return 1

    ultima_fila = df.tail(1)

    ultimo_numero = ultima_fila["Nº de Procesado"][0]

    return int(ultimo_numero) + 1
