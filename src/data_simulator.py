from src.models.cliente import Cliente
from src.models.diagnostico import Diagnostico
from src.models.farmacia import Farmacia
from src.models.forma_pago import FormaPago
from src.models.ingreso import Ingreso
from src.models.pedido import Pedido
from src.models.prescriptor import Prescriptor
from src.models.Medicamento import Medicamento, ProductoIngreso
from src.models.Salidas import Salidas
from src.models.enums import TipoReceta

try:
    import pandas as pd

    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False


def get_datos_simulados():
    """Devuelve datos simulados para pruebas: 2 pedidos, 2 ingresos, 2 salidas."""

    pedidos = [
        Pedido(
            farmacia=Farmacia("HOSP. CENTRAL", "06732F02"),
            cliente=Cliente("00033257", "ABAD CARDENAS, SELOMIT ABIGAIL"),
            prescriptor=Prescriptor("14571"),
            forma_pago=FormaPago.SIS,
            tipo_receta=TipoReceta.SIN_NUMERO,
            diagnosticos=[
                Diagnostico("R100"),
                Diagnostico("R05X"),
                Diagnostico("K750"),
            ],
            Medicamentos=[
                Medicamento("00091", 3),
                Medicamento("18931", 1),
            ],
            fua="786636652",
        ),
        Pedido(
            farmacia=Farmacia("HOSP. CENTRAL", "06732F01"),
            cliente=Cliente("00033258", "OTRO CLIENTE"),
            prescriptor=Prescriptor("00145"),
            forma_pago=FormaPago.CONTADO,
            tipo_receta=TipoReceta.SIN_NUMERO,
            diagnosticos=[Diagnostico("R100")],
            Medicamentos=[Medicamento("00145", 2)],
        ),
    ]

    ingresos = [
        Ingreso(
            almacen_origen="ALM. ANEXO RIOJA",
            almacen_destino="FARM",
            concepto="DISTRIBUCION",
            referencia="B.O.T",
            medicamentos=[
                ProductoIngreso("30588", 27, "2080015", 0, 0),
                ProductoIngreso("30588", 7, "2080015", 4, 3),
            ],
        ),
        Ingreso(
            almacen_origen="ALM. CENTRAL",
            almacen_destino="FARM",
            concepto="COMPRA",
            referencia="REF2",
            medicamentos=[ProductoIngreso("12345", 10, "LOTE1", 1, 2)],
        ),
    ]

    salidas = [
        Salidas(
            almacen_origen="06732F01",
            almacen_destino="FARM - HOSP. DE RIOJA",
            almacen_virtual_origen="06732F0201",
            concepto="DISTRIBUCION",
            referencia="TEST",
            medicamentos=[ProductoIngreso("00390", 1, "L001", 1, 5)],
        ),
        Salidas(
            almacen_origen="06732F01",
            almacen_destino="FARM - HOSP. DE RIOJA",
            almacen_virtual_origen="06732F0201",
            concepto="VENTA",
            referencia="TEST2",
            medicamentos=[ProductoIngreso("00400", 2, "L002", 1, 5)],
        ),
    ]

    return pedidos, ingresos, salidas


def get_datos_from_excel(file_path: str):
    """Lee datos de un archivo Excel y devuelve listas de objetos.

    El Excel debe tener hojas: 'pedidos', 'ingresos', 'salidas' con columnas específicas.
    """
    if not PANDAS_AVAILABLE:
        raise ImportError(
            "pandas no está instalado. Instala con: pip install pandas openpyxl"
        )

    # Leer hojas
    df_pedidos = pd.read_excel(file_path, sheet_name="pedidos")
    df_ingresos = pd.read_excel(file_path, sheet_name="ingresos")
    df_salidas = pd.read_excel(file_path, sheet_name="salidas")

    # Mapear pedidos (simplificado, ajustar según columnas reales)
    pedidos = []
    for _, row in df_pedidos.iterrows():
        cliente_codigo = row.get("cliente_codigo") or row.get("cliente_nombre")
        cliente_nombre = row.get("cliente_nombre", "")

        pedido = Pedido(
            farmacia=Farmacia(row["farmacia_nombre"], row["farmacia_codigo"]),
            cliente=Cliente(cliente_codigo, cliente_nombre),
            prescriptor=Prescriptor(row["prescriptor_codigo"]),
            forma_pago=FormaPago(row["forma_pago"]),  # Asumir string que mapea a enum
            tipo_receta=TipoReceta.SIN_NUMERO,
            diagnosticos=[Diagnostico(d) for d in row["diagnosticos"].split(",")],
            Medicamentos=[
                Medicamento(p.split(":")[0], int(p.split(":")[1]))
                for p in row["productos"].split(";")
            ],
            fua=row.get("fua"),
            ups_codigo=row.get("ups_codigo"),
        )
        pedidos.append(pedido)

    # Similar para ingresos y salidas (implementar según necesidad)

    ingresos = []
    salidas = []

    return pedidos, ingresos, salidas
