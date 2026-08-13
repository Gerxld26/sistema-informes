import json
import pandas as pd
from datetime import date
from pathlib import Path

from . import config, db, nas, perfil
from .catalogo import ReglaNoEncontrada, buscar_especificaciones
from .render_v2 import generar_informe_tecnico_v2

TIPOS_TRAMITE = list(config.TEXTOS_TIPO_TRAMITE.keys())
TIPOS_BIEN = list(config.TIPOS_BIEN.keys())
ETIQUETAS_RESPONSABLE = ["JEFATURA", "A CARGO", "JEFE"]


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


def cargar_responsables() -> pd.DataFrame:
    return pd.read_excel(config.RUTA_INTAKE_DEFAULT, sheet_name=config.HOJA_RESPONSABLES)


def buscar_responsable(responsables_df: pd.DataFrame, area: str) -> dict | None:
    filas = responsables_df[
        responsables_df["area"].astype(str).str.strip().str.lower() == str(area).strip().lower()
    ]
    if filas.empty:
        return None
    fila = filas.iloc[0]
    return {"etiqueta_responsable": fila["etiqueta_responsable"], "nombre_responsable": fila["nombre_responsable"]}


def elegir_responsable(area: str) -> tuple[str, str]:
    try:
        responsables_df = cargar_responsables()
        sugerido = buscar_responsable(responsables_df, area)
    except Exception:
        sugerido = None

    if sugerido:
        usar = input(
            f"\nResponsable sugerido para '{area}': {sugerido['etiqueta_responsable']} = "
            f"{sugerido['nombre_responsable']}. Usar este? (enter = si, 'n' = cambiar): "
        ).strip().lower()
        if usar != "n":
            return sugerido["etiqueta_responsable"], sugerido["nombre_responsable"]

    etiqueta_responsable = elegir_opcion("Etiqueta del responsable", ETIQUETAS_RESPONSABLE)
    nombre_responsable = input("Nombre del responsable: ").strip()
    return etiqueta_responsable, nombre_responsable


def listar_escaneos_disponibles() -> list[Path]:
    if not config.RUTA_ESCANEOS or not config.RUTA_ESCANEOS.exists():
        return []
    return sorted(config.RUTA_ESCANEOS.glob("escaneo_*.json"), reverse=True)


def cargar_escaneo(ruta: Path) -> dict:
    return json.loads(ruta.read_text(encoding="utf-8"))


def ofrecer_escaneo_hardware() -> dict:
    escaneos = listar_escaneos_disponibles()
    if not escaneos:
        return {}

    print("\nEscaneos de hardware disponibles:")
    print("  0. No usar ninguno (llenar a mano)")
    for i, ruta in enumerate(escaneos[:10], start=1):
        datos = cargar_escaneo(ruta)
        print(f"  {i}. {datos.get('hostname', ruta.stem)} - {datos.get('fecha_escaneo', '')}")

    eleccion = input("Elige un numero: ").strip()
    if not eleccion.isdigit() or int(eleccion) == 0:
        return {}

    idx = int(eleccion) - 1
    if 0 <= idx < len(escaneos[:10]):
        return cargar_escaneo(escaneos[idx])
    return {}


def capturar_fila_equipo(columnas: list[str]) -> dict:
    escaneo = ofrecer_escaneo_hardware()
    mapa_escaneo = {
        "ram": f"{escaneo['ram_gb']}GB" if escaneo.get("ram_gb") else None,
        "disco": f"{escaneo['disco_gb']}GB {escaneo.get('disco_tipo', '')}".strip() if escaneo.get("disco_gb") else None,
        "serie": escaneo.get("serie"),
        "modelo": escaneo.get("marca_modelo"),
        "procesador": escaneo.get("cpu"),
    }

    fila = {}
    for col in columnas:
        etiqueta = config.ETIQUETAS_COLUMNA.get(col, col)
        sugerido = mapa_escaneo.get(col)
        if sugerido:
            valor = input(f"  {etiqueta} (enter = '{sugerido}'): ").strip()
            fila[col] = valor or sugerido
        else:
            fila[col] = input(f"  {etiqueta}: ").strip()
    return fila


def capturar_equipos(tipo_bien: str) -> list[dict]:
    columnas = config.TIPOS_BIEN[tipo_bien]["columnas"]
    cantidad = int(input("\nCuantos registros van en la tabla del informe? ").strip() or "1")
    filas = []
    for i in range(cantidad):
        print(f"\n--- Registro {i + 1} de {cantidad} ---")
        filas.append(capturar_fila_equipo(columnas))
    return filas


def capturar_descripcion_problema() -> list[str]:
    print("\nDescribe el problema, un punto por linea. Linea vacia para terminar.")
    puntos = []
    while True:
        linea = input("- ").strip()
        if not linea:
            break
        puntos.append(linea)
    return puntos


def capturar_especificaciones(catalogo_df: pd.DataFrame, tipo_bien: str, area: str) -> list[str]:
    override = input(
        "\nEspecificaciones manuales separadas por ';' (enter para usar el catalogo): "
    ).strip()
    if override:
        return [e.strip() for e in override.split(";") if e.strip()]

    try:
        return buscar_especificaciones(catalogo_df, cargo="", area=area, tipo_bien=tipo_bien)
    except ReglaNoEncontrada as exc:
        print(f"[AVISO] {exc}")
        return ["** ESPECIFICAR MANUALMENTE - no se encontro regla en catalogo **"]


def capturar_grupos_problema() -> list[dict]:
    grupos = []
    print("\nAgrupa el problema por tipo de dispositivo (ej: TECLADOS, MOUSE).")
    while True:
        titulo = input("\nNombre del grupo (enter para terminar): ").strip()
        if not titulo:
            break
        print(f"Puntos de falla para {titulo}, uno por linea. Linea vacia para terminar.")
        puntos = []
        while True:
            punto = input("- ").strip()
            if not punto:
                break
            puntos.append(punto)
        grupos.append({"titulo": f"{titulo.upper()}:", "puntos": puntos})
    return grupos


def capturar_recomendaciones() -> list[str]:
    print("\nLineas de recomendacion, una por linea. Linea vacia para terminar.")
    recomendaciones = []
    while True:
        linea = input("- ").strip()
        if not linea:
            break
        recomendaciones.append(linea)
    return recomendaciones


def ejecutar_wizard():
    perfil_tecnico = perfil.cargar_o_crear_perfil()

    tipo_tramite = elegir_opcion("Tipo de tramite", TIPOS_TRAMITE)
    area = elegir_opcion("Area", config.AREAS_CLINICA, permitir_otro=True)
    tipo_bien = elegir_opcion("Tipo de bien", TIPOS_BIEN)

    usuario = input("\nUsuario o area destino (nombre, 'VARIOS', 'MEDICOS', etc): ").strip() or "Varios"
    etiqueta_responsable, nombre_responsable = elegir_responsable(area)

    estilo = config.TIPOS_BIEN[tipo_bien]["estilo"]
    asunto_linea1 = input("\nAsunto (linea 1): ").strip()
    asunto_linea2 = input("Asunto (linea 2, enter para omitir): ").strip()

    anio = date.today().year
    fecha = date.today().strftime("%d/%m/%Y")

    tramite = {
        "numero_informe": None,
        "anio": anio,
        "tipo_tramite": tipo_tramite,
        "tipo_bien": tipo_bien,
        "area": area,
        "usuario": usuario,
        "siglas_sede": perfil_tecnico["siglas_sede"],
        "fecha": fecha,
        "tecnico_nombre": perfil_tecnico["tecnico_nombre"],
        "tecnico_cargo": perfil_tecnico["tecnico_cargo"],
        "destinatario_nombre": perfil_tecnico["destinatario_nombre"],
        "destinatario_cargo": perfil_tecnico["destinatario_cargo"],
        "jefe_ti_nombre": perfil_tecnico["jefe_ti_nombre"],
        "jefe_ti_cargo": perfil_tecnico["jefe_ti_cargo"],
        "asunto_linea1": asunto_linea1,
        "asunto_linea2": asunto_linea2,
        "etiqueta_responsable": etiqueta_responsable,
        "nombre_responsable": nombre_responsable,
    }

    if estilo == config.ESTILO_PERIFERICO:
        equipos = []
        tramite["intro"] = input(
            "\nFrase introductoria (ej: 'Mediante el presente, se informa que...'): "
        ).strip()
        tramite["grupos_problema"] = capturar_grupos_problema()
        tramite["conclusion"] = input("\nParrafo de conclusion: ").strip()
        tramite["recomendaciones"] = capturar_recomendaciones()
    else:
        equipos = capturar_equipos(tipo_bien)

        info_tipo = config.TEXTOS_TIPO_TRAMITE[tipo_tramite]
        descripcion_problema = []
        if info_tipo["tiene_descripcion_problema"]:
            tramite["intro"] = input(
                "\nFrase introductoria (ej: 'Mediante el presente, se informa que...'): "
            ).strip()
            descripcion_problema = capturar_descripcion_problema()
        else:
            tramite["intro"] = input("\nParrafo de introduccion / justificacion: ").strip()
        tramite["descripcion_problema"] = descripcion_problema

        catalogo_df = cargar_catalogo()
        tramite["especificaciones"] = capturar_especificaciones(catalogo_df, tipo_bien, area)

        tramite["texto_recomendacion"] = ""
        if estilo == config.ESTILO_EQUIPO:
            cantidad_solicitada = input(
                f"\nCantidad a solicitar (enter = {len(equipos):02d}): "
            ).strip() or str(len(equipos)).zfill(2)
            tramite["texto_recomendacion"] = f"Se requiere la compra de {cantidad_solicitada} {tipo_bien.upper()}"

    with db.conexion() as conn:
        numero_informe = siguiente_numero_informe(conn, anio)
        id_tramite = f"{anio}-{numero_informe:03d}"
        tramite["id_tramite"] = id_tramite
        tramite["numero_informe"] = numero_informe

        ruta_docx = generar_informe_tecnico_v2(tramite, equipos)

        ruta_nas = nas.exportar_a_nas(
            ruta_docx,
            numero_informe=numero_informe,
            anio=anio,
            tipo_tramite=tipo_tramite,
            tipo_bien=tipo_bien,
            area=area,
        )

        db.registrar_tramite(
            conn,
            {**tramite, "ruta_docx": str(ruta_docx), "ruta_nas": str(ruta_nas) if ruta_nas else None},
        )
        for fila_equipo in equipos:
            db.registrar_equipo(conn, id_tramite, fila_equipo)

    print(f"\nInforme generado: {ruta_docx}")
    if ruta_nas:
        print(f"Copiado al NAS: {ruta_nas}")
    else:
        print("NAS no configurado (variable de entorno INFORMES_NAS_PATH vacia), solo quedo local.")
