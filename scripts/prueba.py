from uiautomation import ButtonControl

from time import sleep

sleep(3)
aceptar: ButtonControl = ButtonControl(Name="Aceptar")
aceptar.Click()
