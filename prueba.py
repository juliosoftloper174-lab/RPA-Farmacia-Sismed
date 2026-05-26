from loguru import logger

from src.sidmed.ingreso import Ingreso, procesar_ingresos
from src.models.pedido import (
    Cliente,
    Diagnostico,
    Farmacia,
    FormaPago,
    Pedido,
    Prescriptor,
    procesar_pedidos,
)
from src.models.Medicamento import Medicamento, ProductoIngreso
from src.models.Salidas import Salidas
from src.sidmed.salidas import procesar_salidas


def main() -> None:
    """Estoy probando aqui porque no hay base de datos aun para usar el main."""

    salida = Salidas(
        almacen_origen="06732F01",  # código correcto
        almacen_destino="FARM - HOSP. DE RIOJA",
        concepto="DISTRIBUCION",  # ahora sí funciona (string)
        referencia="TEST",
        medicamentos=[ProductoIngreso("00390", 1, "L001", 1, 5)],
    )
    salidas = (salida,)

    pedido = Pedido(
        farmacia=Farmacia("HOSP. CENTRAL", "06732F02"),
        cliente=Cliente("ABAD CARDENAS, SELOMIT ABIGAIL"),
        prescriptor=Prescriptor("14571"),
        forma_pago=FormaPago.SIS,
        diagnosticos=[
            Diagnostico("R100"),
            Diagnostico("R05X"),
            Diagnostico("K750"),
        ],
        Medicamentos=[
            Medicamento("ACIDO ACETILSALICILICO - 500 mg - TABLET -", 3),
            Medicamento("ACIDO ACETILSALICILICO - 100 mg - TABLET -", 7),
            Medicamento("ACIDO TRANEXAMICO - 250 mg - TABLET -", 6),
            Medicamento("ACIDO TRANEXAMICO - 1 g - INYECT - 10 mL", 4),
        ],
        fua="786636652",
    )
    pedidos = (pedido,)

    ingreso = Ingreso(
        almacen_destino="FARM",
        concepto="DISTRIBUCION",
        medicamentos=[
            ProductoIngreso("30588", 27, "2080015", 0, 0),
            ProductoIngreso("30588", 7, "2080015", 4, 3),
        ],
    )
    ingresos = (ingreso,)

    procesar_pedidos(pedidos)
    procesar_ingresos(ingresos)
    procesar_salidas(salidas)

    return logger.info("Finalizando...")


if __name__ == "__main__":
    main()
