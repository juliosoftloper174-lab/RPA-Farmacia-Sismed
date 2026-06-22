from .cliente import Cliente
from .diagnostico import Diagnostico
from .farmacia import Farmacia
from .forma_pago import FormaPago
from .prescriptor import Prescriptor
from .Medicamento import Medicamento
from pydantic import BaseModel, ConfigDict
from .enums import TipoReceta

_fua_counter: int = 0


def generar_fua_ficticio() -> str:
    global _fua_counter
    _fua_counter += 1
    return f"{_fua_counter:08d}"


class Pedido(BaseModel):
    model_config = ConfigDict(
        arbitrary_types_allowed=True,
    )

    farmacia: Farmacia
    cliente: Cliente
    prescriptor: Prescriptor | None = None
    forma_pago: FormaPago
    tipo_receta: TipoReceta
    diagnosticos: list[Diagnostico] = []
    Medicamentos: list[Medicamento]
    fua: str | None = None
    ups_codigo: str = "301"

    def obtener_revisiones(self) -> list[str]:
        motivos: list[str] = []
        if self.forma_pago == FormaPago.SIS and self.fua is None:
            motivos.append("FUA es obligatorio cuando forma_pago es SIS")
        if self.tipo_receta != TipoReceta.SIN_NUMERO:
            motivos.append(
                f"Tipo de receta no es SIN_NUMERO, se recibió: {self.tipo_receta.value}"
            )
        return motivos
