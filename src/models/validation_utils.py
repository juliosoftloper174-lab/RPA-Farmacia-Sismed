from __future__ import annotations
from typing import Any, Dict, List, Optional
from pydantic import ValidationError


def pydantic_errors_to_log(
    exc: ValidationError,
    input_data: Dict[str, Any],
    movimiento_id: Optional[str] = None,
    modelo_nombre: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """
    Transforma ValidationError de Pydantic v2 a lista de dicts amigables para logs/Excel.
    - `input_data`: dict original con los datos que se intentaron validar.
    - devuelve una lista con una entrada por cada error.
    """
    out: List[Dict[str, Any]] = []
    for err in exc.errors():
        loc = err.get("loc") or []
        campo = loc[0] if isinstance(loc, (list, tuple)) and loc else str(loc)
        mensaje = err.get("msg", "")
        valor_recibido = input_data.get(campo) if isinstance(input_data, dict) else None

        entry = {
            "movimiento": movimiento_id,
            "modelo": modelo_nombre,
            "codigo": input_data.get("codigo"),
            "lote": input_data.get("lote"),
            "campo_error": campo,
            "valor_recibido": valor_recibido,
            "mensaje": mensaje,
        }
        out.append(entry)
    return out
