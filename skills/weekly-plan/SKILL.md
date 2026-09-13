---
name: weekly-plan
description: "Planificación semanal: prioriza los objetivos de Rubén, consulta la agenda real y reserva bloques de foco en Google Calendar sin pisar compromisos existentes."
user-invocable: true
metadata:
  {
    "openclaw":
      { "emoji": "🗓️", "requires": { "bins": ["mcporter"] } },
  }
---

# Weekly plan

objetivos + Calendar → planificación → Google Calendar. Se activa con "organiza mi semana", "planifica la semana con estas prioridades", "resérvame tiempo para X".

Lee `USER.md` (compromisos fijos, horas útiles), `TOOLS.md` (calendario por defecto y trampa de zona horaria) y `AGENTS.md` (qué eventos no se tocan) antes de empezar si no están ya en contexto.

## Límites

- **Crear** bloques nuevos: libre, es reversible.
- **Mover, modificar o borrar** un evento existente: pregunta siempre antes. Sin excepciones.
- Nunca planifiques encima de las **clases AI Engineering 4Geeks (L/X/V 18:30–21:30)**.
- No supongas que un hueco está libre: consúltalo con `find_events` antes de escribir.
- Si los objetivos no caben en la semana, dilo. No los comprimas hasta que "quepan".

## Zona horaria — leer antes de escribir nada

El servidor corre en **UTC**; Rubén vive en **Europe/Madrid**. Pasa siempre las fechas con **offset explícito**:

- `2026-09-03T10:00:00+02:00` ✅
- `2026-09-03T10:00:00` ❌ → la API lo toma como UTC y el bloque aparece desplazado.

CEST (`+02:00`) hasta el **25 de octubre de 2026**; CET (`+01:00`) después.

## Workflow

Todos los comandos se lanzan **desde `/root/.openclaw/workspace`** (ahí vive `config/mcporter.json`). Desde otro directorio, añade `--config /root/.openclaw/workspace/config/mcporter.json` o fallará con `Unknown MCP server 'zapier'`.

### 1. Resolver esquemas

```bash
mcporter call zapier.inspect_zapier_actions tool_name=google_calendar_find_events --output json
mcporter call zapier.inspect_zapier_actions tool_name=google_calendar_create_detailed_event --output json
```

### 2. Leer la agenda real de la semana

⚠️ **Los parámetros están invertidos respecto a lo intuitivo**: `start_time` es "empieza antes de" (límite superior) y `end_time` es "termina después de" (límite inferior, por defecto `now`). Para "próximos 7 días" va `start_time="+7 days"` y `end_time="now"` — al revés es una trampa fácil y devuelve siempre vacío.

```bash
mcporter call zapier.execute_zapier_read_action \
  selected_api=GoogleCalendarCLIAPI action=event_v2 tool_name=google_calendar_find_events \
  --args '{"params":{"calendarid":"rubeneai11@gmail.com","start_time":"+7 days","end_time":"now","ordering":"startTime","expand_recurring":"true"}}' \
  --output json
```

Anota cada evento existente con su inicio y fin en hora de Madrid. Ese es el mapa de lo ocupado; todo lo demás es candidato.

Los calendarios `Festivos en España` / `Holidays in Spain` son de solo lectura: consúltalos si la semana tiene festivo, pero no escribas en ellos.

### 3. Priorizar los objetivos

Ordena lo que ha pedido Rubén por:

1. **Fecha límite real** — lo que vence esta semana va primero.
2. **Peso en sus proyectos** (`USER.md`: bootcamp y prácticas por delante del resto).
3. **Coste de aplazarlo.**

Estima horas por objetivo. Si Rubén ya las dio ("estudiar 4 horas"), respétalas. Si no, propón una cifra y dila explícitamente como estimación tuya.

### 4. Encajar los bloques

Reglas:

- Bloques de **60–120 minutos**. Nada más corto (no cunde) ni más largo (no se sostiene).
- **≥ 15 minutos** de margen entre un bloque y el evento contiguo.
- Nada antes de las **08:00** ni después de las **22:30**.
- Máximo **~4 horas** de foco al día.
- Reparte cada objetivo en varios días en vez de amontonarlo en uno.
- Días de clase (L/X/V): la tarde a partir de las 18:00 está fuera de juego.

Si no cabe todo, recorta por el final de la lista de prioridades y **enumera lo que se quedó fuera**.

### 5. Crear los bloques

Uno por sesión, en el calendario `rubeneai11@gmail.com`:

```bash
mcporter call zapier.execute_zapier_write_action \
  selected_api=GoogleCalendarCLIAPI action=detailed_event tool_name=google_calendar_create_detailed_event \
  --args '{"params":{
    "calendarid":"rubeneai11@gmail.com",
    "summary":"[Foco] Práctica OpenClaw",
    "description":"Bloque de trabajo planificado por Rocky.\nObjetivo: avanzar la práctica de skills de OpenClaw.",
    "start__dateTime":"2026-09-03T10:00:00+02:00",
    "end__dateTime":"2026-09-03T12:00:00+02:00",
    "transparency":"opaque"
  }}' --output json
```

Convenciones:

- **`summary`**: `[Foco] <objetivo>` — el prefijo permite distinguir de un vistazo lo que creó Rocky.
- **`description`**: quién lo creó y a qué objetivo responde.
- No añadas `attendees`. Invitar a alguien es una comunicación externa y requiere permiso.

### 6. Verificar

Repite el paso 2 sobre la ventana planificada y comprueba:

1. Los bloques nuevos aparecen **con la hora local correcta** (si ves un desfase de 2 horas, el offset iba mal: bórralos y rehazlos).
2. Los eventos que ya estaban siguen intactos.
3. No hay dos eventos solapados.

Un `success` de la escritura no basta.

### 7. Entregar el plan

En el chat, estructurado y breve:

```text
Plan semanal — <rango de fechas>

Prioridades:
1. <objetivo> — Xh
2. ...

Bloques reservados:
- Lun 3, 10:00–12:00 — [Foco] <objetivo>
- ...

No ha cabido:
- <objetivo> — <motivo>
```

Solo si Rubén lo pide, guarda además el plan en Google Docs (`GoogleDocsV2CLIAPI`). Ojo: vive en otra cuenta (`carerrulu@gmail.com`), no en la del calendario.

## Errores conocidos

- `insufficient tasks on account` → cuota de Zapier agotada. Dilo tal cual y para; no simules haber creado eventos.
- Evento con 2 horas de desfase → faltaba el offset en `start__dateTime`/`end__dateTime`.
- `Missing argument values for required properties` → resuelve el esquema con `inspect_zapier_actions` y repite.
