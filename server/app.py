import threading
from datetime import date
from typing import Optional

import pandas as pd
from fastapi import Depends, FastAPI, Header, HTTPException
from pydantic import BaseModel

from informes import config, db, nas
from informes.intake import Intake
from informes.render import generar_informe_tecnico

app = FastAPI(title="Sistema de Informes Tecnicos - API")
bloqueo_numeracion = threading.Lock()


def verificar_api_key(x_api_key: str = Header(default="")):
    if config.API_KEY and x_api_key != config.API_KEY:
        raise HTTPException(status_code=401, detail="API key invalida")


class EquipoIn(BaseModel):
    usuario: str
    cargo_usuario: str = ""
    sede_usuario: str = ""
    jefatura: str = ""
    tipo_bien: str
    equipo_actual_marca_estado: str = ""
    sede_equipo_actual: str = ""
    especificaciones_override: str = ""
    texto_justificacion_override: str = ""
    serie: str = ""
    marca_modelo: str = ""
    ram_gb: Optional[float] = None
    disco_tipo: str = ""
    disco_gb: Optional[float] = None
    cantidad: int = 1


class TramiteIn(BaseModel):
    tipo_tramite: str
    area: str
    tecnico_nombre: str
    tecnico_cargo: str
    siglas_sede: str
    destinatario_nombre: str
    destinatario_cargo: str
    jefe_ti_nombre: str
    jefe_ti_cargo: str
    equipos: list[EquipoIn]


def cargar_catalogo() -> pd.DataFrame:
    return pd.read_excel(config.RUTA_INTAKE_DEFAULT, sheet_name=config.HOJA_CATALOGO)


@app.get("/salud")
def salud():
    return {"status": "ok"}


@app.get("/areas")
def areas():
    return config.AREAS_CLINICA


@app.get("/catalogo")
def catalogo():
    return cargar_catalogo().fillna("").to_dict(orient="records")


@app.post("/tramites", dependencies=[Depends(verificar_api_key)])
def crear_tramite(payload: TramiteIn):
    if payload.tipo_tramite not in config.TEXTOS_TIPO_TRAMITE:
        raise HTTPException(status_code=400, detail=f"tipo_tramite invalido: {payload.tipo_tramite}")

    anio = date.today().year
    fecha = date.today().strftime("%d/%m/%Y")

    with bloqueo_numeracion, db.conexion() as conn:
        fila = conn.execute(
            "SELECT MAX(numero_informe) AS maximo FROM tramites WHERE anio = :anio", {"anio": anio}
        ).fetchone()
        numero_informe = (fila["maximo"] or 0) + 1
        id_tramite = f"{anio}-{numero_informe:03d}"

        tramite = {
            "id_tramite": id_tramite,
            "numero_informe": numero_informe,
            "anio": anio,
            "tipo_tramite": payload.tipo_tramite,
            "area": payload.area,
            "siglas_sede": payload.siglas_sede,
            "fecha": fecha,
            "tecnico_nombre": payload.tecnico_nombre,
            "tecnico_cargo": payload.tecnico_cargo,
            "destinatario_nombre": payload.destinatario_nombre,
            "destinatario_cargo": payload.destinatario_cargo,
            "jefe_ti_nombre": payload.jefe_ti_nombre,
            "jefe_ti_cargo": payload.jefe_ti_cargo,
        }

        equipos = [
            {**eq.model_dump(), "id_tramite": id_tramite, "area": payload.area} for eq in payload.equipos
        ]

        intake = Intake(
            tramites=pd.DataFrame([tramite]),
            equipos=pd.DataFrame(equipos),
            catalogo=cargar_catalogo(),
        )

        ruta_docx = generar_informe_tecnico(intake, pd.Series(tramite))

        ruta_nas = nas.exportar_a_nas(
            ruta_docx,
            numero_informe=numero_informe,
            anio=anio,
            tipo_tramite=payload.tipo_tramite,
            tipo_bien=equipos[0]["tipo_bien"],
            area=payload.area,
        )

        db.registrar_tramite(
            conn,
            {**tramite, "ruta_docx": str(ruta_docx), "ruta_nas": str(ruta_nas) if ruta_nas else None},
        )
        for eq in equipos:
            db.registrar_equipo(
                conn,
                {
                    "id_tramite": id_tramite,
                    "usuario": eq["usuario"],
                    "area": payload.area,
                    "cargo_usuario": eq["cargo_usuario"],
                    "tipo_bien": eq["tipo_bien"],
                    "serie": eq["serie"],
                    "marca_modelo": eq["marca_modelo"],
                    "ram_gb": eq["ram_gb"],
                    "disco_tipo": eq["disco_tipo"],
                    "disco_gb": eq["disco_gb"],
                    "especificaciones": eq["especificaciones_override"],
                },
            )

    return {
        "id_tramite": id_tramite,
        "numero_informe": numero_informe,
        "anio": anio,
        "ruta_nas": str(ruta_nas) if ruta_nas else None,
    }


@app.get("/tramites")
def buscar_tramites(
    tecnico: Optional[str] = None,
    numero: Optional[int] = None,
    fecha: Optional[str] = None,
    area: Optional[str] = None,
    tipo: Optional[str] = None,
):
    with db.conexion() as conn:
        filas = db.buscar_tramites(
            conn, tecnico=tecnico, numero_informe=numero, fecha=fecha, area=area, tipo_tramite=tipo
        )
        resultado = []
        for fila in filas:
            tramite = dict(fila)
            tramite["equipos"] = [dict(e) for e in db.equipos_de_tramite(conn, fila["id_tramite"])]
            resultado.append(tramite)
        return resultado
