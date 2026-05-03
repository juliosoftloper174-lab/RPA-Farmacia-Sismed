from src.models.cliente import Cliente
from src.models.diagnostico import Diagnostico
from src.models.farmacia import Farmacia
from src.models.forma_pago import FormaPago
from src.models.pedido import Pedido
from src.models.prescriptor import Prescriptor
from src.models.producto import Producto
from src.sidmed.pedido import procesar_pedidos

from src.models.enums import TipoReceta


def test_procesar_pedidos_llama_procesar_pedido(monkeypatch):
    llamadas = []
    """
    def fake_procesar_pedido(pedido):
        llamadas.append(pedido)

    monkeypatch.setattr("src.sidmed.pedido.procesar_pedido", fake_procesar_pedido)
    """
    pedido = Pedido(
        farmacia=Farmacia("HOSP. CENTRAL", "06732F02"),
        cliente=Cliente("00033257", "ABAD CARDENAS, SELOMIT ABIGAIL"),
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
        ups_codigo="407",
    )

    procesar_pedidos((pedido,))


"""
    assert llamadas == [pedido]
    assert llamadas[0].fua == "786636652"
"""

"""
def test_pedido_model_fields():
    farmacia = Farmacia("HOSP. CENTRAL", "06732F02")
    cliente = Cliente("ABAD CARDENAS, SELOMIT ABIGAIL")
    prescriptor = Prescriptor("14571")
    producto = Producto("ACIDO ACETILSALICILICO - 500 mg - TABLET -", 3)

    assert farmacia.nombre == "HOSP. CENTRAL"
    assert farmacia.codigo == "06732F02"
    assert cliente.nombre == "ABAD CARDENAS, SELOMIT ABIGAIL"
    assert prescriptor.codigo == "14571"
    assert producto.nombre.startswith("ACIDO ACETILSALICILICO")
    assert producto.cantidad == 3
"""
