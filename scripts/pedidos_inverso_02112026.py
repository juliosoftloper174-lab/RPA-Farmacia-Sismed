"""Procesa los pedidos pendientes en orden INVERSO (del ultimo al primero).

Pensado para que dos maquinas avancen el mismo lote de pedidos sin pisarse:
- Maquina A (normal): recorre de arriba hacia abajo.
- Maquina B (este script): recorre de abajo hacia arriba.

Antes de cada pedido se vuelve a consultar el estado en la BD. Si el pedido ya
no esta pendiente se omite, y cuando se encuentran N pedidos consecutivos ya
registrados (00) el script se detiene solo: se llego a la zona de la otra
maquina.

Uso:
    python scripts/pedidos_inverso_02112026.py --dry-run
    python scripts/pedidos_inverso_02112026.py --limite 3
    python scripts/pedidos_inverso_02112026.py --si

El SISMED que se abre es el de src.config.SISMED_EXE (.env) salvo que se
indique otro con --exe.
"""

import argparse
import sys
from pathlib import Path
from time import monotonic

project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from src import config
from src.datos.sp_adapter import obtener_movimientos
from src.flujos.pedido import procesar_pedidos
from src.logger import logger

FECHA_POR_DEFECTO = "2026-11-02"
ESTADOS_PENDIENTES = {"", "NONE", "NULL"}


def _parsear_argumentos() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Procesa pedidos pendientes de abajo hacia arriba y se detiene al "
            "encontrar pedidos ya registrados por la otra maquina."
        )
    )
    parser.add_argument(
        "--fecha",
        default=config.FECHA_INI or FECHA_POR_DEFECTO,
        help="fecha de los movimientos a procesar (default: FECHA_INI del .env)",
    )
    parser.add_argument(
        "--limite",
        type=int,
        default=0,
        help="procesar solo los ultimos N pedidos (0 = todos)",
    )
    parser.add_argument(
        "--detener-tras",
        type=int,
        default=5,
        help="detenerse tras N pedidos consecutivos ya registrados (default: 5)",
    )
    parser.add_argument(
        "--refrescar-estado",
        type=int,
        default=60,
        help="segundos de cache del estado en BD (0 = refrescar antes de cada pedido)",
    )
    parser.add_argument(
        "--exe",
        default=None,
        help="ruta del sismedv2.exe a usar (default: SISMED_EXE del .env)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="solo muestra la lista en orden inverso, no abre SISMED",
    )
    parser.add_argument(
        "--si",
        dest="confirmar",
        action="store_true",
        help="no pide confirmacion",
    )
    return parser.parse_args()


class EstadoTracker:
    """Cache del estado de los movimientos, refrescada desde el SP."""

    def __init__(self, fecha_ini: str, fecha_fin: str, ttl: int) -> None:
        self.fecha_ini = fecha_ini
        self.fecha_fin = fecha_fin
        self.ttl = max(ttl, 0)
        self._estados: dict[str, str] = {}
        self._actualizado = 0.0

    def _refrescar(self) -> None:
        from database.conexion import ejecutar_sp_movimientos

        headers, _ = ejecutar_sp_movimientos(self.fecha_ini, self.fecha_fin)
        self._estados = {
            str(h.get("CORRELATIVO_KSALUD", "")).strip(): str(h.get("ESTADO", "")).strip()
            for h in headers
        }
        self._actualizado = monotonic()
        logger.debug(f"[ESTADO] Cache actualizado: {len(self._estados)} movimientos")

    def estado(self, correlativo: str) -> str:
        if self.ttl == 0 or monotonic() - self._actualizado > self.ttl:
            self._refrescar()
        return self._estados.get(correlativo.strip(), "")

    def no_pendiente(self, pedido) -> str | None:
        """Devuelve el estado si el pedido ya no esta pendiente; None si sigue NULL."""
        estado = self.estado(pedido.correlativo_ksalud)
        if estado.upper() in ESTADOS_PENDIENTES:
            return None
        return estado


def _pendientes(fecha: str):
    logger.info(f"Consultando SP_MOVIMIENTOS_SISMED_RPA {fecha} -> {fecha}")
    pedidos, _, _, _, _ = obtener_movimientos(fecha, fecha, skip_errores=True)
    return list(pedidos)


def main() -> int:
    args = _parsear_argumentos()

    if args.exe:
        if not Path(args.exe).exists():
            logger.error(f"No existe el ejecutable indicado: {args.exe}")
            return 3
        config.SISMED_EXE = args.exe

    logger.info("=" * 60)
    logger.info("PEDIDOS EN ORDEN INVERSO (ultimo -> primero)")
    logger.info(f"Fecha           : {args.fecha}")
    logger.info(f"BD Ksalud       : {config.DB_NAME} @ {config.DB_SERVER}")
    logger.info(f"SISMED          : {config.SISMED_EXE}")
    logger.info(f"Parada          : {args.detener_tras} pedidos consecutivos en 00")
    logger.info("=" * 60)

    if not Path(config.SISMED_EXE).exists():
        logger.error(
            f"No se encuentra el ejecutable de SISMED: {config.SISMED_EXE}. "
            "Corrija SISMED_EXE en el .env o use --exe."
        )
        return 3

    pedidos = _pendientes(args.fecha)
    if not pedidos:
        logger.warning("No hay pedidos pendientes para esa fecha.")
        return 0

    pendientes_total = len(pedidos)
    pedidos.reverse()
    if args.limite > 0:
        pedidos = pedidos[: args.limite]

    total = len(pedidos)
    logger.info(
        f"Pedidos pendientes en el SP: {pendientes_total} (en orden inverso, "
        f"se procesaran {total})"
    )
    for pos, pedido in enumerate(pedidos, start=1):
        logger.info(
            f"  {pos:>3}/{total} | {pedido.farmacia.codigo} | "
            f"{pedido.forma_pago.value} | {len(pedido.Medicamentos)} meds | "
            f"{pedido.correlativo_ksalud}"
        )

    if args.dry_run:
        logger.info("DRY-RUN: no se abre SISMED ni se modifica la BD.")
        return 0

    if not args.confirmar:
        respuesta = input(
            f"\n¿Procesar {total} pedidos en orden inverso en SISMED? (s/N): "
        ).strip().lower()
        if respuesta not in ("s", "si", "sí"):
            logger.info("Cancelado por el usuario.")
            return 0

    tracker = EstadoTracker(args.fecha, args.fecha, args.refrescar_estado)

    stats = procesar_pedidos(
        tuple(pedidos),
        fecha=args.fecha,
        fecha_fin=args.fecha,
        modo=config.MODO,
        consultar_estado=tracker.no_pendiente,
        parar_tras_ok=args.detener_tras,
    )

    logger.info("-" * 60)
    logger.info(
        f"Resultado: ok={stats.get('ok')} error={stats.get('error')} "
        f"sin_cliente={stats.get('sin_cliente')} sin_stock={stats.get('sin_stock')} "
        f"omitidos={stats.get('omitidos')}"
    )
    if stats.get("detenido_por"):
        logger.warning(f"Detenido: {stats['detenido_por']}")
    logger.info("-" * 60)
    return 0


if __name__ == "__main__":
    sys.exit(main())
