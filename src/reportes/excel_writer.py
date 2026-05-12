from pathlib import Path
import re
import unicodedata
import polars as pl
from src.reportes.excel_schema import EXCEL_COLUMNS

EXCEL_PATH = "movimientos.xlsx"


def _normalize_header_text(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", str(value))
    normalized = normalized.replace("�", "o").replace("º", "o").replace("°", "o")
    normalized = normalized.encode("ascii", "ignore").decode("ascii")
    normalized = re.sub(r"[^a-z0-9]", "", normalized.lower())
    return normalized


def _is_numeric_column(values: list) -> bool:
    for value in values:
        if value is None:
            continue
        if isinstance(value, (int, float)):
            continue
        value_str = str(value).strip()
        if value_str == "" or value_str.isdigit():
            continue
        return False
    return True


def _normalizar_df_existente(df: pl.DataFrame) -> pl.DataFrame:
    if df.width == 0:
        return df

    first_col = df.columns[0]

    if first_col not in EXCEL_COLUMNS:
        try:
            if _is_numeric_column(df[first_col].to_list()):
                df = df.rename({first_col: EXCEL_COLUMNS[0]})
        except Exception:
            pass

    if df.width == len(EXCEL_COLUMNS):
        position_match = all(
            _normalize_header_text(df_col) == _normalize_header_text(expected_col)
            for df_col, expected_col in zip(df.columns, EXCEL_COLUMNS)
        )
        if position_match:
            df.columns = EXCEL_COLUMNS

    return df


def guardar_movimientos(rows: list[dict]):
    nuevo_df = pl.DataFrame(rows)

    if Path(EXCEL_PATH).exists():
        df_actual = pl.read_excel(EXCEL_PATH)
        df_actual = _normalizar_df_existente(df_actual)
        df_final = pl.concat([df_actual, nuevo_df], how="diagonal_relaxed")
    else:
        df_final = nuevo_df

    df_final.write_excel(EXCEL_PATH)


def obtener_siguiente_numero_procesado() -> int:
    if not Path(EXCEL_PATH).exists():
        return 1

    df = pl.read_excel(EXCEL_PATH)
    df = _normalizar_df_existente(df)

    if df.height == 0:
        return 1

    ultima_fila = df.tail(1)

    if "Nº de Procesado" in df.columns:
        ultimo_numero = ultima_fila["Nº de Procesado"][0]
    else:
        fallback_col = df.columns[0]
        ultimo_numero = ultima_fila[fallback_col][0]

    try:
        return int(ultimo_numero) + 1
    except Exception:
        return df.height + 1
