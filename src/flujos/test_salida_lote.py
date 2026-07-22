import sys
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from src.config import SISMED_PASSWORD, SISMED_USERNAME
from src.flujos.salida import procesar_salidas
from src.models.Medicamento import Medicamento
from src.models.Salidas import Salidas


if __name__ == "__main__":
    salida = Salidas(
        almacen_origen="06732F01",
        almacen_destino="06732F03",
        almacen_virtual_origen="06732F0101",
        concepto="DISTRIBUCION",
        medicamentos=[
            Medicamento(codigo="00111", cantidad=3, lote="2031775"),
            Medicamento(codigo="10230", cantidad=1, lote="003038"),
            Medicamento(codigo="00830", cantidad=1, lote="2505029"),
            Medicamento(codigo="18381", cantidad=1, lote="203071024"),
            Medicamento(codigo="19840", cantidad=1, lote="LTnoexis"),
        ],
    )
    procesar_salidas((salida,))
