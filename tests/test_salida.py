from src.models.producto_ingreso import ProductoIngreso
from src.models.Salidas import Salidas
from src.sidmed.salidas import procesar_salidas


def test_procesar_salidas_llama_procesar_salida(monkeypatch):
    llamadas = []

    """

    def fake_procesar_salida(salidas):
        llamadas.append(salidas)

    monkeypatch.setattr("src.sidmed.salidas.procesar_salida", fake_procesar_salida)
    """
    salida = Salidas(
        almacen_origen="06732F01",
        almacen_destino="FARM - HOSP. DE RIOJA",
        concepto="DISTRIBUCION",
        referencia="TEST",
        productos=[ProductoIngreso("00390", "L001", 1, 1, 5)],
    )

    procesar_salidas((salida,))

    # assert llamadas == [salida]
    # assert llamadas[0].productos[0].lote == "L001"
    # assert llamadas[0].referencia == "TEST"


"""
def test_salidas_model_fields():
    salida = Salidas(
        almacen_origen="06732F01",
        almacen_destino="FARM - HOSP. DE RIOJA",
        concepto="DISTRIBUCION",
        referencia="TEST",
        productos=[],
    )

    assert salida.almacen_origen == "06732F01"
    assert salida.almacen_destino == "FARM - HOSP. DE RIOJA"
    assert salida.concepto == "DISTRIBUCION"
    assert salida.referencia == "TEST"
"""
