import pyodbc

conn = pyodbc.connect(
    "DRIVER={ODBC Driver 17 for SQL Server};"
    "SERVER=192.168.170.37;"
    "DATABASE=ksalud_qa;"
    "UID=rpa;"
    "PWD=rpaKsalud;"
)
cursor = conn.cursor()

# Test 1: Buscar SPs con nombre similar
cursor.execute("SELECT name FROM sys.procedures WHERE name LIKE '%SISMED%'")
rows = cursor.fetchall()
print(f"SPs encontrados: {[r[0] for r in rows]}")

# Test 2: Ejecutar el SP con fechas como strings
cursor.execute("EXEC SP_MOVIMIENTOS_SISMED_RPA ?, ?", ("2026-06-10", "2026-06-10"))

print("\n--- Resultset 1 ---")
if cursor.description:
    cols = [c[0] for c in cursor.description]
    print(f"Columnas ({len(cols)}): {cols}")
    rows = cursor.fetchall()
    print(f"Filas: {len(rows)}")
    if rows:
        print("Primera fila:")
        for k, v in zip(cols, rows[0]):
            print(f"  {k} = {v}")
else:
    print("Sin descripcion - posiblemente no es SELECT")

# Test 3: Ver si hay mas resultsets
i = 2
while cursor.nextset():
    if cursor.description:
        cols = [c[0] for c in cursor.description]
        print(f"\n--- Resultset {i} ---")
        print(f"Columnas ({len(cols)}): {cols}")
        rows = cursor.fetchall()
        print(f"Filas: {len(rows)}")
        if rows:
            print("Primera fila:")
            for k, v in zip(cols, rows[0]):
                print(f"  {k} = {v}")
    else:
        print(f"\n--- Resultset {i} (sin columnas) ---")
    i += 1

cursor.close()
conn.close()
input("\nPresiona Enter para salir...")
