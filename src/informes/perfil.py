import json
from pathlib import Path

from . import config

RUTA_PERFIL = config.RAIZ / "perfil_local.json"

CAMPOS = [
    ("tecnico_nombre", "Tu nombre completo"),
    ("tecnico_cargo", "Tu cargo"),
    ("siglas_sede", "Siglas que van despues de tus iniciales (ej: CHSP)"),
    ("destinatario_nombre", "Nombre del destinatario habitual (Jefe Corporativo TI)"),
    ("destinatario_cargo", "Cargo del destinatario"),
    ("jefe_ti_nombre", "Nombre de quien firma como Jefe TI"),
    ("jefe_ti_cargo", "Cargo de quien firma"),
]


def cargar_o_crear_perfil() -> dict:
    if RUTA_PERFIL.exists():
        return json.loads(RUTA_PERFIL.read_text(encoding="utf-8"))

    print("Primera vez que corres el wizard. Configuremos tu perfil (se guarda localmente, no se pide de nuevo).\n")
    perfil = {}
    for clave, etiqueta in CAMPOS:
        perfil[clave] = input(f"{etiqueta}: ").strip()

    RUTA_PERFIL.write_text(json.dumps(perfil, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\nPerfil guardado en {RUTA_PERFIL}\n")
    return perfil
