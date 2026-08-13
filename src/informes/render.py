"""
Arma el contexto de cada tramite (con sus N equipos) y lo renderiza contra
la plantilla docxtpl para producir el .docx final.
"""
from pathlib import Path

import pandas as pd
from docxtpl import DocxTemplate

from . import config, textos
from .catalogo import ReglaNoEncontrada, buscar_especificaciones
from .intake import Intake


def _resolver_especificaciones(catalogo_df: pd.DataFrame, fila_equipo: pd.Series) -> list[str]:
    override = fila_equipo.get("especificaciones_override", "")
    if pd.notna(override) and str(override).strip():
        return [e.strip() for e in str(override).split(";") if e.strip()]

    try:
        return buscar_especificaciones(
            catalogo_df,
            cargo=fila_equipo.get("cargo_usuario", ""),
            area=fila_equipo.get("area", ""),
            tipo_bien=fila_equipo.get("tipo_bien", "CPU"),
        )
    except ReglaNoEncontrada as exc:
        print(f"[AVISO] {exc} (usuario: {fila_equipo['usuario']})")
        return ["** ESPECIFICAR MANUALMENTE - no se encontro regla en catalogo **"]


def _resolver_justificacion(tipo: str, fila_equipo: pd.Series) -> str:
    override = fila_equipo.get("texto_justificacion_override", "")
    if pd.notna(override) and str(override).strip():
        return str(override).strip()
    return textos.justificacion_default(tipo, fila_equipo)


def _contexto_equipo(catalogo_df: pd.DataFrame, tipo: str, fila_equipo: pd.Series) -> dict:
    return {
        "usuario": fila_equipo["usuario"],
        "area": fila_equipo.get("area", ""),
        "jefatura": fila_equipo.get("jefatura", ""),
        "cantidad": str(fila_equipo.get("cantidad") or 1).zfill(2),
        "tipo_bien": fila_equipo.get("tipo_bien", "CPU"),
        "especificaciones": _resolver_especificaciones(catalogo_df, fila_equipo),
        "texto_justificacion": _resolver_justificacion(tipo, fila_equipo),
    }


def _contexto_tramite(intake: Intake, fila_tramite: pd.Series) -> dict:
    id_tramite = fila_tramite["id_tramite"]
    tipo = str(fila_tramite["tipo_tramite"]).strip().lower()
    equipos_tramite = intake.equipos[intake.equipos["id_tramite"] == id_tramite]

    if equipos_tramite.empty:
        raise ValueError(f"Tramite {id_tramite} no tiene equipos asociados en la hoja Equipos.")

    equipos_ctx = [
        _contexto_equipo(intake.catalogo, tipo, eq) for _, eq in equipos_tramite.iterrows()
    ]

    info_tipo = config.TEXTOS_TIPO_TRAMITE[tipo]
    cantidad_total = sum(int(eq.get("cantidad") or 1) for _, eq in equipos_tramite.iterrows())
    plural = info_tipo["plural_1"] if cantidad_total == 1 else info_tipo["plural_n"]

    areas_vistas = set(equipos_tramite.get("area", pd.Series(dtype=str)).dropna())
    area_asunto = list(areas_vistas)[0] if len(areas_vistas) == 1 else "VARIAS AREAS"
    tipo_bien_asunto = (
        equipos_ctx[0]["tipo_bien"].upper() if len(equipos_ctx) == 1 else "EQUIPOS"
    )

    return {
        "numero_informe": str(int(fila_tramite["numero_informe"])).zfill(3),
        "anio": int(fila_tramite["anio"]),
        "iniciales_tecnicos": textos.iniciales(fila_tramite["tecnico_nombre"]),
        "siglas_sede": fila_tramite["siglas_sede"],
        "destinatario_nombre": fila_tramite["destinatario_nombre"],
        "destinatario_cargo": fila_tramite["destinatario_cargo"],
        "tecnico_nombre": fila_tramite["tecnico_nombre"],
        "tecnico_cargo": fila_tramite["tecnico_cargo"],
        "asunto_linea1": f"{info_tipo['asunto']} {tipo_bien_asunto}",
        "asunto_linea2": area_asunto.upper(),
        "fecha": fila_tramite["fecha"],
        "tipo_verbo": info_tipo["verbo"],
        "cantidad_equipos": str(cantidad_total).zfill(2),
        "tipo_equipo_plural": plural,
        "equipos": equipos_ctx,
        "jefe_ti_nombre": fila_tramite["jefe_ti_nombre"],
        "jefe_ti_cargo": fila_tramite["jefe_ti_cargo"],
    }


def generar_informe_tecnico(
    intake: Intake,
    fila_tramite: pd.Series,
    ruta_plantilla: Path = config.RUTA_PLANTILLA_INFORME_TECNICO,
    carpeta_salida: Path = config.RUTA_SALIDA,
) -> Path:
    """Genera el .docx de un solo tramite y devuelve la ruta del archivo creado."""
    contexto = _contexto_tramite(intake, fila_tramite)

    doc = DocxTemplate(str(ruta_plantilla))
    doc.render(contexto)

    id_tramite = textos.quitar_tildes(fila_tramite["id_tramite"])
    nombre_archivo = (
        f"Informe_Tecnico_{contexto['numero_informe']}-{contexto['anio']}_"
        f"{contexto['iniciales_tecnicos']}_{id_tramite}.docx"
    )
    carpeta_salida = Path(carpeta_salida)
    carpeta_salida.mkdir(parents=True, exist_ok=True)
    ruta_out = carpeta_salida / nombre_archivo
    doc.save(str(ruta_out))
    return ruta_out


def generar_todos(intake: Intake, **kwargs) -> list[Path]:
    generados = []
    for _, fila_tramite in intake.tramites.iterrows():
        try:
            ruta = generar_informe_tecnico(intake, fila_tramite, **kwargs)
            n_equipos = len(intake.equipos[intake.equipos["id_tramite"] == fila_tramite["id_tramite"]])
            print(f"[OK] Generado: {ruta.name} ({n_equipos} equipo(s))")
            generados.append(ruta)
        except ValueError as exc:
            print(f"[AVISO] {exc} Se omite.")
    return generados
