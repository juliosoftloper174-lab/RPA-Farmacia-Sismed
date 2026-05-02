def agregar_producto_ingreso(registro, producto):

    registro.EditControl(Name="txtCodigo").SendKeys(producto.codigo)
    auto.SendKeys("{Enter}")

    registro.EditControl(Name="txtLote").SendKeys(producto.lote)
    auto.SendKeys("{Enter}")

    registro.EditControl(Name="txtCantidad").SendKeys(str(producto.cantidad))
    auto.SendKeys("{Enter}")

    registro.ButtonControl(Name="cmdAceptar").Click()
