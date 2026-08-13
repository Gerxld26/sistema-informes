import sqlite3
from contextlib import contextmanager
from pathlib import Path

from . import config

ESQUEMA = """
CREATE TABLE IF NOT EXISTS tramites (
    id_tramite TEXT PRIMARY KEY,
    numero_informe INTEGER NOT NULL,
    anio INTEGER NOT NULL,
    tipo_tramite TEXT NOT NULL,
    tecnico_nombre TEXT NOT NULL,
    area TEXT,
    fecha TEXT NOT NULL,
    destinatario_nombre TEXT,
    ruta_docx TEXT,
    ruta_nas TEXT,
    creado_en TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS equipos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    id_tramite TEXT NOT NULL REFERENCES tramites(id_tramite),
    usuario TEXT NOT NULL,
    area TEXT,
    cargo_usuario TEXT,
    tipo_bien TEXT,
    serie TEXT,
    marca_modelo TEXT,
    ram_gb REAL,
    disco_tipo TEXT,
    disco_gb REAL,
    especificaciones TEXT
);

CREATE INDEX IF NOT EXISTS idx_tramites_tecnico ON tramites(tecnico_nombre);
CREATE INDEX IF NOT EXISTS idx_tramites_area ON tramites(area);
CREATE INDEX IF NOT EXISTS idx_tramites_fecha ON tramites(fecha);
CREATE INDEX IF NOT EXISTS idx_tramites_numero ON tramites(numero_informe);
"""


@contextmanager
def conexion(ruta_db: Path = config.RUTA_DB):
    ruta_db = Path(ruta_db)
    ruta_db.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(ruta_db))
    conn.row_factory = sqlite3.Row
    try:
        conn.executescript(ESQUEMA)
        yield conn
        conn.commit()
    finally:
        conn.close()


def registrar_tramite(conn, tramite: dict):
    conn.execute(
        """
        INSERT INTO tramites
            (id_tramite, numero_informe, anio, tipo_tramite, tecnico_nombre,
             area, fecha, destinatario_nombre, ruta_docx, ruta_nas)
        VALUES (:id_tramite, :numero_informe, :anio, :tipo_tramite, :tecnico_nombre,
                :area, :fecha, :destinatario_nombre, :ruta_docx, :ruta_nas)
        ON CONFLICT(id_tramite) DO UPDATE SET
            ruta_docx = excluded.ruta_docx,
            ruta_nas = excluded.ruta_nas
        """,
        tramite,
    )


def registrar_equipo(conn, equipo: dict):
    conn.execute(
        """
        INSERT INTO equipos
            (id_tramite, usuario, area, cargo_usuario, tipo_bien, serie,
             marca_modelo, ram_gb, disco_tipo, disco_gb, especificaciones)
        VALUES (:id_tramite, :usuario, :area, :cargo_usuario, :tipo_bien, :serie,
                :marca_modelo, :ram_gb, :disco_tipo, :disco_gb, :especificaciones)
        """,
        equipo,
    )


def buscar_tramites(
    conn,
    tecnico: str | None = None,
    numero_informe: int | None = None,
    fecha: str | None = None,
    area: str | None = None,
    tipo_tramite: str | None = None,
):
    filtros = []
    valores = {}

    if tecnico:
        filtros.append("tecnico_nombre LIKE :tecnico")
        valores["tecnico"] = f"%{tecnico}%"
    if numero_informe:
        filtros.append("numero_informe = :numero_informe")
        valores["numero_informe"] = numero_informe
    if fecha:
        filtros.append("fecha = :fecha")
        valores["fecha"] = fecha
    if area:
        filtros.append("area LIKE :area")
        valores["area"] = f"%{area}%"
    if tipo_tramite:
        filtros.append("tipo_tramite = :tipo_tramite")
        valores["tipo_tramite"] = tipo_tramite

    where = f"WHERE {' AND '.join(filtros)}" if filtros else ""
    consulta = f"SELECT * FROM tramites {where} ORDER BY fecha DESC, numero_informe DESC"
    return conn.execute(consulta, valores).fetchall()


def equipos_de_tramite(conn, id_tramite: str):
    return conn.execute(
        "SELECT * FROM equipos WHERE id_tramite = :id_tramite", {"id_tramite": id_tramite}
    ).fetchall()
