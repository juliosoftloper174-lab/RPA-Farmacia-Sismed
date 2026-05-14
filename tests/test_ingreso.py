from src.models.ingreso import Ingreso
from src.models.producto_ingreso import ProductoIngreso
from src.sidmed.ingreso import procesar_ingresos


def test_procesar_ingresos_llama_procesar_ingreso(monkeypatch):
    llamadas: list = list()

    """
    def fake_procesar_ingreso(ingreso):
        llamadas.append(ingreso)    

    monkeypatch.setattr("src.sidmed.ingreso.procesar_ingreso", fake_procesar_ingreso)
    """
    ingreso = Ingreso(
        almacen_origen="ALM. ANEXO RIOJA - SAN MARTIN   ",
        almacen_destino="06732F01",
        almacen_virtual_origen="030S0101",
        concepto="DISTRIBUCION",
        referencia="B.O.T",  # no creo exista en la bd pero se puede dejar harcodeado
        ups_codigo="407",
        productos=[
            ProductoIngreso(
                "30588",
                "2080015",
                400,
                "SISMED-COMPRA NACIONAL (CN)",
                "Contribuciones a Fondos (CON)",
            ),
        ],
    )

    procesar_ingresos((ingreso,))
    return None


"""
    assert llamadas == [ingreso]
    assert llamadas[0].productos[0].cantidad == 27
    assert llamadas[0].concepto == "DISTRIBUCION"
"""

"""
def test_producto_ingreso_model_fields():
    producto = ProductoIngreso("30588", "2080015", 7, 4, 3)

    assert producto.codigo == "30588"
    assert producto.lote == "2080015"
    assert producto.cantidad == 7
    assert producto.tipo_sum == 4
    assert producto.fuente_fin == 3
"""
