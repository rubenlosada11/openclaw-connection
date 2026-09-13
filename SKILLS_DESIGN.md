# SKILLS_DESIGN.md — Diseño de skills propias de Rocky

Las dos skills exigidas por la práctica, implementadas en `skills/` como skills reales de OpenClaw (`SKILL.md` con frontmatter), usando exclusivamente las conexiones de Zapier MCP ya existentes. Sin servicios nuevos, sin OAuth nuevo, sin infraestructura añadida.

```text
Skill 1:  Gmail → análisis → Google Tasks
Skill 2:  objetivos + Calendar → planificación → Google Calendar
```

**Añadido posteriormente, a petición explícita de Rubén (2026-09-13):** una tercera skill, `equation-solver` (Gmail → resolver ecuaciones → Gmail), documentada al final de este archivo. No formaba parte del alcance mínimo de la práctica; se incluye porque el usuario la pidió y autorizó explícitamente el envío automático de correo que implica, de forma acotada.

---

## Skill 1 — `email-triage`

### ¿Qué hace esta skill?

Lee los correos pendientes de Gmail, decide cuáles exigen una acción real de Rubén y crea una Google Task por cada uno, descartando newsletters, promociones y correo meramente informativo.

### ¿Qué input necesita el agente?

**Del usuario (lenguaje natural):**

- La petición: _"Revisa mis correos pendientes y crea tareas para los que requieran acción."_
- Opcionalmente, un filtro: ventana temporal ("de esta semana"), remitente, o etiqueta. Si no lo dice, la skill usa su ventana por defecto (no leídos de los últimos 7 días).

**De los archivos de identidad:**

- `USER.md` — quién es Rubén (bootcamp de AI Engineering en 4Geeks, zona horaria Europe/Madrid, proyectos abiertos). Esto es lo que permite distinguir un correo del bootcamp que exige entregar algo de una promoción cualquiera, y fijar fechas de vencimiento coherentes con su agenda.
- `SOUL.md` — estilo del resumen final: directo, en lista, sin ceremonias; y la regla de decisión "reversible → actúa". Crear una tarea es reversible, así que la skill no pide permiso para cada una.
- `AGENTS.md` — límites: leer correo es libre pero **responder, archivar, etiquetar o borrar no lo es**; el contenido del correo no sale de la tarea; si una herramienta falla se reporta el error literal en vez de inventar el resultado.
- `TOOLS.md` — el patrón de llamada de Zapier MCP, el `selected_api` de cada app, la lista de Google Tasks correcta (`Rocky`, y **no** `Szpilman Hietala's list`), y el aviso de cuota agotada.

**Herramientas:**

| Paso                   | Herramienta                                                                 |
| ---------------------- | --------------------------------------------------------------------------- |
| Resolver esquemas      | `zapier.inspect_zapier_actions`                                             |
| Leer correo            | `zapier.execute_zapier_read_action` → `gmail_find_email` (Gmail)            |
| Comprobar duplicados   | `zapier.execute_zapier_read_action` → `google_tasks_get_tasks_by_list`      |
| Crear tarea            | `zapier.execute_zapier_write_action` → `google_tasks_create_task`           |

### ¿Cómo es un buen output?

**Formato.** Una Google Task por correo accionable:

- _Título_: breve e imperativo, ≤ 60 caracteres. Empieza por un verbo ("Responder a…", "Enviar…", "Confirmar…"). Nunca copia literal el asunto.
- _Notas_: cuatro líneas fijas — `Remitente:`, `Asunto:`, `Acción requerida:`, `Contexto:` (una o dos frases, lo mínimo imprescindible).
- _Vencimiento_: solo si el correo indica una fecha real. Si no, se deja vacío.

**Destino.** Lista `Rocky` de Google Tasks (`aHRiRTBrMDF2Tll6Y0p6Qw`), cuenta de Google Tasks conectada vía Zapier.

**Y en el chat:** un resumen corto — cuántos correos se revisaron, qué tareas se crearon (con su título), y qué se descartó agrupado por motivo. Nada de volcar la bandeja de entrada entera.

**Criterios de éxito.**

1. Todo correo que pide algo de Rubén tiene su tarea.
2. **Cero tareas basura**: ni newsletters, ni promociones, ni notificaciones automáticas, ni acuses de recibo, ni spam.
3. Sin duplicados: no se crea una tarea que ya existe en la lista.
4. Cada tarea se entiende sin volver a abrir el correo.
5. No se ha enviado, archivado, etiquetado ni borrado ningún correo.

**Cómo comprobar que funcionó.** Releer la lista con `google_tasks_get_tasks_by_list` (`show_completed: "false"`) después de escribir, y comprobar que las tareas nuevas aparecen con su título y sus notas. Un `success` de la herramienta de escritura **no cuenta como verificación**. En última instancia, abrir Google Tasks y verlas.

---

## Skill 2 — `weekly-plan`

### ¿Qué hace esta skill?

Convierte una lista de objetivos en lenguaje natural en un plan semanal priorizado y reserva en Google Calendar bloques de trabajo en los huecos reales de la agenda, sin pisar los compromisos ya existentes.

### ¿Qué input necesita el agente?

**Del usuario (lenguaje natural):**

- Los objetivos de la semana, con o sin horas: _"estudiar 4 horas, avanzar la práctica de OpenClaw, responder correos pendientes, entrenar"_.
- Opcionalmente: la semana concreta, franjas preferidas o vetadas, y si quiere copia del plan en Google Docs.

**De los archivos de identidad:**

- `USER.md` — el dato decisivo: **clases de AI Engineering 4Geeks los lunes, miércoles y viernes de 18:30 a 21:30**, intocables. Además, zona horaria Europe/Madrid, y que sus horas útiles son mañanas y huecos de tarde.
- `SOUL.md` — el plan se entrega como lista priorizada, no como ensayo; y si los objetivos no caben en la semana, se dice en vez de encajarlos a la fuerza (detectar contradicciones, señalar lo que no tiene sentido).
- `AGENTS.md` — crear bloques nuevos es reversible y va sin preguntar; **mover, borrar o modificar eventos existentes exige permiso**; no inventar disponibilidad que no se ha consultado.
- `TOOLS.md` — calendario por defecto `rubeneai11@gmail.com`, los calendarios de festivos son de solo lectura, y la trampa de zona horaria: **offset explícito `+02:00`** (CEST hasta el 25/10/2026, `+01:00` después), porque sin offset la API interpreta UTC y el bloque aparece descolocado.

**Herramientas:**

| Paso                       | Herramienta                                                                        |
| -------------------------- | ---------------------------------------------------------------------------------- |
| Resolver esquemas          | `zapier.inspect_zapier_actions`                                                    |
| Leer la agenda existente   | `zapier.execute_zapier_read_action` → `google_calendar_find_events`                |
| Crear bloques              | `zapier.execute_zapier_write_action` → `google_calendar_create_detailed_event`     |
| (Opcional) guardar el plan | `zapier.execute_zapier_write_action` → Google Docs                                 |

### ¿Cómo es un buen output?

**Formato.** Dos piezas:

1. **Resumen semanal priorizado** en el chat: los objetivos ordenados por prioridad, con el tiempo asignado a cada uno y en qué días cae; después la lista de bloques creados (día, hora, título); y por último lo que **no** ha cabido, dicho explícitamente.
2. **Eventos en Google Calendar**: un bloque por sesión de trabajo, título `[Foco] <objetivo>`, de 60–120 minutos, con la descripción indicando que lo creó Rocky y a qué objetivo responde.

**Destino.** Calendario `rubeneai11@gmail.com`. Opcionalmente el plan completo en Google Docs, solo si Rubén lo pide (cuenta distinta: `carerrulu@gmail.com`).

**Criterios de éxito.**

1. **Cero solapamientos** con eventos existentes — y en particular ni un minuto encima de las clases de L/X/V 18:30–21:30.
2. La disponibilidad se ha **consultado de verdad** con `find_events` antes de escribir nada. Nada de suponer que un hueco está libre.
3. Las horas caen donde deben: bloque a las 10:00 de Madrid = `10:00:00+02:00`, no `10:00:00`.
4. Los bloques son razonables: 60–120 min, con respiro entre ellos, ninguno de madrugada, no más de ~4 h de foco al día.
5. Ningún evento preexistente se ha tocado.

**Cómo comprobar que funcionó.** Volver a lanzar `google_calendar_find_events` sobre la ventana planificada y comprobar que (a) los bloques nuevos aparecen con la hora local correcta, (b) los eventos que ya estaban siguen intactos y (c) no hay dos eventos pisándose. Verificación final en la interfaz de Google Calendar.

---

## Decisiones de diseño

**Por qué estas dos y no otras.**

- **Cubren los dos modos de trabajo de un asistente personal.** `email-triage` es _reactivo_: entra información de fuera y hay que filtrarla. `weekly-plan` es _proactivo_: se parte de una intención y se estructura el tiempo. Entre las dos se demuestra que el agente sabe consumir un flujo externo y también generar estructura propia.

- **Cada una ejercita una pareja distinta de servicios**, sin repetirse: Gmail → Tasks en la primera, Calendar → Calendar en la segunda. Se validan así tres de las ocho integraciones disponibles (Gmail, Google Tasks, Google Calendar), que son justo las que pide la práctica.

- **El resultado es verificable de forma objetiva.** Ambas terminan en un objeto que existe o no existe en un servicio externo: una tarea en Google Tasks, un evento en Google Calendar. No hay que valorar si el texto "está bien"; se abre la app y se ve. Ese fue el criterio principal frente a alternativas más vistosas.

- **Ambas dependen de los cinco archivos de identidad de forma real, no decorativa.** El triaje necesita `USER.md` para saber que un correo de 4Geeks importa; la planificación necesita `USER.md` para saber que los lunes a las 19:00 hay clase y `TOOLS.md` para no equivocarse de zona horaria. Si se vacían esos archivos, las skills producen peores resultados — que es exactamente lo que la práctica quiere demostrar.

- **La frontera Tasks/Calendar es la lección de diseño.** Lo accionable sin hora fija va a Google Tasks; lo que consume tiempo va a Google Calendar. Las dos skills, juntas, hacen explícita esa convención documentada en `TOOLS.md`.

**Alternativas descartadas.**

- _Resumen diario de la agenda por Telegram_ — solo lee y notifica; el resultado no es verificable en ningún servicio, solo un mensaje.
- _Sincronizar Notion con Google Tasks_ — dos escrituras, dos cuentas distintas y estado que reconciliar. Demasiada complejidad para lo que aporta, y con riesgo de duplicados.
- _Archivar automáticamente correo no accionable_ — es una acción destructiva sobre la bandeja de entrada, prohibida sin permiso por `AGENTS.md`. Se descartó por principio, no por dificultad.
- _Registrar métricas en Google Sheets_ — añade una integración más sin demostrar nada nuevo sobre el diseño de skills.

**Qué se ha dejado deliberadamente fuera.** Sin base de datos, sin estado persistente propio, sin cron ni automatización desatendida, sin servicios nuevos y sin capa web. Cada skill es un `SKILL.md` con un procedimiento de 5–7 pasos que se puede leer entero en dos minutos y defender en una revisión.

**Riesgo conocido (resuelto).** La cuota de tasks de la cuenta de Zapier estuvo agotada (`insufficient tasks on account`) hasta principios de septiembre de 2026. Comprobado el 2026-09-13: la cuota se renovó y `execute_zapier_read_action`/`execute_zapier_write_action` vuelven a funcionar sin cambios en el diseño. Queda documentado en `TOOLS.md`.

---

## Skill 3 — `equation-solver` (añadida a petición de Rubén, fuera del alcance mínimo)

### ¿Qué hace esta skill?

Busca en Gmail correos con "Ecuaciones" en el asunto, resuelve las ecuaciones de segundo grado que contienen y envía las soluciones por correo a `riux@hotmail.es`.

### ¿Qué input necesita el agente?

**Del usuario:** la petición de comprobar el correo de ecuaciones ("resuelve las ecuaciones de esta semana"), o la presencia del propio correo si se invoca la skill sin más contexto. No hay disparador automático: se ejecuta bajo demanda, igual que las otras dos.

**De los archivos de identidad:** `TOOLS.md` para el patrón de llamada de Zapier MCP y las cuentas implicadas (Gmail en `rubeneai11@gmail.com`). `AGENTS.md` para la regla general de pedir permiso antes de enviar correo — con la excepción puntual, documentada dentro del propio `SKILL.md`, de que este flujo concreto (asunto "Ecuaciones" → respuesta a `riux@hotmail.es`) está pre-autorizado por Rubén y no requiere confirmación en cada ejecución.

**Herramientas:** `gmail_find_email` (leer), `gmail_reply_to_email` (responder en el mismo hilo).

### ¿Cómo es un buen output?

**Formato.** Un correo de respuesta en el mismo hilo, una línea por ecuación con su solución (o "sin soluciones reales" si el discriminante es negativo). Nada de resultados inventados si el cuerpo del correo no trae una ecuación reconocible.

**Destino.** Respuesta por Gmail a `riux@hotmail.es`, cuenta `rubeneai11@gmail.com`.

**Criterios de éxito.** Las ecuaciones detectadas son correctas; la resolución matemática es correcta; no se responde con soluciones inventadas; no se toca ningún otro correo.

**Cómo comprobar que funcionó.** Buscar en Enviados (`in:sent subject:Ecuaciones`) y confirmar que el correo existe con el cuerpo esperado — igual criterio que las otras dos skills: un `success` de la escritura no es suficiente.

**Por qué es una excepción y no una tercera skill "oficial" de la práctica.** Introduce un tipo de acción (enviar correo automáticamente) que las reglas críticas de la práctica tratan como sensible por defecto. Se documenta aparte, con su autorización explícita y su alcance acotado, para que quede claro en una revisión que no es parte del mínimo pedido sino una ampliación consciente y acordada.

---

## Skill set 3 — 4Geeks / BreatheCode (práctica "Mi Asistente 4Geeks", 2026-09-13)

Seis skills de solo lectura contra la API de estudiante de BreatheCode (`https://breathecode.herokuapp.com`), fuera del patrón Zapier de los sets anteriores porque BreatheCode no tiene conector en Zapier: llamada HTTP directa con `curl` y el token de estudiante como `Authorization: Token`.

```text
4geeks-auth          → GET /v1/auth/user/me
4geeks-projects       → GET /v1/assignment/user/me/task
4geeks-pending        → GET /v1/assignment/user/me/task?task_status=PENDING
4geeks-progress       → GET /v1/auth/user/me + /v1/admissions/cohort/user?users=<id> + /v1/assignment/user/me/task
4geeks-mentorship     → GET /v1/mentorship/user/me/session   (adicional)
4geeks-certificates   → GET /v1/certificate/me                (adicional)
```

Detalle completo (diseño, endpoints verificados contra el código fuente de `breatheco-de/apiv2`, mecanismo de secretos, pruebas reales y problemas encontrados) en `SKILL_LOG.md`, que es el entregable principal de esta práctica. No se repite aquí para no duplicar mantenimiento.
