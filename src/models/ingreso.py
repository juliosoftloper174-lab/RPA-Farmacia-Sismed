from src.models.producto_ingreso import ProductoIngreso


class Ingreso:
    def __init__(
        self,
        almacen_origen: str,
        almacen_destino: str,
        concepto: str,
        referencia: str,
        productos: list[ProductoIngreso],
    ):
        self.almacen_origen = almacen_origen
        self.almacen_destino = almacen_destino
        self.concepto = concepto
        self.referencia = referencia
        self.productos = productos
