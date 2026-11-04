"""Registra una salida pendiente omitiendo los codigos que SISMED rechaza.

Caso 02/11/2026 - salida KS|1|101|6|01|06|2|2|0 (06732F01 -> 06732F03):
SISMED rechaza el codigo 04187 con el aviso
"el medicamento o insumo debe tener el Registro Sanitario vigente",
por eso la nota nunca se grabo y la salida quedo en estado 20.

El script toma la salida del SP, quita los codigos indicados, la registra en
SISMED y deja el estado en 00 SOLO si SISMED confirmo el correlativo.

Uso:
    python scripts/salida_omitir_codigos.py --dry-run
    python scripts/salida_omitir_codigos.py
    python scripts/salida_omitir_codigos.py --excluir 04187,04291 --si

Ojo: al omitir 04187 la mercaderia de ese codigo nunca llega a F03, por lo que
el retorno F03 -> F01 de 24 unidades del lote 2325210B no se debe registrar.
"""

import argparse
import sys
from datetime import datetime
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

import uiautomation as auto

from src import config
from src.datos.sp_adapter import obtener_movimientos
from src.flujos.salida import procesar_salidas
from src.logger import logger

CORRELATIVO_POR_DEFECTO = "KS|1|101|6|01|06|2|2|0"
CODIGOS_POR_DEFECTO = "04187"


def _parsear_argumentos() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Registra una salida pendiente omitiendo codigos rechazados por SISMED."
    )
    parser.add_argument(
        "--correlativo",
        default=CORRELATIVO_POR_DEFECTO,
        help="correlativo Ksalud de la salida a registrar",
    )
    parser.add_argument(
        "--excluir",
        default=CODIGOS_POR_DEFECTO,
        help="codigos separados por coma que no se van a registrar",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="solo muestra el plan, no abre SISMED ni modifica la BD",
    )
    parser.add_argument(
        "--si",
        dest="confirmar",
        action="store_true",
        help="no pide confirmacion",
    )
    return parser.parse_args()


def _fechas() -> tuple[str, str]:
    hoy = datetime.now().strftime("%Y-%m-%d")
    return config.FECHA_INI or hoy, config.FECHA_FIN or hoy


def _ventana_registro_abierta() -> bool:
    try:
        registro = auto.WindowControl(Name="Registro de Salidas ")
        return registro.Exists(maxSearchSeconds=1)
    except Exception as e:
        logger.warning(f"No se pudo verificar la ventana 'Registro de Salidas': {e}")
        return False


def _buscar_salida(correlativo: str):
    fecha_ini, fecha_fin = _fechas()
    logger.info(f"Consultando SP_MOVIMIENTOS_SISMED_RPA {fecha_ini} -> {fecha_fin}")
    _, _, salidas, _, _ = obtener_movimientos(fecha_ini, fecha_fin, skip_errores=False)

    for salida in salidas:
        if salida.correlativo_ksalud == correlativo:
            return salida, fecha_ini, fecha_fin

    raise SystemExit(
        f"No se encontro la salida {correlativo} en el SP ({fecha_ini} -> {fecha_fin})"
    )


def _filtrar_medicamentos(medicamentos, excluidos: set[str]):
    omitidos = [m for m in medicamentos if m.codigo in excluidos]
    conservados = [m for m in medicamentos if m.codigo not in excluidos]
    return conservados, omitidos


def main() -> int:
    args = _parsear_argumentos()
    excluidos = {c.strip() for c in args.excluir.split(",") if c.strip()}

    logger.info("=" * 60)
    logger.info("REGISTRO DE SALIDA OMITIENDO CODIGOS")
    logger.info(f"Salida objetivo : {args.correlativo}")
    logger.info(f"Codigos omitidos: {', '.join(sorted(excluidos))}")
    logger.info(f"BD Ksalud       : {config.DB_NAME} @ {config.DB_SERVER}")
    logger.info(f"Modo            : {config.MODO}")
    logger.info("=" * 60)

    if _ventana_registro_abierta():
        logger.error(
            "Hay una ventana 'Registro de Salidas' abierta en SISMED. "
            "Cierrela (Cancelar, sin guardar) antes de continuar."
        )
        return 2

    salida, fecha_ini, fecha_fin = _buscar_salida(args.correlativo)

    conservados, omitidos = _filtrar_medicamentos(salida.medicamentos, excluidos)

    if not omitidos:
        logger.error(
            f"Ninguno de los codigos {sorted(excluidos)} esta en la salida. "
            "Nada que omitir, se aborta."
        )
        return 3

    if not conservados:
        logger.error("La salida quedaria sin productos. Se aborta.")
        return 3

    if not salida.update_key:
        logger.error("La salida no tiene update_key; no se podria marcar el estado. Se aborta.")
        return 3

    logger.info(
        f"Ruta    : {salida.almacen_origen} -> {salida.almacen_destino} "
        f"({salida.concepto})"
    )
    logger.info(
        f"Detalle : {len(salida.medicamentos)} lineas -> "
        f"{len(conservados)} se registran, {len(omitidos)} se omiten"
    )
    for medicamento in omitidos:
        logger.warning(
            f"  OMITIDO: {medicamento.codigo} lote={medicamento.lote} "
            f"cantidad={medicamento.cantidad}"
        )

    if args.dry_run:
        logger.info("DRY-RUN: no se abre SISMED ni se modifica la BD.")
        return 0

    if not args.confirmar:
        respuesta = input("\n¿Registrar la salida en SISMED? (s/N): ").strip().lower()
        if respuesta not in ("s", "si", "sí"):
            logger.info("Cancelado por el usuario.")
            return 0

    salida.medicamentos = conservados
    stats = procesar_salidas(
        (salida,), fecha=fecha_ini, fecha_fin=fecha_fin, modo=config.MODO
    )

    if stats.get("ok") == 1:
        logger.success("Salida registrada en SISMED y estado actualizado a 00.")
        logger.warning("=" * 60)
        logger.warning(f"Lineas que NO se registraron ({len(omitidos)}):")
        for medicamento in omitidos:
            logger.warning(
                f"  {medicamento.codigo} lote={medicamento.lote} "
                f"cantidad={medicamento.cantidad}"
            )
        logger.warning("Esa mercaderia no llego al almacen destino en SISMED.")
        logger.warning("=" * 60)
        return 0

    logger.error(
        f"La salida no se registro (ok={stats.get('ok')}, error={stats.get('error')}). "
        "El estado quedo en 20, revisar el log."
    )
    return 1


if __name__ == "__main__":
    sys.exit(main())
