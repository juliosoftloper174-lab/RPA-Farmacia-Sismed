from dataclasses import dataclass


@dataclass
class Producto:
    codigo: str
    cantidad: int = 1
