# Sistema de Informes T\u00e9cnicos

Genera autom\u00e1ticamente los informes t\u00e9cnicos (Word) de implementaci\u00f3n, baja y
diagn\u00f3stico de equipos, a partir de un \u00fanico Excel de intake. Soporta m\u00faltiples
equipos por tr\u00e1mite y especificaciones recomendadas por \u00e1rea/cargo mediante un
cat\u00e1logo editable.

## Estructura

```
sistema_informes/
\u251c\u2500\u2500 requirements.txt
\u251c\u2500\u2500 src/informes/          # codigo del sistema (paquete python)
\u2502   \u251c\u2500\u2500 config.py           # rutas y constantes
\u2502   \u251c\u2500\u2500 catalogo.py         # motor de reglas (specs por cargo/area)
\u2502   \u251c\u2500\u2500 textos.py           # textos de justificacion por defecto
\u2502   \u251c\u2500\u2500 intake.py           # lectura/validacion del excel
\u2502   \u251c\u2500\u2500 render.py           # arma contexto y llama a docxtpl
\u2502   \u2514\u2500\u2500 cli.py              # punto de entrada
\u251c\u2500\u2500 plantillas/             # plantillas .docx con marcadores {{ }}
\u251c\u2500\u2500 intake/                 # excel(es) de intake
\u251c\u2500\u2500 scripts/                # scripts puntuales (regenerar plantilla/intake demo)
\u2514\u2500\u2500 salida/                 # informes generados (no se versiona)
```

## Setup (Windows / PowerShell / VS Code)

```powershell
# 1. Crear y activar entorno virtual
python -m venv venv
.\venv\Scripts\Activate.ps1

# Si PowerShell bloquea la activacion por politica de ejecucion:
# Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned

# 2. Instalar dependencias + el paquete en modo editable
pip install -r requirements.txt
pip install -e .

# 3. Generar informes usando el intake por defecto (intake/intake_informes.xlsx)
python -m informes

# 4. O usando otro archivo de intake
python -m informes --intake "ruta\a\otro_intake.xlsx"
```

> VS Code: selecciona el int\u00e9rprete del venv con `Ctrl+Shift+P` \u2192
> "Python: Select Interpreter" \u2192 `.\venv\Scripts\python.exe`, para que el
> editor deje de marcar `pandas`/`docxtpl` como no encontrados.

## C\u00f3mo se usa d\u00eda a d\u00eda

1. Abrir `intake/intake_informes.xlsx`.
2. En la hoja **Tramites**: una fila por tr\u00e1mite (n\u00famero de informe, tipo,
   fecha, t\u00e9cnico, destinatario).
3. En la hoja **Equipos**: una fila por equipo, referenciando el `id_tramite`
   correspondiente. Un tr\u00e1mite con 5 equipos = 5 filas con el mismo `id_tramite`.
4. Dejar `especificaciones_override` vac\u00edo para que el sistema use el
   **Cat\u00e1logo_Equipos** autom\u00e1ticamente seg\u00fan `cargo_usuario` / `area`; llenarlo
   solo en casos especiales.
5. Correr `python -m informes`.
6. Los `.docx` quedan en `salida/`.

## Editar el cat\u00e1logo de equipos recomendados

Hoja **Catalogo_Equipos** del intake. Prioridad de b\u00fasqueda: `cargo` >
`area` > `default`. Se puede editar libremente sin tocar c\u00f3digo \u2014 por
ejemplo, para agregar una regla de laptop para gerentes que hoy cae al
default.

## Comandos disponibles

```powershell
# Genera informes en lote desde el Excel de intake (flujo original)
python -m informes generar

# Wizard interactivo: crea un tramite respondiendo preguntas cortas,
# numera el informe automaticamente, genera el .docx, lo copia al NAS
# (si INFORMES_NAS_PATH esta configurada) y lo registra en la base de datos
python -m informes nuevo

# Busca tramites ya generados (trazabilidad)
python -m informes buscar --tecnico "Antony"
python -m informes buscar --area "Farmacia"
python -m informes buscar --numero 106
python -m informes buscar --fecha "23/04/2026"
python -m informes buscar --tipo baja
```

## Variables de entorno opcionales

```powershell
# Ruta del NAS donde se copian automaticamente los informes generados
$env:INFORMES_NAS_PATH = "\\NAS\TI\Informes"

# Ruta de la base de datos (por defecto: informes.db en la raiz del proyecto)
$env:INFORMES_DB_PATH = "\\NAS\TI\informes.db"
```

Si `INFORMES_DB_PATH` apunta a una ruta en el NAS, todos los tecnicos comparten
la misma base y las busquedas de trazabilidad ven los tramites de todos. Ojo:
SQLite sobre una carpeta compartida (SMB) tolera bien lecturas concurrentes,
pero con muchos tecnicos escribiendo al mismo tiempo puede haber bloqueos. Si
el equipo crece, migrar a un servidor de base de datos real (Postgres/MySQL)
es el siguiente paso natural.

## Escaneo de hardware (evita fotos y tipeo manual)

En la PC del usuario (Windows), corre:

```powershell
python scripts\escanear_hardware.py C:\ruta\donde\guardar
```

Genera un `.json` con serie, marca/modelo, RAM, tipo y tamano de disco. El
wizard (`python -m informes nuevo`) pregunta por la ruta a ese archivo y
autocompleta esos campos.

## Perfil local

La primera vez que corres `python -m informes nuevo`, te pide tu nombre,
cargo, destinatario habitual, etc. y lo guarda en `perfil_local.json` (no se
sube a git, es por maquina/tecnico) para no volver a pedirlo.

## Pr\u00f3ximos pasos (roadmap)

- [ ] Agregar generador de **informe de baja** (mismo intake, nueva plantilla)
- [ ] Agregar generador de **sustento (Excel)**
- [ ] Tests con `pytest` sobre `catalogo.py` y `render.py`
- [ ] Probar `escanear_hardware.py` en Windows real y ajustar segun resultados

## Regenerar la plantilla o el intake de ejemplo

```powershell
python scripts\crear_plantilla.py
python scripts\crear_intake.py
```

Estos scripts reconstruyen `plantillas/plantilla_informe_tecnico.docx` e
`intake/intake_informes.xlsx` desde cero \u2014 \u00fatiles si quieren cambiar el
dise\u00f1o base sin editar el .docx a mano.
