from src.models.Medicamento import Medicamento


class Salidas:
    def __init__(
        self,
        almacen_origen: str,
        almacen_destino: str,
        almacen_virtual_origen: str,
        concepto: str,
        medicamentos: list[Medicamento],
        correlativo_ksalud: str = "",
        update_key: tuple[str, ...] | None = None,
    ):
        self.almacen_origen = almacen_origen
        self.almacen_destino = almacen_destino
        self.almacen_virtual_origen = almacen_virtual_origen
        self.concepto = concepto
        self.medicamentos = medicamentos
        self.correlativo_ksalud = correlativo_ksalud
        self.update_key = update_key
