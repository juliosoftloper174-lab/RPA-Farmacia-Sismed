from uiautomation import GroupControl, WindowControl
from uiautomation import PaneControl
from uiautomation import ButtonControl
from uiautomation import Click

FARMACIA_WINDOW: WindowControl = WindowControl(
    searchDepth=1, Name="FARMACIA - MINSA SISMED C:\sismedv2_hospitalrioja ()"
)

FARMACIA_PANEL: PaneControl = FARMACIA_WINDOW.PaneControl(
    searchDepth=1, Name="FARMACIA - MINSA SISMED C:\sismedv2_hospitalrioja ()"
)

MAIN_WINDOW: WindowControl = WindowControl(searchDepth=1, Name="MINSA SISMED")
BOTON_CLOOSE_MAIN_WINDOW = MAIN_WINDOW.ButtonControl(Name="Cerrar")


REGISTRO_PEDIDO_WINDOW: WindowControl = FARMACIA_PANEL.WindowControl(
    searchDepth=1, Name="Registro de Pedido"
)

MINSA_SISMED_WINDOW: WindowControl = WindowControl(searchDepth=1, Name="MINSA SISMED")
MINSA_SISMED_PANEL: PaneControl = MINSA_SISMED_WINDOW.PaneControl(
    searchDepth=1, Name="MINSA SISMED"
)
MAIN_WINDOW: WindowControl = MINSA_SISMED_PANEL.WindowControl(
    searchDepth=1, Name="Menu Principal"
)
SYSTEM_INFO_PANEL: PaneControl = MAIN_WINDOW.PaneControl(
    searchDepth=1, foundIndex=1, Name=""
)


CONTROL_FARMARCIA_WINDOW: WindowControl = FARMACIA_PANEL.WindowControl(
    searchDepth=1, Name="Control de Farmacia"
)
MODULO_CONTROL_FARMACIA_PANEL: PaneControl = CONTROL_FARMARCIA_WINDOW.PaneControl(
    searchDepth=1, foundIndex=1, Name=""
)
BARRA_GROUP: GroupControl = REGISTRO_PEDIDO_WINDOW.GroupControl(
    searchDepth=1, Name="Barra"
)
