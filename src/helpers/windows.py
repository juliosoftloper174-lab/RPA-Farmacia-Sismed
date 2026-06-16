"""COMs die quickly, do not store constants here."""

from uiautomation import GroupControl, PaneControl, WindowControl


def get_farmacia_window() -> WindowControl:
    return WindowControl(
        searchDepth=1, Name="FARMACIA - MINSA SISMED C:\sismedv2_hospitalrioja ()"
    )


def get_farmacia_panel() -> PaneControl:
    return get_farmacia_window().PaneControl(
        searchDepth=1, Name="FARMACIA - MINSA SISMED C:\sismedv2_hospitalrioja ()"
    )


def get_registro_pedido_window() -> WindowControl:
    return get_farmacia_panel().WindowControl(searchDepth=1, Name="Registro de Pedido")


def get_minsa_sismed_window() -> WindowControl:
    return WindowControl(searchDepth=1, Name="MINSA SISMED")


def get_minsa_sismed_panel() -> PaneControl:
    return get_minsa_sismed_window().PaneControl(searchDepth=1, Name="MINSA SISMED")


def get_main_window() -> WindowControl:
    return get_minsa_sismed_panel().WindowControl(searchDepth=1, Name="Menu Principal")


def get_system_info_panel() -> PaneControl:

    return get_main_window().PaneControl(searchDepth=1, foundIndex=1, Name="")


def get_barrar_group() -> GroupControl:
    return get_registro_pedido_window().GroupControl(searchDepth=1, Name="Barra")
