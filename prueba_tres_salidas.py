"""
Script de prueba para 3 salidas seguidas con guardado real.

Objetivo: verificar que el bot puede procesar salidas externas (doc 05)
con diferentes conceptos y que cierra correctamente la ventana entre cada una.

ADVERTENCIA: este script crea movimientos reales en SISMED QA.
"""

from src.datos.config_salidas_externas import obtener_config_salida_externa
from src.flujos.salida import procesar_salidas
from src.models.Medicamento import Medicamento
from src.models.Salidas import Salidas


def _crear_salida(
    doc: str,
    tipo: str,
    concepto: str,
    almacen_origen: str,
    almacen_destino: str,
    almacen_virtual_origen: str,
    medicamentos: list[Medicamento],
) -> Salidas:
    """Construye una Salidas usando la configuracion centralizada."""
    config = obtener_config_salida_externa(doc, tipo, concepto)
    if config is None:
        raise RuntimeError(f"No hay config para ({doc}, {tipo}, {concepto})")
    if not config.get("coordenadas"):
        raise RuntimeError(
            f"Config para ({doc}, {tipo}, {concepto}) no tiene coordenadas"
        )

    return Salidas(
        almacen_origen=almacen_origen,
        almacen_destino=almacen_destino,
        almacen_virtual_origen=almacen_virtual_origen,
        concepto=config["concepto_sismed"],
        medicamentos=medicamentos,
        tipo_documento=doc,
        tipo_movimiento_sp=tipo,
        concepto_sp=concepto,
        nseap=config["nseap"],
        concepto_sismed=config["concepto_sismed"],
        destino_ksalud=config["destino_ksalud"],
        destino_sismed=config["destino_sismed"],
        coordenadas_concepto=config["coordenadas"],
    )


def main() -> None:
    medicamento = Medicamento(
        codigo="00143",
        cantidad=1,
        lote="2102335",
    )

    salidas = [
        # Salida 1: 06732F01 -> Anexo Rioja, Sobre Stock (C1)
        _crear_salida(
            doc="05",
            tipo="203",
            concepto="31",
            almacen_origen="06732F01",
            almacen_destino="030S01",
            almacen_virtual_origen="06732F0101",
            medicamentos=[medicamento],
        ),
        # Salida 2: 06732F01 -> Logistica, Distribucion (C3)
        _crear_salida(
            doc="05",
            tipo="214",
            concepto="26",
            almacen_origen="06732F01",
            almacen_destino="030A00",
            almacen_virtual_origen="06732F0101",
            medicamentos=[medicamento],
        ),
        # Salida 3: 06732F01 -> Anexo Rioja, Dev. x R.S. (C2)
        _crear_salida(
            doc="05",
            tipo="208",
            concepto="20",
            almacen_origen="06732F01",
            almacen_destino="030S01",
            almacen_virtual_origen="06732F0101",
            medicamentos=[medicamento],
        ),
    ]

    stats = procesar_salidas(
        tuple(salidas),
        fecha="2026-11-19",
        fecha_fin="2026-11-19",
        modo="prueba",
    )
    print("Resultado:", stats)


if __name__ == "__main__":
    main()
