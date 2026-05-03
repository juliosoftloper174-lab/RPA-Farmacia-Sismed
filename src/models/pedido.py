from .cliente import Cliente
from .diagnostico import Diagnostico
from .farmacia import Farmacia
from .forma_pago import FormaPago
from .prescriptor import Prescriptor
from .producto import Producto
from pydantic import BaseModel, ConfigDict, model_validator
from .enums import TipoReceta


class Pedido(BaseModel):
    model_config = ConfigDict(
        # Le permite a pydantic aceptar instancias de clases personalizadas y otras clases de pydantic, como Farmacia, Cliente, etc., sin intentar validarlas o convertirlas.
        arbitrary_types_allowed=True,
    )

    farmacia: Farmacia
    cliente: Cliente
    prescriptor: Prescriptor
    forma_pago: FormaPago
    tipo_receta: TipoReceta
    diagnosticos: list[Diagnostico]
    productos: list[Producto]
    fua: str | None = None
    ups_codigo: str | None = None

    @model_validator(mode="after")
    def validate_condicionales(self):
        if self.forma_pago == FormaPago.INTERVENCION_SANITARIA:
            if self.ups_codigo is None:
                raise ValueError(
                    "ups_codigo es obligatorio cuando forma_pago es INTERVENCION_SANITARIA"
                )
        else:
            if self.ups_codigo is not None:
                raise ValueError(
                    "ups_codigo debe ser None cuando forma_pago no es INTERVENCION_SANITARIA"
                )

        if self.forma_pago == FormaPago.SIS:
            if self.fua is None:
                raise ValueError("fua es obligatorio cuando forma_pago es SIS")

        return self
