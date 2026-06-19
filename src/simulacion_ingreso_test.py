from src.models.ingreso import Ingreso
from src.models.Medicamento import Medicamento

# =========================================================
# SIMULACION DE INGRESO PARA INYECTAR STOCK
# =========================================================
# La nota de ingreso solo permite enviar productos desde el
# almacen "030S01" (ALM. ANEXO RIOJA) hacia la farmacia
# "06732F01". Ningun otro destino es alcanzable.
#
# Este archivo genera 1 ingreso a 06732F01 con TODOS los
# productos que aparecen en las salidas del SP, multiplicados
# por 5. Esto asegura que la farmacia principal tenga stock
# suficiente para luego distribuir a las demas farmacias
# mediante notas de salida (ver simulacion_salida_test.py).
# =========================================================


def generar_ingresos_para_prueba() -> tuple[Ingreso, ...]:
    ALMACEN_VIRTUAL = "030S0101"
    CONCEPTO = "DISTRIBUCION"
    LOTE = "SIMTEST"
    TIPO_SUM = "SISMED-COMPRA NACIONAL (CN)"
    FUENTE_FIN = "Donaciones y Transferencias (DYT)"
    REG_SAN = "SIN_REG_SAN"
    FECHA_VEN = "2026/12/30"
    PRECIO = 0.01

    multiplicador = 5

    # Todos los productos de todas las SALIDAS, agrupados por código
    productos = [
        ("00269", 300), ("01537", 125), ("01636", 2200),
        ("01964", 500), ("03086", 30), ("03215", 100),
        ("03751", 30), ("04677", 200), ("04901", 3),
        ("04922", 70), ("05335", 2000), ("05578", 10),
        ("05873", 120), ("05884", 30), ("06285", 15),
        ("06471", 50), ("10145", 200), ("10299", 100),
        ("10367", 60), ("10554", 50), ("11368", 500),
        ("12019", 24), ("12804", 100), ("12805", 150),
        ("12808", 150), ("16571", 600), ("16572", 200),
        ("16597", 100), ("16599", 100), ("16602", 100),
        ("18091", 15), ("18157", 7), ("19404", 780),
        ("19719", 200), ("22256", 200), ("24704", 300),
        ("38955", 100),
    ]

    medicamentos = [
        Medicamento(
            codigo=codigo,
            cantidad=cantidad * multiplicador,
            lote=LOTE,
            tipo_sum=TIPO_SUM,
            fuente_fin=FUENTE_FIN,
            registro_sanitario=REG_SAN,
            fecha_vencimiento=FECHA_VEN,
            precio_compra=PRECIO,
        )
        for codigo, cantidad in productos
    ]

    return (
        Ingreso(
            almacen_destino="06732F01",
            almacen_virtual_origen=ALMACEN_VIRTUAL,
            concepto=CONCEPTO,
            medicamentos=medicamentos,
        ),
    )
