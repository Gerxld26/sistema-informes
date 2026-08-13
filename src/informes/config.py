import os
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent.parent

RUTA_PLANTILLA_INFORME_TECNICO = RAIZ / "plantillas" / "plantilla_informe_tecnico.docx"
RUTA_INTAKE_DEFAULT = RAIZ / "intake" / "intake_informes.xlsx"
RUTA_SALIDA = RAIZ / "salida"
RUTA_DB = Path(os.environ.get("INFORMES_DB_PATH", RAIZ / "informes.db"))
RUTA_NAS = os.environ.get("INFORMES_NAS_PATH")

HOJA_TRAMITES = "Tramites"
HOJA_EQUIPOS = "Equipos"
HOJA_CATALOGO = "Catalogo_Equipos"

AREAS_CLINICA = [
    "Farmacia Corporativa",
    "Contabilidad",
    "Sistemas",
    "Admisi\u00f3n",
    "Enfermer\u00eda",
    "Laboratorio",
    "Recursos Humanos",
    "Gerencia General",
]

TEXTOS_TIPO_TRAMITE = {
    "implementacion": {
        "verbo": "la implementaci\u00f3n de",
        "plural_1": "equipo",
        "plural_n": "equipos",
        "asunto": "IMPLEMENTACI\u00d3N DE",
    },
    "baja": {
        "verbo": "la baja de",
        "plural_1": "equipo",
        "plural_n": "equipos",
        "asunto": "BAJA DE",
    },
    "diagnostico": {
        "verbo": "el diagn\u00f3stico de",
        "plural_1": "equipo",
        "plural_n": "equipos",
        "asunto": "DIAGN\u00d3STICO DE",
    },
}

