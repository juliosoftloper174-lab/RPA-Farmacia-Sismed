from src.models.cliente import Cliente
from src.models.diagnostico import Diagnostico
from src.models.farmacia import Farmacia
from src.models.forma_pago import FormaPago
from src.models.Medicamento import Medicamento
from src.models.pedido import Pedido
from src.models.enums import TipoReceta


def generar_pedidos_simulados() -> tuple[list[Pedido], list, list]:
    """Retorna (pedidos, [], []) simulados para pruebas.
    3 pedidos con las 3 formas de pago, misma farmacia, mismo cliente, mismo producto.
    """
    farmacia = Farmacia("06732F02")
    cliente = Cliente("00024201")

    medicamento = Medicamento(codigo="00200", cantidad=1)

    pedidos = [
        Pedido(
            farmacia=farmacia,
            cliente=cliente,
            forma_pago=FormaPago.CONTADO,
            tipo_receta=TipoReceta.SIN_NUMERO,
            Medicamentos=[medicamento],
            diagnosticos=[Diagnostico("R05X")],
        ),
        Pedido(
            farmacia=farmacia,
            cliente=cliente,
            forma_pago=FormaPago.SIS,
            tipo_receta=TipoReceta.SIN_NUMERO,
            Medicamentos=[medicamento],
            diagnosticos=[Diagnostico("R05X")],
            fua="12345678",
        ),
        Pedido(
            farmacia=farmacia,
            cliente=cliente,
            forma_pago=FormaPago.INTERVENCION_SANITARIA,
            tipo_receta=TipoReceta.SIN_NUMERO,
            Medicamentos=[medicamento],
            diagnosticos=[Diagnostico("R05X")],
        ),
    ]

    return pedidos, [], []
