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
        tipo_movimiento: str = "SALIDA",
        # Campos para salidas externas (doc 05)
        tipo_documento: str = "06",
        tipo_movimiento_sp: str = "",
        concepto_sp: str = "",
        nseap: str = "",
        concepto_sismed: str = "",
        destino_ksalud: str = "",
        destino_sismed: str = "",
        coordenadas_concepto: list[tuple[int, int]] | None = None,
        ups_codigo: str = "",
    ):
        self.almacen_origen = almacen_origen
        self.almacen_destino = almacen_destino
        self.almacen_virtual_origen = almacen_virtual_origen
        self.concepto = concepto
        self.medicamentos = medicamentos
        self.correlativo_ksalud = correlativo_ksalud
        self.update_key = update_key
        self.tipo_movimiento = tipo_movimiento

        # Salidas externas
        self.tipo_documento = tipo_documento
        self.tipo_movimiento_sp = tipo_movimiento_sp
        self.concepto_sp = concepto_sp
        self.nseap = nseap
        self.concepto_sismed = concepto_sismed
        self.destino_ksalud = destino_ksalud
        self.destino_sismed = destino_sismed
        self.coordenadas_concepto = coordenadas_concepto or []
        self.ups_codigo = ups_codigo

    @property
    def es_salida_externa(self) -> bool:
        return self.tipo_documento == "05"
