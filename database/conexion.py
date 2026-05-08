import pyodbc  # type: ignore
from src.logger import logger


def test_conexion():
    try:
        conexion = pyodbc.connect(
            "DRIVER={ODBC Driver 17 for SQL Server};"
            "SERVER=localhost;"
            "DATABASE=SismedRPA;"
            "Trusted_Connection=yes;"
        )

        logger.info("✅ Conexión exitosa")

        cursor = conexion.cursor()
        cursor.execute("SELECT * FROM MovimientosRPA")

        for fila in cursor.fetchall():
            logger.info(fila)

    except Exception as e:
        logger.info("❌ Error:", e)
