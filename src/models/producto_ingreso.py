class ProductoIngreso:
    def __init__(
        self,
        codigo: str,
        lote: str,
        cantidad: int,
        tipo_sum: int,
        fuente_fin: int,
    ):
        self.codigo = codigo
        self.lote = lote
        self.cantidad = cantidad
        self.tipo_sum = tipo_sum
        self.fuente_fin = fuente_fin
