"""
Genera el parrafo de justificacion por defecto segun el tipo de tramite.
Si el tecnico llena 'texto_justificacion_override' en la hoja Equipos,
ese texto manda y estas funciones no se usan.
"""
import pandas as pd


def justificacion_default(tipo_tramite: str, fila_equipo: pd.Series) -> str:
    marca_estado = fila_equipo.get("equipo_actual_marca_estado", "")
    sede_actual = fila_equipo.get("sede_equipo_actual", "")
    usuario = fila_equipo["usuario"]
    sede_usuario = fila_equipo["sede_usuario"]
    area = fila_equipo["area"]

    if tipo_tramite == "implementacion":
        return (
            f"El equipo en menci\u00f3n se requiere debido a que el equipo perteneciente a sede "
            f"{sede_actual} en uso del personal {usuario} quien pertenece a sede {sede_usuario}, "
            f"se encuentra {marca_estado}, ocasionando problemas en el desarrollo de sus funciones "
            f"dentro del \u00e1rea de {area}."
        )
    if tipo_tramite == "baja":
        return (
            f"El equipo en menci\u00f3n perteneciente a sede {sede_actual}, asignado a "
            f"{usuario} del \u00e1rea de {area}, se encuentra {marca_estado}, por lo que se "
            f"solicita su baja del inventario."
        )
    # diagnostico / default
    return (
        f"Se realiz\u00f3 el diagn\u00f3stico del equipo perteneciente a sede {sede_actual}, en uso de "
        f"{usuario} del \u00e1rea de {area}. Estado encontrado: {marca_estado}."
    )


def iniciales(nombre_completo: str) -> str:
    """'Antony Reyes Recalde' -> 'ARR'"""
    partes = str(nombre_completo).split()
    return "".join(p[0].upper() for p in partes if p)


def quitar_tildes(txt: str) -> str:
    import unicodedata
    return "".join(
        c for c in unicodedata.normalize("NFKD", str(txt))
        if not unicodedata.combining(c)
    )
