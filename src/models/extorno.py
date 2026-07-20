class Extorno:
    def __init__(
        self,
        farmacia: str,
        cliente_dni: str,
        fecha: str,
        medicamentos: list,
        correlativo_ksalud: str = "",
        update_key: tuple[str, ...] | None = None,
    ):
        self.farmacia = farmacia
        self.cliente_dni = cliente_dni
        self.fecha = fecha
        self.medicamentos = medicamentos
        self.correlativo_ksalud = correlativo_ksalud
        self.update_key = update_key
