"""
Lee y limpia las 3 hojas del Excel de intake (Tramites, Equipos, Catalogo_Equipos).
Aisla toda la logica de "el excel tiene una fila de nota al final que hay que
descartar" para que el resto del sistema trabaje con DataFrames limpios.
"""
from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from . import config


class IntakeInvalido(Exception):
    """El excel de intake no tiene la forma esperada."""


@dataclass
class Intake:
    tramites: pd.DataFrame
    equipos: pd.DataFrame
    catalogo: pd.DataFrame


def _quitar_filas_nota(df: pd.DataFrame, columna_clave: str) -> pd.DataFrame:
    """Descarta la fila de instrucciones (empieza con 'Nota:') que las plantillas
    de intake incluyen como ayuda visual para quien las llena a mano."""
    return df[~df[columna_clave].astype(str).str.startswith("Nota")]


def cargar_intake(ruta: Path | str = config.RUTA_INTAKE_DEFAULT) -> Intake:
    ruta = Path(ruta)
    if not ruta.exists():
        raise IntakeInvalido(f"No existe el archivo de intake: {ruta}")

    tramites_df = pd.read_excel(ruta, sheet_name=config.HOJA_TRAMITES)
    equipos_df = pd.read_excel(ruta, sheet_name=config.HOJA_EQUIPOS)
    catalogo_df = pd.read_excel(ruta, sheet_name=config.HOJA_CATALOGO)

    for col in ("id_tramite", "numero_informe", "tipo_tramite"):
        if col not in tramites_df.columns:
            raise IntakeInvalido(f"Falta la columna '{col}' en la hoja {config.HOJA_TRAMITES}")
    for col in ("id_tramite", "usuario"):
        if col not in equipos_df.columns:
            raise IntakeInvalido(f"Falta la columna '{col}' en la hoja {config.HOJA_EQUIPOS}")

    tramites_df["numero_informe"] = pd.to_numeric(tramites_df["numero_informe"], errors="coerce")
    tramites_df = tramites_df.dropna(subset=["id_tramite", "numero_informe"])
    tramites_df = _quitar_filas_nota(tramites_df, "id_tramite")

    equipos_df = equipos_df.dropna(subset=["id_tramite", "usuario"])
    equipos_df = _quitar_filas_nota(equipos_df, "id_tramite")

    tipos_validos = set(config.TEXTOS_TIPO_TRAMITE.keys())
    tipos_en_datos = set(tramites_df["tipo_tramite"].astype(str).str.strip().str.lower())
    tipos_invalidos = tipos_en_datos - tipos_validos
    if tipos_invalidos:
        raise IntakeInvalido(
            f"tipo_tramite invalido(s): {tipos_invalidos}. Validos: {sorted(tipos_validos)}"
        )

    ids_tramite = set(tramites_df["id_tramite"])
    ids_equipos = set(equipos_df["id_tramite"])
    huerfanos = ids_equipos - ids_tramite
    if huerfanos:
        raise IntakeInvalido(
            f"Hay equipos referenciando id_tramite que no existe en la hoja Tramites: {huerfanos}"
        )

    return Intake(tramites=tramites_df, equipos=equipos_df, catalogo=catalogo_df)
