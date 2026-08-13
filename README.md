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

# Carpeta donde el script de escaneo de hardware deja sus .json (compartida
# en el NAS para que cualquier tecnico los recoja desde el wizard)
$env:INFORMES_ESCANEOS_PATH = "\\NAS\TI\Escaneos"
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
python scripts\escanear_hardware.py \\NAS\TI\Escaneos
```

Genera un `.json` con serie, marca/modelo, RAM, tipo y tamano de disco,
directamente en la carpeta compartida (usa la misma ruta que
`INFORMES_ESCANEOS_PATH`). De vuelta en tu PC, el wizard
(`python -m informes nuevo`) detecta los escaneos disponibles y te deja
elegir uno por nombre de equipo — autocompleta RAM/disco/serie/modelo, y tu
solo confirmas o corriges los campos que el escaneo no puede saber (estado,
ubicacion).

## Responsables por area (hoja `Responsables` del intake)

Al elegir un area en el wizard, se sugiere autom\u00e1ticamente el responsable
(etiqueta + nombre) desde esta hoja, para no volver a tipearlo cada vez.
Si el area no est\u00e1 en la tabla, el wizard simplemente pide los datos a mano.
Edita la hoja libremente para mantenerla al d\u00eda.

## Perfil local

La primera vez que corres `python -m informes nuevo`, te pide tu nombre,
cargo, destinatario habitual, etc. y lo guarda en `perfil_local.json` (no se
sube a git, es por maquina/tecnico) para no volver a pedirlo.

## Arquitectura cliente-servidor (recomendado con varios tecnicos)

Sin servidor configurado, cada tecnico genera informes localmente con su
propia copia de la plantilla, el catalogo y una base SQLite propia. Funciona,
pero cada quien puede quedar con una version distinta y no hay numeracion
compartida.

Con el servidor corriendo (en Docker, en el NAS), el wizard deja de generar
nada localmente: le manda los datos al servidor por HTTP, y el servidor
asigna el numero de informe, genera el `.docx` con la plantilla oficial, lo
guarda en el NAS con la nomenclatura, y lo registra en una unica base de
datos compartida.

Para activarlo, en la PC del tecnico:

```powershell
$env:INFORMES_API_URL = "http://IP-DEL-NAS:8000"
$env:INFORMES_API_KEY = "la-misma-clave-que-pusiste-en-.env"
python -m informes nuevo
python -m informes buscar --area "Farmacia"
```

Sin esas 2 variables, el sistema sigue funcionando 100% local (buen respaldo
si el NAS esta caido o estas trabajando offline).

### Desplegar el servidor en un QNAP con Container Station

1. Habilita SSH en el QNAP (Panel de Control \u2192 Red y Archivos \u2192 Telnet/SSH)
   y copia esta carpeta completa a una carpeta compartida, por ejemplo
   `/share/CACHEDEV1_DATA/Sistemas/informes-api` (usa File Station o `scp`).

2. Crea la carpeta donde ya guardas los informes hoy si no existe, por
   ejemplo `/share/Informes`.

3. Copia `.env.example` a `.env` y edita los 2 valores:

   ```
   INFORMES_API_KEY=una-clave-larga-que-solo-conozcan-los-tecnicos
   RUTA_CARPETA_NAS_INFORMES=/share/Informes
   ```

4. Por SSH, parado en la carpeta del proyecto dentro del QNAP:

   ```bash
   docker compose up -d --build
   ```

   (Si tu QNAP no tiene `docker compose` como plugin, usa Container Station
   \u2192 "Crear" \u2192 "Aplicacion" \u2192 importa este mismo `docker-compose.yml`.)

5. Verifica que responde:

   ```bash
   curl http://localhost:8000/salud
   ```

6. Desde cualquier PC de la clinica en la misma LAN:

   ```
   http://IP-DEL-QNAP:8000/salud
   ```

   debe devolver `{"status":"ok"}`. Esa IP es la que usan los tecnicos en
   `INFORMES_API_URL`.

7. Opcional pero recomendado: en el QNAP, resérvale una IP fija al equipo
   (DHCP reservation en tu router) para que `INFORMES_API_URL` no se rompa
   si el QNAP cambia de IP tras un reinicio.

Como todo corre dentro de la LAN de la clinica, no hace falta HTTPS ni VPN
para esto \u2014 la API key en el header evita que cualquiera en la red escriba
informes sin querer, pero no es seguridad de nivel internet. Si alguna vez
el NAS queda expuesto a internet (no deberia), habria que agregar HTTPS y
repensar la autenticacion.


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

## Estado actual del motor de informes tecnicos (v2)

El motor real (`render_v2.py` + `wizard.py`) qued\u00f3 validado contra informes
reales de la cl\u00ednica y reemplaza al motor original (`render.py`, usado solo
por `python -m informes generar` desde el Excel de intake, que sigue
funcionando pero representa el dise\u00f1o viejo de "un bloque por equipo").

Diferencias clave descubiertas al comparar con informes reales:

- Cuando un tr\u00e1mite tiene varios equipos, van **todos en una sola tabla**
  (una fila por equipo), no en bloques repetidos por p\u00e1gina.
- Hay 2 "estilos" de informe seg\u00fan el tipo de bien (`config.TIPOS_BIEN`):
  - **equipo** (CPU, Laptop, All In One, Monitor, Impresora, Mouse, Teclado,
    Audifonos, Repotenciacion): tabla con columnas t\u00e9cnicas (RAM, disco,
    procesador, serie, etc.) + secci\u00f3n "DESCRIPCION DEL PROBLEMA" (solo en
    baja/diagn\u00f3stico) + recomendaci\u00f3n consolidada.
  - **consumible** (Toner y similares): tabla de "Estado de suministro"
    (\u00e1rea, etiqueta, modelo, serie, nivel actual), sin descripci\u00f3n de
    problema.
- Las columnas de la tabla para Mouse/Teclado/Audifonos son un supuesto
  (modelo/ubicaci\u00f3n/serie, igual que Monitor/Impresora) pendiente de
  confirmar con un informe real de esos tipos.
- El pie del informe (Jefatura / A cargo / Jefe) es un campo libre
  (`etiqueta_responsable`) porque var\u00eda seg\u00fan el caso.

### Pendiente (no conectado todav\u00eda a este motor v2)

- `server/app.py` (la API de Docker) todav\u00eda usa el modelo de datos viejo
  (un bloque por equipo). Hay que actualizarla para que hable el mismo
  formato que `wizard.py` v2 antes de volver a usar el flujo cliente-servidor.
- El formulario oficial de baja patrimonial (`MAN.F.10`, con logo y c\u00f3digo
  de versi\u00f3n) y el SOLPED de sustento (`RSC.AD.GFI.PR.001.01`, con centro de
  costo y presupuesto) son formularios corporativos codificados, distintos al
  "informe t\u00e9cnico". Se rellenan sobre el archivo oficial existente en vez
  de reconstruirse desde cero, para no romper el dise\u00f1o/logo. A\u00fan no est\u00e1n
  automatizados.

