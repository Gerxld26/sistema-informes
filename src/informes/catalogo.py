"""
Motor de reglas: decide que especificaciones de equipo recomendar
segun cargo del usuario, area, y tipo de bien (CPU, Laptop, etc).

Prioridad de busqueda: cargo > area > default.
La tabla vive en la hoja Catalogo_Equipos del intake y se puede editar
libremente sin tocar este archivo.
"""
import pandas as pd


class ReglaNoEncontrada(Exception):
    """Se lanza cuando ninguna regla del catalogo aplica (ni siquiera el default)."""


def normalizar_catalogo(catalogo_df: pd.DataFrame) -> pd.DataFrame:
    df = catalogo_df.copy()
    df["prioridad"] = pd.to_numeric(df["prioridad"], errors="coerce")
    df = df.dropna(subset=["prioridad"])
    return df.sort_values("prioridad")


def _match(catalogo_df: pd.DataFrame, campo: str, valor: str, tipo_bien: str) -> pd.DataFrame:
    return catalogo_df[
        (catalogo_df["campo"] == campo)
        & (catalogo_df["valor"].astype(str).str.strip().str.lower() == str(valor).strip().lower())
        & (catalogo_df["tipo_bien"].astype(str).str.strip().str.lower() == str(tipo_bien).strip().lower())
    ]


def buscar_especificaciones(
    catalogo_df: pd.DataFrame, cargo: str, area: str, tipo_bien: str
) -> list[str]:
    """Devuelve la lista de especificaciones aplicable, o lanza ReglaNoEncontrada."""
    cat = normalizar_catalogo(catalogo_df)

    filas = _match(cat, "cargo", cargo, tipo_bien)
    if filas.empty:
        filas = _match(cat, "area", area, tipo_bien)
    if filas.empty:
        filas = cat[
            (cat["campo"] == "default")
            & (cat["tipo_bien"].astype(str).str.strip().str.lower() == str(tipo_bien).strip().lower())
        ]
    if filas.empty:
        raise ReglaNoEncontrada(
            f"No hay regla en Catalogo_Equipos para cargo='{cargo}' / area='{area}' / "
            f"tipo_bien='{tipo_bien}'. Agrega una fila 'default' para ese tipo_bien, o usa "
            f"'especificaciones_override' en la fila del equipo."
        )

    especs_raw = filas.iloc[0]["especificaciones (separadas por ;)"]
    return [e.strip() for e in str(especs_raw).split(";") if e.strip()]
