import pyodbc
from src.logger import logger
from src.config import DB_SERVER, DB_NAME, DB_USER, DB_PASS


COLUMNAS_HEADER = {"CORRELATIVO_KSALUD", "TIPO_MOVIMIENTO_DES", "FARMACIA", "FORMA_PAGO", "ALMACEN_DESTINO"}
COLUMNAS_DETALLE = {"CORRELATIVO_KSALUD", "MATERIAL_CODIGO", "CANTIDAD", "LOTE", "REGISTRO_SANITARIO"}


def get_connection() -> pyodbc.Connection:
    conn_str = (
        f"DRIVER={{ODBC Driver 17 for SQL Server}};"
        f"SERVER={DB_SERVER};"
        f"DATABASE={DB_NAME};"
        f"UID={DB_USER};"
        f"PWD={DB_PASS};"
    )
    return pyodbc.connect(conn_str)


def _identificar_resultset(columns: list[str]) -> str | None:
    colset = set(columns)
    if COLUMNAS_HEADER.issubset(colset):
        return "header"
    if COLUMNAS_DETALLE.issubset(colset):
        return "detalle"
    return None


def ejecutar_sp_movimientos(fecha_ini: str, fecha_fin: str) -> tuple[list[dict], list[dict]]:
    conn = get_connection()
    cursor = conn.cursor()

    logger.info(f"Ejecutando SP_MOVIMIENTOS_SISMED_RPA '{fecha_ini}' a '{fecha_fin}'")
    cursor.execute(f"EXEC SP_MOVIMIENTOS_SISMED_RPA ?, ?", (fecha_ini, fecha_fin))

    headers = []
    detalles = []

    while True:
        if cursor.description is None:
            if not cursor.nextset():
                break
            continue

        columns = [col[0] for col in cursor.description]
        rows = cursor.fetchall()
        tipo = _identificar_resultset(columns)

        if tipo == "header":
            headers = [dict(zip(columns, row)) for row in rows]
            logger.info(f"Header detectado: {len(headers)} filas, {len(columns)} columnas")
        elif tipo == "detalle":
            detalles = [dict(zip(columns, row)) for row in rows]
            logger.info(f"Detalle detectado: {len(detalles)} filas, {len(columns)} columnas")
        else:
            logger.info(f"Resultset ignorado: {len(rows)} filas, columnas: {columns[:3]}...")

        if not cursor.nextset():
            break

    cursor.close()
    conn.close()

    logger.info(f"Total headers: {len(headers)}, total detalles: {len(detalles)}")
    return headers, detalles


def ejecutar_sp_update_estado(update_key: tuple[str, ...]) -> None:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        DECLARE @RptaCod varchar(3), @RtaMensjError varchar(900)
        SET @RptaCod = NULL; SET @RtaMensjError = NULL
        EXEC SP_UPDESTADOMOV_RPA ?, ?, ?, ?, ?, ?, ?, ?, @RptaCod OUTPUT, @RtaMensjError OUTPUT
        SELECT @RptaCod, @RtaMensjError
        """,
        update_key,
    )
    conn.commit()
    row = cursor.fetchone()
    cursor.close()
    conn.close()
    if row:
        rpta, msg = str(row[0] or ""), str(row[1] or "")
        logger.info(f"SP_UPDESTADOMOV_RPA -> cod={rpta}, msg={msg}")
