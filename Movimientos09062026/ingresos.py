from src.models.ingreso import Ingreso
from src.models.Medicamento import Medicamento

ALMACEN_VIRTUAL = "030S0101"
CONCEPTO = "DISTRIBUCION"
LOTE = "SIM0906"
TIPO_SUM = "SISMED-COMPRA NACIONAL (CN)"
FUENTE_FIN = "Donaciones y Transferencias (DYT)"
REG_SAN = "SIN_REG_SAN"
FECHA_VEN = "2026/12/30"
PRECIO = 0.01


def generar_ingresos() -> tuple[Ingreso, ...]:
    # Todos los productos que necesita cualquier almacen como ORIGEN en las
    # salidas del SP, con cantidad x20 para poder ejecutar el pipeline real
    # 20 veces sin quedarse sin stock.
    productos = [
        ("00269", 6000), ("01537", 2500), ("01636", 44000), ("01964", 10000),
        ("03086", 600),  ("03215", 2000), ("03751", 600),  ("04677", 4000),
        ("04901", 60),   ("04922", 1400), ("05335", 40000),("05578", 200),
        ("05873", 2400), ("05884", 600),  ("06285", 300),  ("06471", 1000),
        ("10145", 4000), ("10299", 2000), ("10367", 1200), ("10554", 1000),
        ("11368", 10000),("12019", 480),  ("12804", 2000), ("12805", 3000),
        ("12808", 3000), ("16571", 12000),("16572", 4000), ("16597", 2000),
        ("16599", 2000), ("16602", 2000), ("18091", 300),  ("18157", 140),
        ("19404", 15600),("19719", 4000), ("22256", 4000), ("24704", 6000),
        ("38955", 2000),
    ]
    medicamentos = [
        Medicamento(codigo=c, cantidad=q, lote=LOTE,
            tipo_sum=TIPO_SUM, fuente_fin=FUENTE_FIN,
            registro_sanitario=REG_SAN, fecha_vencimiento=FECHA_VEN,
            precio_compra=PRECIO)
        for c, q in productos
    ]
    return (Ingreso(
        almacen_destino="06732F01",
        almacen_virtual_origen=ALMACEN_VIRTUAL,
        concepto=CONCEPTO,
        medicamentos=medicamentos,
    ),)
