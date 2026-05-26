from enum import StrEnum


class TipoReceta(StrEnum):
    """NOTE: Others may exists."""

    SIN_NUMERO = "Receta Sin Numero"
    NUMERADA = "Receta Numerada"
    ESTANDAR = "Receta Estandar"
