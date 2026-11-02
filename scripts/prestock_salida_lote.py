import sys
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from src.flujos.ingreso import procesar_ingresos
from src.models.ingreso import Ingreso
from src.models.Medicamento import Medicamento

# Mismos codigos/lotes que usa src/flujos/test_salida_lote.py.
# El ingreso entra a 06732F01 para que luego la salida 06732F01 -> 06732F03
# encuentre stock suficiente.
PRODUCTOS = [
    ("00111", 20, "2031775"),
    ("10230", 20, "003038"),
    ("00830", 20, "2505029"),
    ("18381", 20, "203071024"),
    ("19840", 20, "LTnoexis"),
]

TIPO_SUM = "SISMED-COMPRA NACIONAL (CN)"
FUENTE_FIN = "Donaciones y Transferencias (DYT)"
REG_SAN = "SIN_REG_SAN"
FECHA_VEN = "2026/12/30"
PRECIO = 0.01


def generar_ingreso_prestock() -> tuple[Ingreso, ...]:
    medicamentos = [
        Medicamento(
            codigo=codigo,
            cantidad=cantidad,
            lote=lote,
            tipo_sum=TIPO_SUM,
            fuente_fin=FUENTE_FIN,
            registro_sanitario=REG_SAN,
            fecha_vencimiento=FECHA_VEN,
            precio_compra=PRECIO,
        )
        for codigo, cantidad, lote in PRODUCTOS
    ]
    return (
        Ingreso(
            almacen_destino="06732F01",
            almacen_virtual_origen="030S0101",
            concepto="DISTRIBUCION",
            medicamentos=medicamentos,
        ),
    )


if __name__ == "__main__":
    procesar_ingresos(generar_ingreso_prestock())
