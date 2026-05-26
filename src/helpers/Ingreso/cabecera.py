def llenar_cabecera_ingreso(registro, ingreso):

    # 🔹 Almacén Origen (hardcoded - se eliminó del modelo)
    auto.Click(700, 230)
    auto.SendKeys("ALM. ANEXO RIOJA - SAN MARTIN")
    auto.SendKeys("{Enter}{Enter}")

    # 🔹 Almacén Destino
    auto.Click(1140, 230)
    auto.SendKeys(ingreso.almacen_destino)
    auto.SendKeys("{Enter}")

    # 🔹 Concepto
    combo = registro.ComboBoxControl(Name="cmbConcepto")
    combo.Click()

    opcion = auto.ListItemControl(RegexName=ingreso.concepto)
    opcion.Click()

    # 🔹 NGR
    ngr = generar_codigo_ngr()
    registro.EditControl(Name="txtGuiaRemision").SendKeys(ngr)

    # 🔹 Referencia
    registro.EditControl(Name="txtReferencia").SendKeys(ingreso.referencia)
