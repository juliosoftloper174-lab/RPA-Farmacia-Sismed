from os import environ

from dotenv import load_dotenv
from loguru import logger

from .sidmed.ingreso import Ingreso, procesar_ingresos
from .sidmed.pedido import (
    Cliente,
    Diagnostico,
    Farmacia,
    FormaPago,
    Pedido,
    Prescriptor,
    Producto,
    procesar_pedidos,
)
from .sidmed.salidas import ProductoIngreso, Salidas, procesar_salidas
from .sidmed.wrapper import Sismed

load_dotenv()

sismed_username = environ["SISMED_USERNAME"]
sismed_password = environ["SISMED_PASSWORD"]


class Database:
    def __init__(self):
        pass

    def login(self, db_name: str, db_user: str, db_pass: str) -> None:
        return None

    def obtener_pedidos(self) -> list[dict]:
        return []

    def obtener_ingresos(self) -> list[dict]:
        return []  # TODO: Tengo sueño lo hago mañana

    def obtener_salidas(self) -> list[dict]:
        return []


def main() -> None:

    logger.info("Iniciando...")

    db: Database = Database()
    db.login(environ["DB_NAME"], environ["DB_USER"], environ["DB_PASS"])

    raw_pedidos: list[dict] = db.obtener_pedidos()
    raw_ingresos: list[dict] = db.obtener_ingresos()
    raw_salidas: list[dict] = Database().obtener_salidas()

    pedidos = tuple(Pedido(**d) for d in raw_pedidos)
    ingresos = tuple(Ingreso(**d) for d in raw_ingresos)
    salidas = tuple(Salidas(**d) for d in raw_salidas)

    salida = Salidas(
        almacen_origen="06732F01",  # código correcto
        almacen_destino="FARM - HOSP. DE RIOJA",
        concepto="DISTRIBUCION",  # ahora sí funciona (string)
        referencia="TEST",
        productos=[ProductoIngreso("00390", "L001", 1, 1, 5)],
    )

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

    procesar_pedidos(pedidos)
    procesar_ingresos(ingresos)
    procesar_salidas(salidas)

    return logger.info("Finalizando...")


if __name__ == "__main__":
    main()
