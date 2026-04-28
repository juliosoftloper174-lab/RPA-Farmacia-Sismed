from dataclasses import dataclass


@dataclass
class Producto:
    nombre: str
    cantidad: int = 1
