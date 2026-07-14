from pathlib import Path
import re
import unicodedata
from datetime import datetime
import polars as pl
from src.reportes.excel_schema import EXCEL_COLUMNS

MESES_ES = [
    "", "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
    "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre",
]


def _path_del_dia(fecha: str | None = None, fecha_fin: str | None = None, modo: str = "horario") -> Path:
    if fecha is None:
        fecha = datetime.now().strftime("%Y-%m-%d")
    dt = datetime.strptime(fecha, "%Y-%m-%d")
    if fecha_fin:
        dt_fin = datetime.strptime(fecha_fin, "%Y-%m-%d")
        filename = f"MOV_{dt.strftime('%d-%m-%y')}_{dt_fin.strftime('%d-%m-%y')}.xlsx"
    else:
        filename = f"MOV_{dt.strftime('%d-%m-%y')}.xlsx"
    ruta = Path("ReportesExcel") / modo / str(dt.year) / MESES_ES[dt.month] / filename
    ruta.parent.mkdir(parents=True, exist_ok=True)
    return ruta


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


def guardar_movimientos(rows: list[dict] | dict, fecha: str | None = None, fecha_fin: str | None = None, modo: str = "horario"):
    if isinstance(rows, dict):
        rows = [rows]

    for row in rows:
        for key, value in row.items():
            row[key] = str(value) if value is not None else ""

    path = _path_del_dia(fecha, fecha_fin, modo)
    nuevo_df = pl.DataFrame(rows)

    if path.exists():
        schema_overrides = {col: pl.Utf8 for col in EXCEL_COLUMNS}
        df_actual = pl.read_excel(path, schema_overrides=schema_overrides)
        df_actual = _normalizar_df_existente(df_actual)
        df_final = pl.concat([df_actual, nuevo_df], how="diagonal_relaxed")
    else:
        df_final = nuevo_df

    df_final.write_excel(path)


def obtener_siguiente_numero_procesado(fecha: str | None = None, fecha_fin: str | None = None, modo: str = "horario") -> int:
    path = _path_del_dia(fecha, fecha_fin, modo)
    if not path.exists():
        return 1

    schema_overrides = {col: pl.Utf8 for col in EXCEL_COLUMNS}
    df = pl.read_excel(path, schema_overrides=schema_overrides)
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


def leer_resumen_diario(fecha: str | None = None, fecha_fin: str | None = None, modo: str = "horario") -> dict:
    path = _path_del_dia(fecha, fecha_fin, modo)
    if not path.exists():
        return {"ingresos": 0, "salidas": 0, "pedidos": 0, "ok": 0, "error": 0, "sin_stock": 0, "saltados": 0}

    schema_overrides = {col: pl.Utf8 for col in EXCEL_COLUMNS}
    df = pl.read_excel(path, schema_overrides=schema_overrides)

    resumen = {"ingresos": 0, "salidas": 0, "pedidos": 0, "ok": 0, "error": 0, "sin_stock": 0, "saltados": 0}

    if "TipoMovimiento" in df.columns:
        for tipo in ("INGRESO", "SALIDA", "PEDIDO"):
            resumen[tipo.lower() + "s"] = (df["TipoMovimiento"] == tipo).sum()

    if "Estado" in df.columns:
        estados = df["Estado"].to_list()
        resumen["ok"] = sum(1 for e in estados if str(e).upper() in ("OK", "OK_REPROCESADO"))
        resumen["error"] = sum(1 for e in estados if str(e).upper() == "ERROR")
        resumen["sin_stock"] = sum(1 for e in estados if str(e).upper() == "SIN_STOCK")
        resumen["saltados"] = sum(1 for e in estados if str(e).upper() == "SALTADO")

    return resumen



