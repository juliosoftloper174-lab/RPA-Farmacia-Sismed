from src.flujos import salida as salida_mod
from src.models.Medicamento import Medicamento
from src.models.Salidas import Salidas


def _salida(tipo_movimiento: str) -> Salidas:
    return Salidas(
        almacen_origen="06732F02",
        almacen_destino="06732F01",
        almacen_virtual_origen="06732F0201",
        concepto="SOBRE STOCK" if tipo_movimiento == "DEVOLUCION" else "DISTRIBUCION",
        medicamentos=[Medicamento(codigo="39992", cantidad=1)],
        tipo_movimiento=tipo_movimiento,
    )


class TestSeleccionConcepto:
    def test_devolucion_solo_dos_clicks(self, monkeypatch):
        clicks = []
        monkeypatch.setattr(salida_mod, "Click", lambda x, y: clicks.append((x, y)))
        monkeypatch.setattr(salida_mod, "sleep", lambda _: None)

        salida_mod._seleccionar_concepto(_salida("DEVOLUCION"))

        assert clicks == [(700, 280), (572, 381)]

    def test_salida_mantiene_cinco_clicks(self, monkeypatch):
        clicks = []
        monkeypatch.setattr(salida_mod, "Click", lambda x, y: clicks.append((x, y)))
        monkeypatch.setattr(salida_mod, "sleep", lambda _: None)

        salida_mod._seleccionar_concepto(_salida("SALIDA"))

        assert clicks == [
            (700, 280),
            (704, 340),
            (507, 307),
            (704, 340),
            (507, 307),
        ]


class TestAdapterDevolucion:
    def test_mapea_devolucion_como_salida_sobre_stock(self, monkeypatch):
        from src.datos import sp_adapter

        ks = "KS|1|101|1|02|06|25|2|0"
        headers_fake = [
            {
                "CORRELATIVO_KSALUD": ks,
                "ESTADO": "0",
                "TIPO_MOVIMIENTO": "5",
                "TIPO_MOVIMIENTO_DES": "DEVOLUCION",
                "FECHA_MOVIMIENTO": "2026-10-27",
                "ALMACEN_ORIGEN": "06732F02",
                "ALMACEN_VIRTUAL_ORIGEN": "0",
                "ALMACEN_DESTINO": "06732F01",
                "ALMACEN_VIRTUAL_DESTINO": "0",
                "FARMACIA": "NULL",
                "PRESCRIPTOR": "NULL",
                "FORMA_PAGO": "NULL",
                "DIAGNOSTICO": "NULL",
                "FUA": "NULL",
                "KS_ORIGEN_CAS": "1",
                "KS_CENTRO_CAS": "101",
                "KS_TIPO_ALMACEN": "1",
                "KS_ALMACEN": "02",
                "KS_DOCUMENTO": "06",
                "KS_NUMERO_MOVIMIENTO": "25",
                "KS_TIPO_TRANSACCION": "2",
                "KS_COD_TIPO_ALMACEN_VIRTUAL": "0",
                "KS_TIPO_MOVIMIENTO": "202",
                "KS_TIPO_MOVIMIENTO_DES": "DEVOLUCION",
                "KS_CONCEPTO": "28",
                "KS_CONCEPTO_DES": "SOBRE STOCK",
            }
        ]
        detalles_fake = [
            {
                "CORRELATIVO_KSALUD": ks,
                "MATERIAL_CODIGO": "39992",
                "CANTIDAD": "1",
                "LOTE": "L001",
                "TIPO_SUMINISTRO": "CN",
                "FUENTE_FINANCIAMIENTO": "DYT",
                "REGISTRO_SANITARIO": "RS001",
                "FECHA_VENCIMIENTO": "2026-12-31",
                "PRECIO_COMPRA": "10.00",
            }
        ]

        monkeypatch.setattr(
            sp_adapter,
            "ejecutar_sp_movimientos",
            lambda *_: (headers_fake, detalles_fake),
        )

        pedidos, ingresos, salidas, extornos, _ = sp_adapter.obtener_movimientos(
            "2026-10-27", "2026-10-27"
        )

        assert pedidos == []
        assert ingresos == []
        assert extornos == []
        assert len(salidas) == 1

        salida = salidas[0]
        assert salida.tipo_movimiento == "DEVOLUCION"
        assert salida.concepto == "SOBRE STOCK"
        assert salida.almacen_origen == "06732F02"
        assert salida.almacen_destino == "06732F01"
        assert salida.almacen_virtual_origen == "06732F0201"
        assert salida.correlativo_ksalud == ks
        assert salida.update_key == ("1", "101", "1", "02", "06", "25", "2", "0")
        assert len(salida.medicamentos) == 1
        assert salida.medicamentos[0].codigo == "39992"
