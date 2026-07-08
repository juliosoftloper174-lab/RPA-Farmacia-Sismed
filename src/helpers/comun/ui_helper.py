import uiautomation as auto


def normalizar(texto: str) -> str:
    if not texto:
        return ""
    return texto.replace(" ", "").strip().upper()


def obtener_texto_edit(ctrl):
    for hijo in ctrl.GetChildren():
        if hijo.ControlType == auto.ControlType.EditControl:
            try:
                vp = hijo.GetValuePattern()
                if vp:
                    return vp.Value
            except:
                pass

            try:
                return hijo.Name
            except:
                pass

    return ""
