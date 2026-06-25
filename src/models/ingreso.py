from src.models.Medicamento import Medicamento


class Ingreso:
    def __init__(
        self,
        almacen_destino: str,
        almacen_virtual_origen: str,
        concepto: str,
        medicamentos: list[Medicamento],
        update_key: tuple[str, ...] | None = None,
    ):
        self.almacen_destino = almacen_destino
        self.almacen_virtual_origen = almacen_virtual_origen
        self.concepto = concepto
        self.medicamentos = medicamentos
        self.update_key = update_key
