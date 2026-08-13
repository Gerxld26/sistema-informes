import shutil
from pathlib import Path

from . import config

NOMBRES_TIPO_DOCUMENTO = {
    "implementacion": "IMPLEMENTACI\u00d3N",
    "baja": "BAJA",
    "diagnostico": "DIAGN\u00d3STICO",
}


def nombre_nomenclatura(numero_informe: str, tipo_tramite: str, tipo_bien: str, area: str) -> str:
    tipo_doc = NOMBRES_TIPO_DOCUMENTO.get(tipo_tramite, tipo_tramite.upper())
    return f"INFORME TECNICO N\u00b0{numero_informe}- {tipo_doc} {tipo_bien.upper()}- {area.upper()}"


def exportar_a_nas(
    ruta_local: Path,
    numero_informe: str,
    anio: int,
    tipo_tramite: str,
    tipo_bien: str,
    area: str,
    ruta_nas_base: str | None = config.RUTA_NAS,
) -> Path | None:
    if not ruta_nas_base:
        return None

    carpeta_destino = Path(ruta_nas_base) / str(anio) / tipo_tramite.capitalize()
    carpeta_destino.mkdir(parents=True, exist_ok=True)

    nombre_final = nombre_nomenclatura(numero_informe, tipo_tramite, tipo_bien, area)
    extension = Path(ruta_local).suffix
    ruta_destino = carpeta_destino / f"{nombre_final}{extension}"

    shutil.copy2(ruta_local, ruta_destino)
    return ruta_destino
