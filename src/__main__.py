from src.models.Medicamento import Medicamento

from .logger import logger
from loguru import logger

from .sidmed.ingreso import Ingreso, procesar_ingresos
from .models.cliente import Cliente
from .models.diagnostico import Diagnostico
from .models.farmacia import Farmacia
from .models.prescriptor import Prescriptor
from .models.producto import Producto
from .sidmed.pedido import FormaPago, Pedido, procesar_pedidos
from .sidmed.salidas import Medicamento, Salidas, procesar_salidas
from .sidmed.wrapper import Sismed
from .models.enums import TipoReceta


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


@logger.catch
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
        forma_pago=FormaPago.SIS,
        tipo_receta=TipoReceta.SIN_NUMERO,
        diagnosticos=[Diagnostico("R100"), Diagnostico("R05X"), Diagnostico("K750")],
        Medicamentos=[
            Medicamento("00091", 1),
            Medicamento("10155", 1),
            Medicamento("10145", 1),
        ],
        fua="786636652",
        ups_codigo=None,  # SE MANTENDRA ESTATICO 19/05/2026
    )

    ingreso = Ingreso(
        almacen_origen="ALM. ANEXO RIOJA - SAN MARTIN",  # SE MANTENDRA ESTATICO 19/05/2026
        almacen_destino="06732F01",  # ESTE DATO SE OBTIENE DE LA BD, SI ES DIFERENTE A 06732F01 NO SE PUEDE CONTINUAR, AGREGAR VALIDACION CON PYTHON EN EL MODELO.
        almacen_virtual_origen="030S0101",  # SE ME PASARA EL TIPO, YO ME ENCARGARE DE MAPEAR CUANDO ES SIMED (S) = 030S0101 Y SI ES DONACION (D) = 030S0102
        concepto="DISTRIBUCION",  # CONSULTAR A LEO
        ups_codigo="407",  # SE MANTENDRA ESTATICO 19/05/2026
        medicamentos=[
            # medicamento lote nuevo
            Medicamento(
                "36394",
                400,
                "LteNvo1",
                "SISMED-COMPRA NACIONAL (CN)",
                "Contribuciones a Fondos (CON)",
                "SIN_REG_SAN",
                "2029/12/20",
                "500",
            ),
            # medicamento con lote que si existe y trae datos
            Medicamento(
                "36394",
                400,
                "DE5FDJ6D",
                "SISMED-TRANSF Y PRESTAMOS UE (ST) TP",
                "Contribuciones a Fondos (CON)",
                "SIN_REG_SAN",
                "2029/12/20",
                "500",
            ),
            Medicamento(
                "36394",
                400,
                "LteNvo2",
                "SISMED-COMPRA NACIONAL (CN)",
                "Contribuciones a Fondos (CON)",
                "SIN_REG_SAN",
                "2029/12/20",
                "500",
            ),
            Medicamento(
                "36394",
                950,
                "DE5FDJ6D",
                "SISMED-TRANSF Y PRESTAMOS UE (ST) TP",
                "Recursos Determinados (RDE)",
                "SIN_REG_SAN",
                "2029/12/20",
                "500",
            ),
        ],
    )

    salida = Salidas(
        almacen_origen="06732F01",
        almacen_destino="06732F02",
        almacen_virtual_origen="06732F0101",
        concepto="DISTRIBUCION",
        medicamentos=[
            Medicamento("36394", 900, "DE5FDJ6D", 1, 5),
            Medicamento("00223", 1, "L001", 1, 5),
        ],
    )

    pedidos = (pedido,)
    ingresos = (ingreso,)
    salidas = (salida,)

    # TODO: por ahora hacer que se cierren las ventanas al terminar, hasta conseguir una forma de reutilizar la misma ventana.

    for _ in range(2):

        # procesar_ingresos(ingresos)
        # procesar_salidas(salidas)

        # funciona para que se registren 4 pedidos en una sola vez con un solo login.
        pedidos = tuple(pedido for _ in range(4))

        procesar_pedidos(pedidos)
    return logger.info("Finalizando...")


if __name__ == "__main__":
    main()
