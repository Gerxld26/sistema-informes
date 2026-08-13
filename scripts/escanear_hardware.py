import json
import socket
import subprocess
import sys
from datetime import datetime
from pathlib import Path


def powershell(comando: str) -> str:
    resultado = subprocess.run(
        ["powershell", "-NoProfile", "-Command", comando],
        capture_output=True,
        text=True,
        timeout=30,
    )
    return resultado.stdout.strip()


def obtener_serie() -> str:
    return powershell("(Get-CimInstance Win32_BIOS).SerialNumber")


def obtener_marca_modelo() -> str:
    fabricante = powershell("(Get-CimInstance Win32_ComputerSystem).Manufacturer")
    modelo = powershell("(Get-CimInstance Win32_ComputerSystem).Model")
    return f"{fabricante} {modelo}".strip()


def obtener_ram_gb() -> float:
    bytes_totales = powershell(
        "(Get-CimInstance Win32_ComputerSystem).TotalPhysicalMemory"
    )
    try:
        return round(int(bytes_totales) / (1024 ** 3), 1)
    except ValueError:
        return None


def obtener_disco() -> dict:
    salida = powershell(
        "Get-PhysicalDisk | Select-Object MediaType,Size,FriendlyName | ConvertTo-Json"
    )
    try:
        discos = json.loads(salida)
    except json.JSONDecodeError:
        return {"disco_tipo": "", "disco_gb": None}

    if isinstance(discos, dict):
        discos = [discos]
    if not discos:
        return {"disco_tipo": "", "disco_gb": None}

    principal = discos[0]
    return {
        "disco_tipo": principal.get("MediaType", ""),
        "disco_gb": round(principal.get("Size", 0) / (1024 ** 3), 1) if principal.get("Size") else None,
    }


def obtener_cpu() -> str:
    return powershell("(Get-CimInstance Win32_Processor).Name")


def escanear() -> dict:
    disco = obtener_disco()
    return {
        "hostname": socket.gethostname(),
        "fecha_escaneo": datetime.now().isoformat(timespec="seconds"),
        "serie": obtener_serie(),
        "marca_modelo": obtener_marca_modelo(),
        "cpu": obtener_cpu(),
        "ram_gb": obtener_ram_gb(),
        "disco_tipo": disco["disco_tipo"],
        "disco_gb": disco["disco_gb"],
    }


def main():
    if sys.platform != "win32":
        print("Este script usa WMI y solo corre en Windows.")
        return 1

    datos = escanear()

    carpeta_salida = Path(sys.argv[1]) if len(sys.argv) > 1 else Path.cwd()
    carpeta_salida.mkdir(parents=True, exist_ok=True)
    nombre_archivo = f"escaneo_{datos['hostname']}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    ruta = carpeta_salida / nombre_archivo
    ruta.write_text(json.dumps(datos, indent=2, ensure_ascii=False), encoding="utf-8")

    print(json.dumps(datos, indent=2, ensure_ascii=False))
    print(f"\nGuardado en: {ruta}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
