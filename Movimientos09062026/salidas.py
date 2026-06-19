from src.models.Medicamento import Medicamento
from src.models.Salidas import Salidas

ORIGEN = "06732F01"
VIRTUAL = "06732F0101"
CONCEPTO = "DISTRIBUCION"


def generar_salidas() -> tuple[Salidas, ...]:
    return (
        # F02: 33 productos
        Salidas(
            almacen_origen=ORIGEN, almacen_destino="06732F02",
            almacen_virtual_origen=VIRTUAL, concepto=CONCEPTO,
            medicamentos=[
                Medicamento(codigo=c, cantidad=q)
                for c, q in [
                    ("01537", 125), ("00269", 300), ("01636", 2200),
                    ("01964", 500), ("03086", 30),  ("03215", 100),
                    ("03751", 30),  ("04677", 200), ("04922", 50),
                    ("05335", 2000),("05578", 10),  ("05873", 120),
                    ("05884", 30),  ("06285", 15),  ("10145", 200),
                    ("10299", 100), ("10367", 60),  ("10554", 50),
                    ("11368", 500), ("12019", 24),  ("12805", 50),
                    ("12808", 150), ("16571", 600), ("16572", 200),
                    ("16597", 100), ("16599", 100), ("16602", 100),
                    ("18091", 15),  ("19404", 780), ("19719", 200),
                    ("22256", 200), ("24704", 300), ("38955", 100),
                ]
            ],
        ),
        # F04: 04901 x3
        Salidas(
            almacen_origen=ORIGEN, almacen_destino="06732F04",
            almacen_virtual_origen=VIRTUAL, concepto=CONCEPTO,
            medicamentos=[
                Medicamento(codigo="04901", cantidad=3),
            ],
        ),
        # F05: 06471, 18157, 04922, 12804, 12805
        Salidas(
            almacen_origen=ORIGEN, almacen_destino="06732F05",
            almacen_virtual_origen=VIRTUAL, concepto=CONCEPTO,
            medicamentos=[
                Medicamento(codigo=c, cantidad=q)
                for c, q in [
                    ("06471", 50), ("18157", 7), ("04922", 20),
                    ("12804", 100), ("12805", 100),
                ]
            ],
        ),
    )
