from os import environ

from dotenv import load_dotenv
from loguru import logger

from .sidmed.ingreso import Ingreso, procesar_ingresos
from .models.cliente import Cliente
from .models.diagnostico import Diagnostico
from .models.farmacia import Farmacia
from .models.prescriptor import Prescriptor
from .models.producto import Producto
from .sidmed.pedido import FormaPago, Pedido, procesar_pedidos
from .sidmed.salidas import ProductoIngreso, Salidas, procesar_salidas
from .sidmed.wrapper import Sismed
from .models.enums import TipoReceta

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

    # Database flow

    db: Database = Database()
    # db.login(environ["DB_NAME"], environ["DB_USER"], environ["DB_PASS"])

    raw_pedidos: list[dict] = db.obtener_pedidos()
    raw_ingresos: list[dict] = db.obtener_ingresos()
    raw_salidas: list[dict] = db.obtener_salidas()

    pedidos = tuple(Pedido(**d) for d in raw_pedidos)
    ingresos = tuple(Ingreso(**d) for d in raw_ingresos)
    salidas = tuple(Salidas(**d) for d in raw_salidas)

    # Simulate database flow

    # Datos de prueba basados en los tests
    pedido = Pedido(
        farmacia=Farmacia("06732F02"),
        cliente=Cliente("00033257"),
        prescriptor=Prescriptor("14571"),
        forma_pago=FormaPago.INTERVENCION_SANITARIA,
        tipo_receta=TipoReceta.SIN_NUMERO,
        diagnosticos=[Diagnostico("R100"), Diagnostico("R05X"), Diagnostico("K750")],
        productos=[
            Producto("00091", 1),
            Producto("36413", 1),
            Producto("10145", 1),
        ],
        fua="786636652",
        ups_codigo="301",
    )

    ingreso = Ingreso(
        almacen_origen="ALM. ANEXO RIOJA - SAN MARTIN   ",
        almacen_destino="06732F01",
        concepto="DISTRIBUCION",
        referencia="B.O.T",
        ups_codigo="407",
        productos=[
            ProductoIngreso(
                "30588",
                "2080015",
                1,
                "SISMED-CENTRALIZADO (SC)",
                "Contribuciones a Fondos (CON)",
            ),
            ProductoIngreso(
                "30588",
                "2080015",
                1,
                "SISMED-COMPRA REGIONAL (CR)",
                "Recursos Determinados (RDE)",
            ),
        ],
    )

    salida = Salidas(
        almacen_origen="06732F02",
        almacen_destino="06732F01",
        almacen_virtual_origen="06732F0201",
        concepto="DISTRIBUCION",
        referencia="TEST",
        productos=[
            ProductoIngreso("01205", "L001", 1, 1, 5),
            ProductoIngreso(
                "00947",
                "2080015",
                2,
                "SISMED-COMPRA REGIONAL (CR)",
                "Recursos Determinados (RDE)",
            ),
        ],
    )

    pedidos = (pedido,)
    ingresos = (ingreso,)
    salidas = (salida,)

    # TODO: por ahora hacer que se cierren las ventanas al terminar, hasta conseguir una forma de reutilizar la misma ventana.

    procesar_pedidos(pedidos)
    procesar_ingresos(ingresos)
    procesar_salidas(salidas)

    return logger.info("Finalizando...")


if __name__ == "__main__":
    main()
