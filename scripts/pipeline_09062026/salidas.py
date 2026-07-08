from src.models.Medicamento import Medicamento
from src.models.Salidas import Salidas

ORIGEN = "06732F01"
VIRTUAL = "06732F0101"
CONCEPTO = "DISTRIBUCION"


def generar_pre_distribuciones() -> tuple[Salidas, ...]:
    # Pre-distribuye stock desde F01 a las farmacias que actuan como ORIGEN
    # en las salidas del SP, para que tengan suficiente stock para 20 ejecuciones.
    return (
        # F02 necesita 06471 x 50 (para F02->F05) * 20 = 1000
        Salidas(
            almacen_origen=ORIGEN, almacen_destino="06732F02",
            almacen_virtual_origen=VIRTUAL, concepto=CONCEPTO,
            medicamentos=[
                Medicamento(codigo="06471", cantidad=1000),
            ],
        ),
        # F03 necesita 01537 x 70 (para F03->F02) * 20 = 1400
        Salidas(
            almacen_origen=ORIGEN, almacen_destino="06732F03",
            almacen_virtual_origen=VIRTUAL, concepto=CONCEPTO,
            medicamentos=[
                Medicamento(codigo="01537", cantidad=1400),
            ],
        ),
        # F04 necesita 18157 x 7 (para F04->F05) * 20 = 140
        Salidas(
            almacen_origen=ORIGEN, almacen_destino="06732F04",
            almacen_virtual_origen=VIRTUAL, concepto=CONCEPTO,
            medicamentos=[
                Medicamento(codigo="18157", cantidad=140),
            ],
        ),
        # F05 necesita 01537 x 55 (para F05->F02) + 04901 x 3 (para F05->F04)
        # * 20 = 1100 + 60
        Salidas(
            almacen_origen=ORIGEN, almacen_destino="06732F05",
            almacen_virtual_origen=VIRTUAL, concepto=CONCEPTO,
            medicamentos=[
                Medicamento(codigo="01537", cantidad=1100),
                Medicamento(codigo="04901", cantidad=60),
            ],
        ),
    )
