import json
from datetime import date
from pathlib import Path

import pandas as pd

from . import config, db, nas, perfil
from .intake import Intake
from .render import generar_informe_tecnico

TIPOS_TRAMITE = list(config.TEXTOS_TIPO_TRAMITE.keys())
TIPOS_BIEN = ["CPU", "Laptop", "Monitor", "Impresora"]


def elegir_opcion(titulo: str, opciones: list[str], permitir_otro: bool = False) -> str:
    print(f"\n{titulo}")
    for i, op in enumerate(opciones, start=1):
        print(f"  {i}. {op}")
    if permitir_otro:
        print(f"  {len(opciones) + 1}. Otro (escribir manualmente)")

    while True:
        eleccion = input("Elige un numero: ").strip()
        if eleccion.isdigit():
            idx = int(eleccion)
            if 1 <= idx <= len(opciones):
                return opciones[idx - 1]
            if permitir_otro and idx == len(opciones) + 1:
                return input("Escribe el valor: ").strip()
        print("Opcion invalida, intenta de nuevo.")


def siguiente_numero_informe(conn, anio: int) -> int:
    fila = conn.execute(
        "SELECT MAX(numero_informe) AS maximo FROM tramites WHERE anio = :anio", {"anio": anio}
    ).fetchone()
    return (fila["maximo"] or 0) + 1


def cargar_catalogo() -> pd.DataFrame:
    return pd.read_excel(config.RUTA_INTAKE_DEFAULT, sheet_name=config.HOJA_CATALOGO)


def importar_escaneo_hardware(ruta: str) -> dict:
    datos = json.loads(Path(ruta).read_text(encoding="utf-8"))
    return {
        "serie": datos.get("serie", ""),
        "marca_modelo": datos.get("marca_modelo", ""),
        "ram_gb": datos.get("ram_gb"),
        "disco_tipo": datos.get("disco_tipo", ""),
        "disco_gb": datos.get("disco_gb"),
    }


def capturar_equipo_unico(area: str) -> dict:
    usuario = input("Nombre del usuario: ").strip()
    cargo_usuario = input("Cargo del usuario: ").strip()
    sede_usuario = input("Sede del usuario: ").strip()
    jefatura = input("Jefe directo del usuario: ").strip()
    tipo_bien = elegir_opcion("Tipo de bien", TIPOS_BIEN)
    equipo_actual_marca_estado = input("Estado del equipo actual (breve): ").strip()
    sede_equipo_actual = input("Sede del equipo actual: ").strip()

    hardware = {}
    ruta_escaneo = input("Ruta al archivo de escaneo de hardware (enter para omitir): ").strip()
    if ruta_escaneo:
        hardware = importar_escaneo_hardware(ruta_escaneo)

    especificaciones_override = input(
        "Especificaciones manuales separadas por ';' (enter para usar el catalogo): "
    ).strip()

    return {
        "usuario": usuario,
        "cargo_usuario": cargo_usuario,
        "area": area,
        "sede_usuario": sede_usuario,
        "jefatura": jefatura,
        "tipo_bien": tipo_bien,
        "equipo_actual_marca_estado": equipo_actual_marca_estado,
        "sede_equipo_actual": sede_equipo_actual,
        "especificaciones_override": especificaciones_override,
        "cantidad": 1,
        **hardware,
    }


def capturar_equipos_varios(area: str, cantidad: int) -> dict:
    tipo_bien = elegir_opcion("Tipo de bien", TIPOS_BIEN)
    jefatura = input("Jefatura responsable del area: ").strip()
    sede_equipo_actual = input("Sede de los equipos: ").strip()
    equipo_actual_marca_estado = input("Descripcion breve del estado de los equipos: ").strip()
    especificaciones_override = input(
        "Especificaciones manuales separadas por ';' (enter para usar el catalogo): "
    ).strip()

    return {
        "usuario": "Varios",
        "cargo_usuario": "",
        "area": area,
        "sede_usuario": area,
        "jefatura": jefatura,
        "tipo_bien": tipo_bien,
        "equipo_actual_marca_estado": equipo_actual_marca_estado,
        "sede_equipo_actual": sede_equipo_actual,
        "especificaciones_override": especificaciones_override,
        "cantidad": cantidad,
    }


def ejecutar_wizard():
    perfil_tecnico = perfil.cargar_o_crear_perfil()

    tipo_tramite = elegir_opcion("Tipo de tramite", TIPOS_TRAMITE)
    area = elegir_opcion("Area", config.AREAS_CLINICA, permitir_otro=True)

    cantidad = int(input("\nCuantos equipos incluye este informe? ").strip() or "1")
    equipo = capturar_equipo_unico(area) if cantidad == 1 else capturar_equipos_varios(area, cantidad)

    anio = date.today().year
    fecha = date.today().strftime("%d/%m/%Y")

    with db.conexion() as conn:
        numero_informe = siguiente_numero_informe(conn, anio)
        id_tramite = f"{anio}-{numero_informe:03d}"

        tramite = {
            "id_tramite": id_tramite,
            "numero_informe": numero_informe,
            "anio": anio,
            "tipo_tramite": tipo_tramite,
            "area": area,
            "siglas_sede": perfil_tecnico["siglas_sede"],
            "fecha": fecha,
            "tecnico_nombre": perfil_tecnico["tecnico_nombre"],
            "tecnico_cargo": perfil_tecnico["tecnico_cargo"],
            "destinatario_nombre": perfil_tecnico["destinatario_nombre"],
            "destinatario_cargo": perfil_tecnico["destinatario_cargo"],
            "jefe_ti_nombre": perfil_tecnico["jefe_ti_nombre"],
            "jefe_ti_cargo": perfil_tecnico["jefe_ti_cargo"],
        }
        equipo["id_tramite"] = id_tramite

        intake = Intake(
            tramites=pd.DataFrame([tramite]),
            equipos=pd.DataFrame([equipo]),
            catalogo=cargar_catalogo(),
        )

        ruta_docx = generar_informe_tecnico(intake, pd.Series(tramite))

        ruta_nas = nas.exportar_a_nas(
            ruta_docx,
            numero_informe=tramite["numero_informe"],
            anio=anio,
            tipo_tramite=tipo_tramite,
            tipo_bien=equipo["tipo_bien"],
            area=area,
        )

        db.registrar_tramite(
            conn,
            {
                **tramite,
                "ruta_docx": str(ruta_docx),
                "ruta_nas": str(ruta_nas) if ruta_nas else None,
            },
        )
        db.registrar_equipo(
            conn,
            {
                "id_tramite": id_tramite,
                "usuario": equipo["usuario"],
                "area": equipo["area"],
                "cargo_usuario": equipo.get("cargo_usuario", ""),
                "tipo_bien": equipo["tipo_bien"],
                "serie": equipo.get("serie", ""),
                "marca_modelo": equipo.get("marca_modelo", ""),
                "ram_gb": equipo.get("ram_gb"),
                "disco_tipo": equipo.get("disco_tipo", ""),
                "disco_gb": equipo.get("disco_gb"),
                "especificaciones": equipo.get("especificaciones_override", ""),
            },
        )

    print(f"\nInforme generado: {ruta_docx}")
    if ruta_nas:
        print(f"Copiado al NAS: {ruta_nas}")
    else:
        print("NAS no configurado (variable de entorno INFORMES_NAS_PATH vacia), solo quedo local.")
