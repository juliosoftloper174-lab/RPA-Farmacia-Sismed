class Medicamento:
    def __init__(
        self,
        codigo: str,
        cantidad: int,
        lote: str = None,
        tipo_sum: str = None,
        fuente_fin: str = None,
        registro_sanitario: str = None,
        fecha_vencimiento: str = None,
        precio_compra: float = None,
    ):
        self.codigo = codigo
        self.cantidad = cantidad
        self.lote = lote
        self.tipo_sum = tipo_sum
        self.fuente_fin = fuente_fin
        self.registro_sanitario = registro_sanitario
        self.fecha_vencimiento = fecha_vencimiento
        self.precio_compra = precio_compra


# Alias para mantener compatibilidad con ingreso y salida
ProductoIngreso = Medicamento
