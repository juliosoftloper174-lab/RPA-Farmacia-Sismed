import pytest
from pydantic import ValidationError

from src.models.cliente import Cliente
from src.models.diagnostico import Diagnostico
from src.models.farmacia import Farmacia
from src.models.forma_pago import FormaPago
from src.models.pedido import Pedido
from src.models.prescriptor import Prescriptor
from src.models.Medicamento import Medicamento
from src.models.enums import TipoReceta
from src.reportes.excel_schema import crear_row_pedido, crear_row_incidencia_validacion


# ============================================================
# Tests del MODELO Pedido (Pydantic)
# ============================================================

class TestPedidoModel:
    def test_pedido_valido(self):
        pedido = Pedido(
            farmacia=Farmacia("06732F02"),
            cliente=Cliente("00033257"),
            prescriptor=Prescriptor("14571"),
            forma_pago=FormaPago.CONTADO,
            tipo_receta=TipoReceta.SIN_NUMERO,
            diagnosticos=[Diagnostico("R100")],
            Medicamentos=[Medicamento("00091", 2)],
            fua=None,
        )
        assert pedido.farmacia.codigo == "06732F02"
        assert pedido.cliente.codigo == "00033257"
        assert pedido.prescriptor.codigo == "14571"
        assert pedido.forma_pago == FormaPago.CONTADO
        assert pedido.tipo_receta == TipoReceta.SIN_NUMERO
        assert len(pedido.diagnosticos) == 1
        assert pedido.diagnosticos[0].codigo == "R100"
        assert len(pedido.Medicamentos) == 1
        assert pedido.Medicamentos[0].codigo == "00091"
        assert pedido.Medicamentos[0].cantidad == 2

    def test_pedido_sin_prescriptor(self):
        pedido = Pedido(
            farmacia=Farmacia("06732F02"),
            cliente=Cliente("00033257"),
            forma_pago=FormaPago.CONTADO,
            tipo_receta=TipoReceta.SIN_NUMERO,
            Medicamentos=[Medicamento("00091", 1)],
        )
        assert pedido.prescriptor is None
        assert pedido.diagnosticos == []
        assert pedido.fua is None

    def test_pedido_sin_medicamentos_falla(self):
        with pytest.raises(ValidationError):
            Pedido(
                farmacia=Farmacia("06732F02"),
                cliente=Cliente("00033257"),
                forma_pago=FormaPago.CONTADO,
                tipo_receta=TipoReceta.SIN_NUMERO,
            )

    def test_pedido_sin_farmacia_falla(self):
        with pytest.raises(ValidationError):
            Pedido(
                cliente=Cliente("00033257"),
                forma_pago=FormaPago.CONTADO,
                tipo_receta=TipoReceta.SIN_NUMERO,
                Medicamentos=[Medicamento("00091", 1)],
            )

    def test_pedido_sin_cliente_falla(self):
        with pytest.raises(ValidationError):
            Pedido(
                farmacia=Farmacia("06732F02"),
                forma_pago=FormaPago.CONTADO,
                tipo_receta=TipoReceta.SIN_NUMERO,
                Medicamentos=[Medicamento("00091", 1)],
            )

    def test_pedido_con_varios_diagnosticos(self):
        pedido = Pedido(
            farmacia=Farmacia("06732F02"),
            cliente=Cliente("00033257"),
            forma_pago=FormaPago.CONTADO,
            tipo_receta=TipoReceta.SIN_NUMERO,
            diagnosticos=[Diagnostico("R100"), Diagnostico("R05X"), Diagnostico("K750")],
            Medicamentos=[Medicamento("00091", 1)],
        )
        assert len(pedido.diagnosticos) == 3
        assert [d.codigo for d in pedido.diagnosticos] == ["R100", "R05X", "K750"]

    def test_pedido_con_fua(self):
        pedido = Pedido(
            farmacia=Farmacia("06732F02"),
            cliente=Cliente("00033257"),
            forma_pago=FormaPago.SIS,
            tipo_receta=TipoReceta.SIN_NUMERO,
            Medicamentos=[Medicamento("00091", 1)],
            fua="786636652",
        )
        assert pedido.fua == "786636652"

    def test_medicamento_con_datos_completos(self):
        med = Medicamento(
            codigo="36394",
            cantidad=400,
            lote="DE5FDJ6D",
            tipo_sum="SISMED-COMPRA NACIONAL (CN)",
            fuente_fin="Recursos Determinados (RDE)",
            registro_sanitario="SIN_REG_SAN",
            fecha_vencimiento="2029/12/20",
            precio_compra=500.0,
        )
        assert med.lote == "DE5FDJ6D"
        assert med.precio_compra == 500.0
        assert med.registro_sanitario == "SIN_REG_SAN"


# ============================================================
# Tests de REGLAS DE NEGOCIO (obtener_revisiones)
# ============================================================

class TestPedidoRevisiones:
    def test_sin_revision_si_forma_pago_no_es_sis(self):
        pedido = Pedido(
            farmacia=Farmacia("06732F02"),
            cliente=Cliente("00033257"),
            forma_pago=FormaPago.CONTADO,
            tipo_receta=TipoReceta.SIN_NUMERO,
            Medicamentos=[Medicamento("00091", 1)],
        )
        assert pedido.obtener_revisiones() == []

    def test_revision_si_sis_sin_fua(self):
        pedido = Pedido(
            farmacia=Farmacia("06732F02"),
            cliente=Cliente("00033257"),
            forma_pago=FormaPago.SIS,
            tipo_receta=TipoReceta.SIN_NUMERO,
            Medicamentos=[Medicamento("00091", 1)],
        )
        revisiones = pedido.obtener_revisiones()
        assert len(revisiones) == 1
        assert "FUA" in revisiones[0]

    def test_sin_revision_si_sis_con_fua(self):
        pedido = Pedido(
            farmacia=Farmacia("06732F02"),
            cliente=Cliente("00033257"),
            forma_pago=FormaPago.SIS,
            tipo_receta=TipoReceta.SIN_NUMERO,
            Medicamentos=[Medicamento("00091", 1)],
            fua="786636652",
        )
        assert pedido.obtener_revisiones() == []

    def test_revision_si_tipo_receta_no_es_sin_numero(self):
        pedido = Pedido(
            farmacia=Farmacia("06732F02"),
            cliente=Cliente("00033257"),
            forma_pago=FormaPago.CONTADO,
            tipo_receta=TipoReceta.NUMERADA,
            Medicamentos=[Medicamento("00091", 1)],
        )
        revisiones = pedido.obtener_revisiones()
        assert len(revisiones) == 1
        assert "Numerada" in revisiones[0]

    def test_revision_multiple(self):
        pedido = Pedido(
            farmacia=Farmacia("06732F02"),
            cliente=Cliente("00033257"),
            forma_pago=FormaPago.SIS,
            tipo_receta=TipoReceta.ESTANDAR,
            Medicamentos=[Medicamento("00091", 1)],
        )
        revisiones = pedido.obtener_revisiones()
        assert len(revisiones) == 2


# ============================================================
# Tests de TRANSFORMACIONES (SP Adapter helpers)
# ============================================================

class TestMappingHelpers:
    def test_mapear_forma_pago_nulo_devuelve_contado(self):
        from src.datos.sp_adapter import _mapear_forma_pago
        assert _mapear_forma_pago(None) == FormaPago.CONTADO
        assert _mapear_forma_pago("") == FormaPago.CONTADO
        assert _mapear_forma_pago("NULL") == FormaPago.CONTADO

    def test_mapear_forma_pago_cero_devuelve_intervencion(self):
        from src.datos.sp_adapter import _mapear_forma_pago
        assert _mapear_forma_pago("0") == FormaPago.INTERVENCION_SANITARIA
        assert _mapear_forma_pago(0) == FormaPago.INTERVENCION_SANITARIA

    def test_mapear_forma_pago_uno_devuelve_sis(self):
        from src.datos.sp_adapter import _mapear_forma_pago
        assert _mapear_forma_pago("1") == FormaPago.SIS
        assert _mapear_forma_pago(1) == FormaPago.SIS

    def test_extraer_precio(self):
        from src.datos.sp_adapter import _extraer_precio
        assert _extraer_precio(None) is None
        assert _extraer_precio("NULL") is None
        assert _extraer_precio("500") == 500.0
        assert _extraer_precio("500.50") == 500.5
        assert _extraer_precio("123.45 algunos texto") == 123.45

    def test_parsear_fecha_vencimiento(self):
        from src.datos.sp_adapter import _parsear_fecha_vencimiento
        assert _parsear_fecha_vencimiento("") == ""
        assert _parsear_fecha_vencimiento("NULL") == ""
        assert _parsear_fecha_vencimiento("2029/12/20") == "2029/12/20"
        assert _parsear_fecha_vencimiento("2029-12-20") == "2029/12/20"
        assert _parsear_fecha_vencimiento("2029/01/31") == "2029/01/30"

    def test_mapear_almacen_virtual(self):
        from src.datos.sp_adapter import _mapear_almacen_virtual
        assert _mapear_almacen_virtual("0") == "030S0101"
        assert _mapear_almacen_virtual("1") == "030S0102"
        assert _mapear_almacen_virtual("9") == "030S0101"

    def test_mapear_tipo_suministro(self):
        from src.datos.sp_adapter import _mapear_tipo_suministro
        assert _mapear_tipo_suministro("CN") == "SISMED-COMPRA NACIONAL (CN)"
        assert _mapear_tipo_suministro("CI") == "SISMED-COMPRA UNIDAD EJECUTORA (CI)"
        assert _mapear_tipo_suministro("SC") == "SISMED-CENTRALIZADO (SC)"
        assert _mapear_tipo_suministro("OTRO") == "OTRO"

    def test_mapear_fuente_financiamiento(self):
        from src.datos.sp_adapter import _mapear_fuente_financiamiento
        assert _mapear_fuente_financiamiento("DYT") == "Donaciones y Transferencias (DYT)"
        assert _mapear_fuente_financiamiento("RDR") == "Recursos Directamente Recaudados (RDR)"
        assert _mapear_fuente_financiamiento("ROR") == "Recursos Ordinarios (ROR)"
        assert _mapear_fuente_financiamiento("OTRO") == "OTRO"


# ============================================================
# Tests del SP ADAPTER (construccion de objetos Pedido)
# ============================================================

class TestSpAdapterPedidos:
    def test_construir_medicamentos(self):
        from src.datos.sp_adapter import _construir_medicamentos
        detalles = [
            {"MATERIAL_CODIGO": "00091", "CANTIDAD": "2", "LOTE": "L001",
             "TIPO_SUMINISTRO": "CN", "FUENTE_FINANCIAMIENTO": "DYT",
             "REGISTRO_SANITARIO": "RS001", "FECHA_VENCIMIENTO": "2026-12-31",
             "PRECIO_COMPRA": "150.00"},
        ]
        meds = _construir_medicamentos(detalles)
        assert len(meds) == 1
        assert meds[0].codigo == "00091"
        assert meds[0].cantidad == 2
        assert meds[0].lote == "L001"
        assert meds[0].tipo_sum == "SISMED-COMPRA NACIONAL (CN)"
        assert meds[0].fuente_fin == "Donaciones y Transferencias (DYT)"
        assert meds[0].registro_sanitario == "RS001"
        assert meds[0].precio_compra == 150.0

    def test_construir_medicamentos_vacios(self):
        from src.datos.sp_adapter import _construir_medicamentos
        assert _construir_medicamentos([]) == []

    def test_construir_medicamentos_con_nulos(self):
        from src.datos.sp_adapter import _construir_medicamentos
        detalles = [
            {"MATERIAL_CODIGO": "00091", "CANTIDAD": "0", "LOTE": None,
             "TIPO_SUMINISTRO": None, "FUENTE_FINANCIAMIENTO": None,
             "REGISTRO_SANITARIO": None, "FECHA_VENCIMIENTO": None,
             "PRECIO_COMPRA": None},
        ]
        meds = _construir_medicamentos(detalles)
        assert meds[0].lote is None
        assert meds[0].tipo_sum is None
        assert meds[0].fuente_fin is None
        assert meds[0].registro_sanitario is None
        assert meds[0].fecha_vencimiento == ""
        assert meds[0].precio_compra is None

    def test_obtener_movimientos_pedidos_con_header_real(self, monkeypatch):
        from src.datos import sp_adapter

        headers_fake = [
            {
                "CORRELATIVO_KSALUD": "KS|1|101|1|02|03|759|2|0",
                "TIPO_MOVIMIENTO": "0",
                "TIPO_MOVIMIENTO_DES": "PEDIDO",
                "FECHA_MOVIMIENTO": "2026-06-09",
                "ALMACEN_ORIGEN": "NULL",
                "ALMACEN_VIRTUAL_ORIGEN": "0",
                "ALMACEN_DESTINO": "06732F02",
                "ALMACEN_VIRTUAL_DESTINO": "0",
                "FARMACIA": "06732F02",
                "PRESCRIPTOR": "NULL",
                "FORMA_PAGO": "1",
                "DIAGNOSTICO": "NULL",
                "FUA": "NULL",
            }
        ]
        detalles_fake = [
            {
                "CORRELATIVO_KSALUD": "KS|1|101|1|02|03|759|2|0",
                "MATERIAL_CODIGO": "00091",
                "CANTIDAD": "2",
                "LOTE": "L001",
                "TIPO_SUMINISTRO": "CN",
                "FUENTE_FINANCIAMIENTO": "DYT",
                "REGISTRO_SANITARIO": "RS001",
                "FECHA_VENCIMIENTO": "2026-12-31",
                "PRECIO_COMPRA": "150.00",
            }
        ]

        def fake_ejecutar_sp(fecha_ini, fecha_fin):
            return headers_fake, detalles_fake

        monkeypatch.setattr(sp_adapter, "ejecutar_sp_movimientos", fake_ejecutar_sp)

        pedidos, ingresos, salidas, _ = sp_adapter.obtener_movimientos("2026-06-09", "2026-06-10")
        assert len(pedidos) == 1
        assert len(ingresos) == 0
        assert len(salidas) == 0

        p = pedidos[0]
        assert p.farmacia.codigo == "06732F02"
        assert p.cliente.codigo == "00025759"
        assert p.prescriptor is None
        assert p.forma_pago == FormaPago.SIS
        assert p.tipo_receta == TipoReceta.SIN_NUMERO
        assert p.diagnosticos == []
        assert p.fua is None
        assert len(p.Medicamentos) == 1
        assert p.Medicamentos[0].codigo == "00091"

    def test_obtener_movimientos_pedido_con_prescriptor_y_diagnostico(self, monkeypatch):
        from src.datos import sp_adapter

        headers_fake = [
            {
                "CORRELATIVO_KSALUD": "KS|1|101|1|02|03|766|2|0",
                "TIPO_MOVIMIENTO": "0",
                "TIPO_MOVIMIENTO_DES": "PEDIDO",
                "FECHA_MOVIMIENTO": "2026-06-09",
                "ALMACEN_ORIGEN": "NULL",
                "ALMACEN_VIRTUAL_ORIGEN": "0",
                "ALMACEN_DESTINO": "06732F02",
                "ALMACEN_VIRTUAL_DESTINO": "0",
                "FARMACIA": "06732F02",
                "PRESCRIPTOR": "FLORES HUACHANI NAZARIO",
                "FORMA_PAGO": "1",
                "DIAGNOSTICO": "L239",
                "FUA": "00003575",
            }
        ]
        detalles_fake = [
            {
                "CORRELATIVO_KSALUD": "KS|1|101|1|02|03|766|2|0",
                "MATERIAL_CODIGO": "00091",
                "CANTIDAD": "1",
                "LOTE": "L001",
                "TIPO_SUMINISTRO": "CN",
                "FUENTE_FINANCIAMIENTO": "DYT",
                "REGISTRO_SANITARIO": "RS001",
                "FECHA_VENCIMIENTO": "2026-12-31",
                "PRECIO_COMPRA": "150.00",
            }
        ]

        def fake_ejecutar_sp(fecha_ini, fecha_fin):
            return headers_fake, detalles_fake

        monkeypatch.setattr(sp_adapter, "ejecutar_sp_movimientos", fake_ejecutar_sp)

        pedidos, _, _, _ = sp_adapter.obtener_movimientos("2026-06-09", "2026-06-10")
        p = pedidos[0]

        assert p.prescriptor is not None
        assert p.prescriptor.codigo == "87705"
        assert len(p.diagnosticos) == 1
        assert p.diagnosticos[0].codigo == "L239"
        assert p.fua == "00003575"
        assert p.forma_pago == FormaPago.SIS

    def test_farmacia_fallback_cuando_farmacia_vacio(self, monkeypatch):
        from src.datos import sp_adapter

        headers_fake = [
            {
                "CORRELATIVO_KSALUD": "KS|1|101|1|02|03|999|2|0",
                "TIPO_MOVIMIENTO": "0",
                "TIPO_MOVIMIENTO_DES": "PEDIDO",
                "FECHA_MOVIMIENTO": "2026-06-09",
                "ALMACEN_ORIGEN": "NULL",
                "ALMACEN_VIRTUAL_ORIGEN": "0",
                "ALMACEN_DESTINO": "06732F02",
                "ALMACEN_VIRTUAL_DESTINO": "0",
                "FARMACIA": "",
                "PRESCRIPTOR": "NULL",
                "FORMA_PAGO": "0",
                "DIAGNOSTICO": "NULL",
                "FUA": "NULL",
            }
        ]
        detalles_fake = [
            {
                "CORRELATIVO_KSALUD": "KS|1|101|1|02|03|999|2|0",
                "MATERIAL_CODIGO": "00091",
                "CANTIDAD": "1",
                "LOTE": "",
                "TIPO_SUMINISTRO": "",
                "FUENTE_FINANCIAMIENTO": "",
                "REGISTRO_SANITARIO": "",
                "FECHA_VENCIMIENTO": "NULL",
                "PRECIO_COMPRA": None,
            }
        ]

        def fake_ejecutar_sp(fecha_ini, fecha_fin):
            return headers_fake, detalles_fake

        monkeypatch.setattr(sp_adapter, "ejecutar_sp_movimientos", fake_ejecutar_sp)

        pedidos, _, _, _ = sp_adapter.obtener_movimientos("2026-06-09", "2026-06-10")
        p = pedidos[0]
        assert p.farmacia.codigo == "06732F02"
        assert p.forma_pago == FormaPago.INTERVENCION_SANITARIA


# ============================================================
# Tests del EXCEL SCHEMA para Pedidos
# ============================================================

class TestExcelSchemaPedido:
    def test_crear_row_pedido_ok(self):
        pedido = Pedido(
            farmacia=Farmacia("06732F02"),
            cliente=Cliente("00033257"),
            prescriptor=Prescriptor("14571"),
            forma_pago=FormaPago.SIS,
            tipo_receta=TipoReceta.SIN_NUMERO,
            diagnosticos=[Diagnostico("R100"), Diagnostico("R05X")],
            Medicamentos=[Medicamento("00091", 1), Medicamento("01532", 2)],
            fua="786636652",
        )
        row = crear_row_pedido(
            i=1,
            username="admin",
            correlativo_ksalud="KS123",
            correlativo_sismed="456",
            pedido=pedido,
            estado="OK",
        )
        assert row["Nº de Procesado"] == 1
        assert row["TipoMovimiento"] == "PEDIDO"
        assert row["Estado"] == "OK"
        assert row["farmacia"] == "06732F02"
        assert row["cliente"] == "00033257"
        assert row["prescriptor"] == "14571"
        assert row["forma_pago"] == "SIS"
        assert row["tipo_receta"] == "Receta Sin Numero"
        assert row["FUA"] == "786636652"
        assert row["Diag Nº1"] == "R100"
        assert row["Diag Nº2"] == "R05X"
        assert row["Diag Nº3"] == ""
        assert row["CantidadMedicamentos"] == 2

    def test_crear_row_pedido_error(self):
        pedido = Pedido(
            farmacia=Farmacia("06732F02"),
            cliente=Cliente("00033257"),
            forma_pago=FormaPago.CONTADO,
            tipo_receta=TipoReceta.SIN_NUMERO,
            Medicamentos=[Medicamento("00091", 1)],
        )
        row = crear_row_pedido(
            i=1,
            username="admin",
            correlativo_ksalud="KS123",
            correlativo_sismed="",
            pedido=pedido,
            estado="ERROR",
            error="Fallo en guardado",
        )
        assert row["Estado"] == "ERROR"
        assert row["Error"] == "Fallo en guardado"
        assert row["Nº correlativo Sismed"] == ""

    def test_crear_row_pedido_sin_prescriptor(self):
        pedido = Pedido(
            farmacia=Farmacia("06732F02"),
            cliente=Cliente("00033257"),
            forma_pago=FormaPago.CONTADO,
            tipo_receta=TipoReceta.SIN_NUMERO,
            Medicamentos=[Medicamento("00091", 1)],
        )
        row = crear_row_pedido(
            i=1,
            username="admin",
            correlativo_ksalud="KS123",
            correlativo_sismed="456",
            pedido=pedido,
            estado="OK",
        )
        assert row["prescriptor"] == ""

    def test_crear_row_pedido_con_tres_diagnosticos(self):
        pedido = Pedido(
            farmacia=Farmacia("06732F02"),
            cliente=Cliente("00033257"),
            forma_pago=FormaPago.CONTADO,
            tipo_receta=TipoReceta.SIN_NUMERO,
            diagnosticos=[Diagnostico("R100"), Diagnostico("R05X"), Diagnostico("K750")],
            Medicamentos=[Medicamento("00091", 1)],
        )
        row = crear_row_pedido(
            i=1,
            username="admin",
            correlativo_ksalud="KS123",
            correlativo_sismed="456",
            pedido=pedido,
            estado="OK",
        )
        assert row["Diag Nº1"] == "R100"
        assert row["Diag Nº2"] == "R05X"
        assert row["Diag Nº3"] == "K750"

    def test_crear_row_incidencia_validacion_pedido(self):
        row = crear_row_incidencia_validacion(
            tipo="PEDIDO",
            error="FUA es obligatorio",
            data={"farmacia": "06732F02", "cliente": "00033257"},
            i=1,
            estado="REVISION",
        )
        assert row["TipoMovimiento"] == "PEDIDO"
        assert row["Estado"] == "REVISION"
        assert row["Error"] == "FUA es obligatorio"
        assert row["farmacia"] == "06732F02"
        assert row["cliente"] == "00033257"
