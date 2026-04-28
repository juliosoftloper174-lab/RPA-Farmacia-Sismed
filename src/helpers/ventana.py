from uiautomation import WindowControl


def esperar_ventana(nombre: str, timeout: int = 10) -> WindowControl:
    ventana: WindowControl = WindowControl(searchDepth=4, Name=nombre)
    if not ventana.Exists(timeout):
        raise Exception(f"No se encontró la ventana: {nombre}")
    return ventana
