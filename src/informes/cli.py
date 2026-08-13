import argparse
import sys

from . import config, db
from .intake import IntakeInvalido, cargar_intake
from .render import generar_todos


def comando_generar(args):
    try:
        intake = cargar_intake(args.intake)
    except IntakeInvalido as exc:
        print(f"[ERROR] {exc}", file=sys.stderr)
        return 1

    generados = generar_todos(intake, carpeta_salida=args.salida)
    print(f"\n{len(generados)} informe(s) generado(s) en {args.salida}")
    return 0


def comando_nuevo(args):
    from .wizard import ejecutar_wizard

    ejecutar_wizard()
    return 0


def comando_buscar(args):
    with db.conexion() as conn:
        resultados = db.buscar_tramites(
            conn,
            tecnico=args.tecnico,
            numero_informe=args.numero,
            fecha=args.fecha,
            area=args.area,
            tipo_tramite=args.tipo,
        )

        if not resultados:
            print("No se encontraron tramites con esos filtros.")
            return 0

        for fila in resultados:
            print(
                f"{fila['id_tramite']:<12} N.{fila['numero_informe']:>3}-{fila['anio']}  "
                f"{fila['tipo_tramite']:<15} {fila['tipo_bien'] or '':<15} "
                f"{fila['tecnico_nombre']:<25} {fila['area'] or '':<20} {fila['fecha']}"
            )
            for eq in db.equipos_de_tramite(conn, fila["id_tramite"]):
                detalle = {k: v for k, v in eq.items() if k not in ("id", "serie") and v}
                print(f"    -> serie={eq['serie'] or 's/serie'} {detalle}")
            if fila["ruta_nas"]:
                print(f"    NAS: {fila['ruta_nas']}")
    return 0


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Sistema de informes tecnicos.")
    subparsers = parser.add_subparsers(dest="comando", required=True)

    p_generar = subparsers.add_parser("generar", help="Genera informes en batch desde el Excel de intake")
    p_generar.add_argument("--intake", default=config.RUTA_INTAKE_DEFAULT)
    p_generar.add_argument("--salida", default=config.RUTA_SALIDA)
    p_generar.set_defaults(func=comando_generar)

    p_nuevo = subparsers.add_parser("nuevo", help="Wizard interactivo para crear un tramite")
    p_nuevo.set_defaults(func=comando_nuevo)

    p_buscar = subparsers.add_parser("buscar", help="Busca tramites registrados")
    p_buscar.add_argument("--tecnico")
    p_buscar.add_argument("--numero", type=int)
    p_buscar.add_argument("--fecha")
    p_buscar.add_argument("--area")
    p_buscar.add_argument("--tipo")
    p_buscar.set_defaults(func=comando_buscar)

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
