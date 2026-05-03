class ProductoIngreso:
    def __init__(
        self,
        codigo: str,
        lote: str,
        cantidad: int,
        tipo_sum: str,
        fuente_fin: str,
    ):
        self.codigo = codigo
        self.lote = lote
        self.cantidad = cantidad
        self.tipo_sum = tipo_sum
        self.fuente_fin = fuente_fin
