from src.models.Medicamento import Medicamento
from src.models.Salidas import Salidas

# =========================================================
# SIMULACION DE LLENADO DE STOCK PARA SALIDAS DEL SP
# =========================================================
# Las salidas del SP requieren que los productos tengan
# stock en los almacenes origen. Como la nota de ingreso
# solo permite enviar stock al almacen 06732F01 (farmacia
# principal), necesitamos distribuir desde ahi hacia las
# demas farmacias usando notas de salida.
#
# Este archivo genera salidas simuladas desde 06732F01
# hacia F02, F03, F04 y F05 con los productos exactos que
# cada farmacia necesita como origen en las salidas del SP.
#
# MULTIPLICADOR = 2: se envia el doble del stock necesario
# para que sobre margen en caso de repetir pruebas.
# =========================================================


def generar_salidas_para_prueba() -> tuple[Salidas, ...]:
    ORIGEN = "06732F01"
    VIRTUAL = "06732F0101"
    CONCEPTO = "DISTRIBUCION"
    MULTIPLICADOR = 1

    salidas = [
        Salidas(
            almacen_origen=ORIGEN,
            almacen_destino="06732F02",
            almacen_virtual_origen=VIRTUAL,
            concepto=CONCEPTO,
            medicamentos=[
                Medicamento(codigo="06471", cantidad=50 * MULTIPLICADOR),
            ],
        ),
        Salidas(
            almacen_origen=ORIGEN,
            almacen_destino="06732F03",
            almacen_virtual_origen=VIRTUAL,
            concepto=CONCEPTO,
            medicamentos=[
                Medicamento(codigo="01537", cantidad=70 * MULTIPLICADOR),
            ],
        ),
        Salidas(
            almacen_origen=ORIGEN,
            almacen_destino="06732F04",
            almacen_virtual_origen=VIRTUAL,
            concepto=CONCEPTO,
            medicamentos=[
                Medicamento(codigo="18157", cantidad=7 * MULTIPLICADOR),
            ],
        ),
        Salidas(
            almacen_origen=ORIGEN,
            almacen_destino="06732F05",
            almacen_virtual_origen=VIRTUAL,
            concepto=CONCEPTO,
            medicamentos=[
                Medicamento(codigo="01537", cantidad=55 * MULTIPLICADOR),
                Medicamento(codigo="04901", cantidad=3 * MULTIPLICADOR),
            ],
        ),
    ]

    return tuple(salidas)
