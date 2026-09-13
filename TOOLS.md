# TOOLS.md — Local Notes

Las skills definen _cómo_ funcionan las herramientas. Este archivo recoge _lo específico de esta instalación_: qué está conectado, con qué cuenta, para qué se usa cada servicio y dónde están las trampas.

## Acceso: Zapier MCP

Todos los servicios externos se alcanzan por **un único servidor MCP de Zapier**, configurado en `config/mcporter.json` (servidor `zapier`). No hay CLIs de Google instaladas: la skill `gog` aparece como _needs setup_ y **no debe configurarse** — supondría un OAuth nuevo.

**Dónde ejecutar `mcporter`.** Busca su config en `./config/mcporter.json`, relativa al directorio actual. Lanzado desde otro sitio falla con `Unknown MCP server 'zapier'`. Dos opciones válidas:

```bash
cd /root/.openclaw/workspace && mcporter ...
# o, desde cualquier sitio:
mcporter --config /root/.openclaw/workspace/config/mcporter.json ...
```

Patrón de llamada, siempre en este orden:

```bash
# 1. Ver qué apps y acciones hay disponibles
mcporter call zapier.inspect_zapier_actions selected_api=<APP> --output json

# 2. Ver el esquema exacto de una acción (nunca adivinar parámetros)
mcporter call zapier.inspect_zapier_actions tool_name=<tool_name> --output json

# 3. Resolver enums dinámicos (calendarios, listas de tareas…)
mcporter call zapier.inspect_zapier_actions tool_name=<tool_name> enum_property=<campo> --output json

# 4. Ejecutar
mcporter call zapier.execute_zapier_read_action  selected_api=<APP> action=<key> tool_name=<tool_name> --args '{"params":{...}}' --output json
mcporter call zapier.execute_zapier_write_action selected_api=<APP> action=<key> tool_name=<tool_name> --args '{"params":{...}}' --output json
```

Reglas duras:

- **Nunca inventes `action` ni `tool_name`.** Resuélvelos con `inspect_zapier_actions` en la misma sesión.
- Los parámetros van **anidados** en `--args '{"params":{...}}'`. Los `key=value` sueltos no llegan a la acción.
- No uses `enable_zapier_action`, `disable_zapier_action` ni `manage_zapier_connections`. Las conexiones están dadas; no se tocan.
- El token del servidor MCP no se imprime ni se comparte. Nunca.

### Límite de cuota (comprobado 2026-09-02)

La cuenta de Zapier está **sin tasks disponibles**: cualquier `execute_zapier_read_action` o `execute_zapier_write_action` devuelve

```text
insufficient tasks on account. To add more tasks to your account, visit: https://zapier.com/pricing
```

`inspect_zapier_actions` y `discover_zapier_actions` sí funcionan (no consumen task). Cuando aparezca este error: **dilo, no lo disimules**, y no reintentes en bucle. Una vez renovada la cuota, todo lo documentado aquí vuelve a funcionar sin cambios.

## Cuentas conectadas

Hay **tres identidades distintas** en juego. No las mezcles y avisa si el contexto de una petición no encaja con la cuenta que va a ejecutarla.

| Servicio        | `selected_api`         | Cuenta                                |
| --------------- | ---------------------- | ------------------------------------- |
| Gmail           | `GoogleMailV2CLIAPI`   | `rubeneai11@gmail.com`                |
| Google Calendar | `GoogleCalendarCLIAPI` | `rubeneai11@gmail.com`                |
| Google Tasks    | `GoogleTasksCLIAPI`    | (cuenta única "Google Tasks")         |
| Google Drive    | `GoogleDriveCLIAPI`    | `carerrulu@gmail.com`                 |
| Google Docs     | `GoogleDocsV2CLIAPI`   | `carerrulu@gmail.com`                 |
| Google Sheets   | `GoogleSheetsV2CLIAPI` | `carerrulu@gmail.com`                 |
| Notion          | `NotionCLIAPI`         | Rubén Losada (`riux@hotmail.es`)      |
| Telegram        | `TelegramCLIAPI`       | bot `AIE4_rub` (`@aie4rub_bot`)       |

⚠️ Correo y calendario viven en **una cuenta** y los documentos en **otra**. Un plan guardado en Docs no será visible desde la cuenta del calendario.

## Cuándo usar cada servicio

### Google Calendar → planificación temporal y bloques de trabajo

- Calendario por defecto: **`rubeneai11@gmail.com`**. Los otros dos disponibles (`Festivos en España`, `Holidays in Spain`) son de solo lectura: úsalos para _consultar_ festivos, nunca para escribir.
- Consultar antes de escribir: `google_calendar_find_events` (requiere `calendarid`; `start_time`/`end_time` aceptan lenguaje relativo tipo `now`, `+7 days`). **Ojo, están invertidos**: `start_time` = límite superior ("empieza antes de"), `end_time` = límite inferior ("termina después de", por defecto `now`). Para "próximos 7 días": `start_time="+7 days", end_time="now"`.
- Crear: `google_calendar_create_detailed_event` — requeridos `calendarid`, `summary`, `start__dateTime`, `end__dateTime`.
- **NO usar para:** listas de cosas por hacer sin hora (eso es Tasks), ni recordatorios que no ocupan tiempo real.
- **Nunca** borres, muevas ni modifiques un evento existente sin preguntar. Crear un bloque propio sí es libre.

#### Trampa de zonas horarias (aprendida a base de fallos)

Pasa siempre las fechas **con offset explícito**: `2026-09-03T09:00:00+02:00`.
Sin offset, la API interpreta la hora como **UTC** y el evento aparece desplazado (pasó de verdad: un evento de 18:30 acabó a la 01:30).

- Madrid está en **CEST (+02:00)** hasta el 25 de octubre de 2026; después **CET (+01:00)**.
- El servidor corre en **UTC**: `date` no da la hora de Rubén. Calcula el offset, no lo asumas.

### Google Tasks → tareas accionables

- Lista por defecto de trabajo del agente: **`Rocky`** (`task_list` = `aHRiRTBrMDF2Tll6Y0p6Qw`). Existe también `Szpilman Hietala's list`, que no es de Rubén: no escribas ahí.
- Crear: `google_tasks_create_task` — requeridos `title` y `task_list`; opcionales `notes` y `due`.
- Leer: `google_tasks_get_tasks_by_list` — requiere `task_list` **y** `show_completed` (`"true"`/`"false"`).
- **NO usar para:** cosas que necesitan un hueco de tiempo reservado (eso es Calendar) ni para notas de conocimiento (eso es Notion/Docs).

### Gmail → comunicaciones y correo

- Buscar: `gmail_find_email` con `query` en sintaxis de búsqueda de Gmail (`in:inbox is:unread newer_than:7d`, `from:`, `subject:`…).
- Leer y clasificar es libre. **Enviar, responder, reenviar, archivar, etiquetar o borrar requiere permiso explícito de Rubén** (ver `AGENTS.md` → _Acciones sensibles_).
- Si hace falta preparar una respuesta, usa `gmail_create_draft` y deja que Rubén la revise; no envíes.
- **Excepción puntual** (`skills/equation-solver`, autorizada por Rubén el 2026-09-13): responder automáticamente correos con "Ecuaciones" en el asunto, enviando la respuesta solo a `riux@hotmail.es`. No se extiende a ningún otro caso.
- **NO usar para:** avisar a Rubén de algo. Para eso, Telegram.

### Telegram → notificaciones breves al usuario

- Canal principal de conversación con Rocky. Mensajes cortos, una idea por mensaje.
- Sin tablas markdown; usa listas.
- **NO usar para:** volcar informes largos ni contenido sensible de correo. Un titular y el enlace, no el cuerpo entero.

### Google Docs → documentos estructurados que deben conservarse

- Planes semanales, informes, documentación que Rubén va a releer o compartir.
- Recuerda: vive en `carerrulu@gmail.com`, distinta de la cuenta de calendario.
- **NO usar para:** apuntes efímeros ni para algo que cabe en un mensaje.

### Google Drive → almacenamiento y localización de archivos

- Buscar y organizar archivos, obtener enlaces compartibles.
- **NO usar para:** crear contenido (usa Docs/Sheets) ni como base de datos.

### Notion → información estructurada y conocimiento persistente

- Notas de proyecto, bases de conocimiento, seguimiento a largo plazo.
- Cuenta distinta (`riux@hotmail.es`): no asumas que ve nada de Google.
- **NO usar para:** tareas del día a día (Tasks) ni para planificación horaria (Calendar).

### Google Sheets → datos tabulares

- Registros, series numéricas, cualquier cosa que se agregue fila a fila.
- **NO usar para:** prosa, ni como sustituto de una base de datos real.

## Prioridades cuando se solapan

1. ¿Necesita **tiempo reservado**? → Calendar.
2. ¿Es algo **que hacer**, sin hora fija? → Tasks.
3. ¿Es **conocimiento** que debe durar? → Notion (o Docs si es un documento con formato).
4. ¿Son **filas de datos**? → Sheets.
5. ¿Hay que **avisar a Rubén**? → Telegram.
6. ¿Hay que **hablar con otra persona**? → Gmail, y solo con permiso.

## Herramientas locales

- `openclaw doctor` — diagnóstico de la instalación.
- `openclaw skills list` / `openclaw skills check` / `openclaw skills info <name>` — descubrimiento y validación de skills.
- Skills propias del workspace: `skills/<nombre>/SKILL.md` (se descubren automáticamente desde `/root/.openclaw/workspace/skills`).
- El workspace es un repo git (`openclaw-connection`). **Commits locales sí; `git push` nunca sin pedirlo.**

---

Add whatever helps you do your job. This is your cheat sheet.

## Related

- [Agent workspace](/concepts/agent-workspace)
- [USER.md](USER.md) · [AGENTS.md](AGENTS.md) · [SKILLS_DESIGN.md](SKILLS_DESIGN.md)
