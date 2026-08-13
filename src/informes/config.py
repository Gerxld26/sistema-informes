import os
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent.parent

RUTA_PLANTILLA_INFORME_TECNICO = RAIZ / "plantillas" / "plantilla_informe_tecnico.docx"
RUTA_INTAKE_DEFAULT = RAIZ / "intake" / "intake_informes.xlsx"
RUTA_SALIDA = RAIZ / "salida"
RUTA_DB = Path(os.environ.get("INFORMES_DB_PATH", RAIZ / "informes.db"))
RUTA_NAS = os.environ.get("INFORMES_NAS_PATH")
RUTA_ESCANEOS = Path(os.environ["INFORMES_ESCANEOS_PATH"]) if os.environ.get("INFORMES_ESCANEOS_PATH") else None
API_KEY = os.environ.get("INFORMES_API_KEY", "")
API_URL = os.environ.get("INFORMES_API_URL", "")

HOJA_TRAMITES = "Tramites"
HOJA_EQUIPOS = "Equipos"
HOJA_CATALOGO = "Catalogo_Equipos"
HOJA_RESPONSABLES = "Responsables"

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

ESTILO_EQUIPO = "equipo"
ESTILO_CONSUMIBLE = "consumible"
ESTILO_PERIFERICO = "periferico"

COLUMNAS_EQUIPO_DEFAULT = ["ram", "disco", "estado", "modelo", "ubicacion", "procesador", "serie"]

TIPOS_BIEN = {
    "CPU": {"estilo": ESTILO_EQUIPO, "columnas": COLUMNAS_EQUIPO_DEFAULT},
    "Laptop": {"estilo": ESTILO_EQUIPO, "columnas": COLUMNAS_EQUIPO_DEFAULT},
    "All In One": {"estilo": ESTILO_EQUIPO, "columnas": COLUMNAS_EQUIPO_DEFAULT},
    "Monitor": {"estilo": ESTILO_EQUIPO, "columnas": ["modelo", "ubicacion", "serie"]},
    "Impresora": {"estilo": ESTILO_EQUIPO, "columnas": ["modelo", "ubicacion", "serie"]},
    "Repotenciacion": {"estilo": ESTILO_EQUIPO, "columnas": COLUMNAS_EQUIPO_DEFAULT},
    "Toner": {"estilo": ESTILO_CONSUMIBLE, "columnas": ["area", "etiqueta", "modelo", "serie", "nivel_actual"]},
    "Mouse": {"estilo": ESTILO_PERIFERICO, "columnas": []},
    "Teclado": {"estilo": ESTILO_PERIFERICO, "columnas": []},
    "Mouse y Teclado": {"estilo": ESTILO_PERIFERICO, "columnas": []},
    "Audifonos": {"estilo": ESTILO_PERIFERICO, "columnas": []},
}

ETIQUETAS_COLUMNA = {
    "ram": "RAM",
    "disco": "SATA/HDD",
    "estado": "ESTADO",
    "modelo": "MODELO",
    "ubicacion": "UBICACI\u00d3N",
    "procesador": "PROCESADOR",
    "serie": "SERIE",
    "etiqueta": "ETIQUETA",
    "nivel_actual": "NIVEL ACTUAL",
    "area": "AREA",
}

TEXTOS_TIPO_TRAMITE = {
    "implementacion": {
        "verbo": "la implementaci\u00f3n de",
        "plural_1": "equipo",
        "plural_n": "equipos",
        "asunto": "IMPLEMENTACI\u00d3N DE",
        "tiene_descripcion_problema": False,
    },
    "baja": {
        "verbo": "la baja de",
        "plural_1": "equipo",
        "plural_n": "equipos",
        "asunto": "BAJA DE",
        "tiene_descripcion_problema": True,
    },
    "diagnostico": {
        "verbo": "el diagn\u00f3stico de",
        "plural_1": "equipo",
        "plural_n": "equipos",
        "asunto": "DIAGN\u00d3STICO DE",
        "tiene_descripcion_problema": True,
    },
}

