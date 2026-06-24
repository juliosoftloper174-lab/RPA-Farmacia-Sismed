from src.models.cliente import Cliente
from src.models.diagnostico import Diagnostico
from src.models.farmacia import Farmacia
from src.models.forma_pago import FormaPago
from src.models.Medicamento import Medicamento
from src.models.pedido import Pedido
from src.models.enums import TipoReceta


def generar_pedidos_simulados() -> tuple[list[Pedido], list, list]:
    """Retorna (pedidos, [], []) simulados para pruebas.
    3 pedidos: 1ro con cliente inexistente (test de fallo), 2do y 3ro normales.
    """
    farmacia = Farmacia("06732F02")
    cliente_normal = Cliente("43414397")
    cliente_inexistente = Cliente("42659892")

    medicamento = Medicamento(codigo="00200", cantidad=1)

    pedidos = [
        # 1er pedido: cliente que NO existe en SISMED (solo en ksalud)
        Pedido(
            farmacia=farmacia,
            cliente=cliente_inexistente,
            forma_pago=FormaPago.CONTADO,
            tipo_receta=TipoReceta.SIN_NUMERO,
            Medicamentos=[medicamento],
            diagnosticos=[Diagnostico("R05X")],
        ),
        Pedido(
            farmacia=farmacia,
            cliente=cliente_normal,
            forma_pago=FormaPago.SIS,
            tipo_receta=TipoReceta.SIN_NUMERO,
            Medicamentos=[medicamento],
            diagnosticos=[Diagnostico("R05X")],
            fua="12345678",
        ),
        Pedido(
            farmacia=farmacia,
            cliente=cliente_normal,
            forma_pago=FormaPago.INTERVENCION_SANITARIA,
            tipo_receta=TipoReceta.SIN_NUMERO,
            Medicamentos=[medicamento],
            diagnosticos=[Diagnostico("R05X")],
        ),
    ]

    return pedidos, [], []
