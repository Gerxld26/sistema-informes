import requests

from . import config


class ErrorApi(Exception):
    pass


def _cabeceras():
    return {"X-API-Key": config.API_KEY} if config.API_KEY else {}


def servidor_configurado() -> bool:
    return bool(config.API_URL)


def obtener_areas() -> list[str]:
    resp = requests.get(f"{config.API_URL}/areas", timeout=10)
    resp.raise_for_status()
    return resp.json()


def crear_tramite(payload: dict) -> dict:
    resp = requests.post(
        f"{config.API_URL}/tramites", json=payload, headers=_cabeceras(), timeout=30
    )
    if resp.status_code == 401:
        raise ErrorApi("API key invalida o faltante. Configura INFORMES_API_KEY.")
    resp.raise_for_status()
    return resp.json()


def buscar_tramites(**filtros) -> list[dict]:
    filtros = {k: v for k, v in filtros.items() if v}
    resp = requests.get(f"{config.API_URL}/tramites", params=filtros, timeout=15)
    resp.raise_for_status()
    return resp.json()
