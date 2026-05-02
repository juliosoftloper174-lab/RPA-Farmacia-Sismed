from typing import List

from .cliente import Cliente
from .diagnostico import Diagnostico
from .farmacia import Farmacia
from .forma_pago import FormaPago
from .prescriptor import Prescriptor
from .producto import Producto


class Pedido:
    def __init__(
        self,
        farmacia: Farmacia,
        cliente: Cliente,
        prescriptor: Prescriptor,
        forma_pago: FormaPago,
        diagnosticos: List[Diagnostico],
        productos: List[Producto],
        fua: str,
    ):
        self.farmacia = farmacia
        self.cliente = cliente
        self.prescriptor = prescriptor
        self.forma_pago = forma_pago
        self.diagnosticos = diagnosticos
        self.productos = productos
        self.fua = fua
