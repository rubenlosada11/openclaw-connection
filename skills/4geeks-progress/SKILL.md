---
name: 4geeks-progress
description: "Ofrece una visión general del progreso del estudiante en el bootcamp de 4Geeks: estado del cohort y estadísticas de tareas completadas/pendientes/calificadas."
user-invocable: true
metadata:
  {
    "openclaw":
      {
        "emoji": "📊",
        "requires": { "bins": ["curl"], "env": ["BREATHECODE_STUDENT_TOKEN"] },
        "primaryEnv": "BREATHECODE_STUDENT_TOKEN",
      },
  }
---

# 4Geeks — Resumen de progreso

Combina el estado del cohort con las estadísticas de tareas para dar una foto general de "cómo voy" en el bootcamp. Se activa con peticiones tipo "¿cómo voy en el bootcamp?", "resumen de mi progreso en 4Geeks", "¿en qué punto está mi cohort?".

Antes de usarla, si no hay confirmación reciente de que el token funciona, ejecuta primero `4geeks-auth`.

## Seguridad

Igual que `4geeks-auth`: `BREATHECODE_STUDENT_TOKEN` nunca se imprime ni se cita.

## Endpoints (tres llamadas, dos preguntas distintas)

Esta skill es la única excepción documentada a "un endpoint por skill": necesita **tres** llamadas de solo lectura porque "progreso" combina dos cosas que BreatheCode expone en dos recursos distintos (en qué cohort estás vs. qué tareas has hecho). Ninguna llamada escribe nada.

| # | Método + ruta | Para qué | Fuente verificada |
| - | -------------- | -------- | ------------------- |
| 1 | `GET /v1/auth/user/me` | Obtener tu propio `id` de usuario (necesario para el paso 2) | igual que `4geeks-auth` |
| 2 | `GET /v1/admissions/cohort/user?users=<tu_id>` | Cohort(s) del estudiante y su estado educativo | `breathecode/admissions/urls.py` (patrón `"cohort/user"`, nombre `cohort_user`); filtro `users` verificado en `CohortUserView` (`breathecode/admissions/views.py`) |
| 3 | `GET /v1/assignment/user/me/task` | Todas las tareas, para calcular estadísticas | igual que `4geeks-projects` |

Auth en las tres: header `Authorization: Token <BREATHECODE_STUDENT_TOKEN>`.

### ⚠️ Regla dura, verificada en producción: nunca llames a `cohort/user` sin `users=`

`GET /v1/admissions/cohort/user` **sin** el parámetro `users` no filtra por el usuario autenticado — devuelve una página de cohorts de cientos de estudiantes distintos (comprobado en pruebas reales: 1000 resultados, ninguno del usuario del token, 781 usuarios distintos). Es un endpoint de listado de academia, no un "mis cohorts". Llamarlo sin `users=<tu_id>` sería tanto un dato incorrecto como una fuga de datos personales de terceros (estado educativo y financiero de otros estudiantes). **Siempre** pásale `users=<id>` con el id obtenido en el paso 1. No proceses ni muestres el resultado si por error llega sin filtrar.

### Campos verificados en el código fuente (`breathecode/admissions/models.py`)

**`CohortUser`**: `role` (`STUDENT`, `TEACHER`, `ASSISTANT`, `REVIEWER`), `educational_status` (`ACTIVE`, `POSTPONED`, `GRADUATED`, `SUSPENDED`, `DROPPED`, `NOT_COMPLETING`), `finantial_status` (`FULLY_PAID`, `UP_TO_DATE`, `LATE`), `cohort` (objeto).

**`Cohort`**: `name`, `slug`, `stage` (`INACTIVE`, `PREWORK`, `STARTED`, `FINAL_PROJECT`, `ENDED`, `DELETED`), `kickoff_date`, `current_day`, `never_ends`.

No asumas otros campos (por ejemplo, un porcentaje numérico de progreso) salvo que aparezcan realmente en la respuesta — si aparecen, repórtalos tal cual; si no, no los inventes.

## Workflow

### 1. Tu propio id de usuario

```bash
curl -s -H "Authorization: Token $BREATHECODE_STUDENT_TOKEN" \
  https://breathecode.herokuapp.com/v1/auth/user/me | tee /tmp/4geeks_me.json | grep -o '"id":[0-9]*'
```

Guarda el `id` — lo necesitas en el paso siguiente. Si esta llamada falla, para aquí (ver `4geeks-auth`).

### 2. Cohort(s) del estudiante (filtrado por tu id, nunca sin filtrar)

```bash
my_id=$(python3 -c "import json;print(json.load(open('/tmp/4geeks_me.json'))['id'])")
http_code_cohort=$(curl -s -o /tmp/4geeks_cohort.json -w "%{http_code}" \
  -H "Authorization: Token $BREATHECODE_STUDENT_TOKEN" \
  "https://breathecode.herokuapp.com/v1/admissions/cohort/user?users=$my_id")
echo "HTTP cohort: $http_code_cohort"
```

Identifica el cohort "actual" como el que tenga `stage` distinto de `INACTIVE`/`ENDED`/`DELETED` (normalmente `STARTED`). Si hay más de uno en ese estado, muéstralos todos y dilo explícitamente; los demás (`INACTIVE`/`ENDED`) son cursos ya cerrados del programa modular — resúmelos aparte, no los mezcles con "el progreso actual".

### 3. Estadísticas de tareas

```bash
http_code_tasks=$(curl -s -o /tmp/4geeks_tasks_all.json -w "%{http_code}" \
  -H "Authorization: Token $BREATHECODE_STUDENT_TOKEN" \
  https://breathecode.herokuapp.com/v1/assignment/user/me/task)
echo "HTTP tasks: $http_code_tasks"
```

Calcula sobre el array completo:

- Total de tareas.
- `task_status=DONE` vs `PENDING` → % completado.
- Dentro de las `DONE`, `revision_status=APPROVED` vs `REJECTED` vs `PENDING` (en revisión) → % calificado y aprobado.
- Desglose por `task_type` si aporta claridad (p. ej. "3/5 proyectos entregados").

### 4. Interpretar errores

Si cualquiera de las llamadas falla (`401`/`403`/red/timeout), repórtalo tal cual **para esa llamada concreta** — no descartes toda la skill si solo una falla; di explícitamente qué parte del resumen no se pudo obtener y por qué.

### 5. Responder al usuario

```text
Cohort: <cohort.name> — etapa: <stage> (día <current_day>)
Tu estado: <educational_status> / pago: <finantial_status>

Tareas: <done>/<total> completadas (<pct>%)
De las completadas: <approved> aprobadas, <rejected> rechazadas, <in_review> en revisión

Por tipo:
- Proyectos: <done>/<total>
- Quizzes: <done>/<total>
- Lecciones: <done>/<total>
- Ejercicios: <done>/<total>
```

Si el estudiante tiene más de un cohort activo, repite el bloque de cohort por cada uno; las estadísticas de tareas son globales salvo que se pida filtrar por cohort (usa el parámetro `cohort` del endpoint de tareas, verificado en `TaskMeView`, si se pide explícitamente).

## Errores conocidos

- `cohort/user` devolviendo lista vacía → el estudiante no tiene ningún cohort asociado a ese token; dilo tal cual, no es un fallo de la skill.
- No inventes un "% de progreso" único si BreatheCode no lo da directamente: constrúyelo siempre a partir de los conteos reales de tareas, mostrando cómo se calculó.
