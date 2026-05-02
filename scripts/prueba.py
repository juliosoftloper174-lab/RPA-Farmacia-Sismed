from loguru import logger

from src.sidmed.ingreso import Ingreso, procesar_ingresos
from src.sidmed.pedido import (
    Cliente,
    Diagnostico,
    Farmacia,
    FormaPago,
    Pedido,
    Prescriptor,
    Producto,
    procesar_pedidos,
)
from src.sidmed.salidas import ProductoIngreso, Salidas, procesar_salidas


def main() -> None:
    """Estoy probando aqui porque no hay base de datos aun para usar el main."""

    salida = Salidas(
        almacen_origen="06732F01",  # código correcto
        almacen_destino="FARM - HOSP. DE RIOJA",
        concepto="DISTRIBUCION",  # ahora sí funciona (string)
        referencia="TEST",
        productos=[ProductoIngreso("00390", "L001", 1, 1, 5)],
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
        productos=[
            Producto("ACIDO ACETILSALICILICO - 500 mg - TABLET -", 3),
            Producto("ACIDO ACETILSALICILICO - 100 mg - TABLET -", 7),
            Producto("ACIDO TRANEXAMICO - 250 mg - TABLET -", 6),
            Producto("ACIDO TRANEXAMICO - 1 g - INYECT - 10 mL", 4),
        ],
        fua="786636652",
    )
    pedidos = (pedido,)

    ingreso = Ingreso(
        almacen_origen="ALM. ANEXO RIOJA",
        almacen_destino="FARM",
        concepto="DISTRIBUCION",
        referencia="B.O.T",
        productos=[
            ProductoIngreso("30588", "2080015", 27, 0, 0),
            ProductoIngreso("30588", "2080015", 7, 4, 3),
        ],
    )
    ingresos = (ingreso,)

    procesar_pedidos(pedidos)
    procesar_ingresos(ingresos)
    procesar_salidas(salidas)

    return logger.info("Finalizando...")


if __name__ == "__main__":
    main()
