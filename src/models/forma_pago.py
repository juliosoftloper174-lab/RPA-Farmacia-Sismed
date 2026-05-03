from enum import StrEnum


class FormaPago(StrEnum):
    """NOTE: Others may exists."""

    CONTADO = "CONTADO"
    INTERVENCION_SANITARIA = "INTERVENCION SANITAR"
    SIS = "SIS"
