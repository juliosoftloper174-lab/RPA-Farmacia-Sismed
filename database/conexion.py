import pyodbc  # type: ignore


def test_conexion():
    try:
        conexion = pyodbc.connect(
            "DRIVER={ODBC Driver 17 for SQL Server};"
            "SERVER=localhost;"
            "DATABASE=SismedRPA;"
            "Trusted_Connection=yes;"
        )

        print("✅ Conexión exitosa")

        cursor = conexion.cursor()
        cursor.execute("SELECT * FROM MovimientosRPA")

        for fila in cursor.fetchall():
            print(fila)

    except Exception as e:
        print("❌ Error:", e)
