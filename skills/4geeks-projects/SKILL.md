---
name: 4geeks-projects
description: "Recupera la lista completa de proyectos/asignaciones del estudiante en 4Geeks/BreatheCode con su estado (pendiente, entregado, calificado)."
user-invocable: true
metadata:
  {
    "openclaw":
      {
        "emoji": "📋",
        "requires": { "bins": ["curl"], "env": ["BREATHECODE_STUDENT_TOKEN"] },
        "primaryEnv": "BREATHECODE_STUDENT_TOKEN",
      },
  }
---

# 4Geeks — Mis proyectos

Lista todas las tareas/asignaciones (lecciones, quizzes, ejercicios y proyectos) del estudiante en BreatheCode, con su estado. Se activa con peticiones tipo "¿qué proyectos tengo en 4Geeks?", "lista mis asignaciones del bootcamp", "¿cómo va mi entrega del módulo X?".

Antes de usarla, si no hay confirmación reciente de que el token funciona, ejecuta primero `4geeks-auth`.

## Seguridad

Igual que `4geeks-auth`: `BREATHECODE_STUDENT_TOKEN` nunca se imprime, ni se cita, ni sale de la llamada `curl`. No vuelques el JSON crudo completo en el chat — resume.

## Endpoint

| Campo          | Valor                                                |
| -------------- | ----------------------------------------------------- |
| Base URL       | `https://breathecode.herokuapp.com`                    |
| Método + ruta  | `GET /v1/assignment/user/me/task`                       |
| Auth           | Header `Authorization: Token <BREATHECODE_STUDENT_TOKEN>` |
| Fuente         | Verificado contra `breathecode/assignments/urls.py` (patrón `"user/me/task"`, nombre `user_me_task`) y `breathecode/assignments/models.py` (modelo `Task`) del repo oficial `breatheco-de/apiv2`. |

### Campos relevantes del modelo `Task` (verificados en `models.py`)

| Campo             | Valores posibles                                   |
| ------------------ | ---------------------------------------------------- |
| `task_type`        | `PROJECT`, `QUIZ`, `LESSON`, `EXERCISE`                |
| `task_status`       | `PENDING`, `DONE`                                     |
| `revision_status`   | `PENDING`, `APPROVED`, `REJECTED`, `IGNORED`            |
| `title`, `description`, `cohort`, `created_at`, `updated_at` | texto / referencia / fecha        |

No asumas más campos que los que realmente vengan en la respuesta (`id`, slugs, etc. pueden variar). Si necesitas un campo no listado aquí, léelo directamente del JSON de respuesta antes de usarlo — no lo inventes.

## Workflow

### 1. Llamar al endpoint (lista completa, sin filtrar)

```bash
http_code=$(curl -s -o /tmp/4geeks_tasks.json -w "%{http_code}" \
  -H "Authorization: Token $BREATHECODE_STUDENT_TOKEN" \
  https://breathecode.herokuapp.com/v1/assignment/user/me/task)
echo "HTTP $http_code"
```

### 2. Interpretar

| HTTP | Significado | Acción |
| ---- | ------------ | ------ |
| `200` con array | OK | Continúa al paso 3. |
| `200` con array vacío `[]` | Sin tareas asignadas todavía | Dilo tal cual: "BreatheCode no devuelve ninguna tarea para tu usuario". No es un error. |
| `401`/`403` | Token inválido/caducado | Repórtalo y sugiere ejecutar `4geeks-auth`. No sigas. |
| otro | Error de API/red | Reporta el HTTP/error literal de `curl`. No simules una lista. |

### 3. Agrupar y presentar

Agrupa por `task_type` (proyectos, quizzes, lecciones, ejercicios). Para cada tarea, traduce el estado a lenguaje llano:

- `task_status=PENDING` → **pendiente**
- `task_status=DONE` + `revision_status=PENDING` → **entregado, en revisión**
- `task_status=DONE` + `revision_status=APPROVED` → **entregado y calificado (aprobado)**
- `task_status=DONE` + `revision_status=REJECTED` → **entregado y calificado (rechazado, requiere corrección)**
- `revision_status=IGNORED` → **entregado, sin revisión prevista**

### 4. Responder al usuario

Formato corto, por tipo:

```text
Proyectos (N):
- <title>: <estado en llano>
...

Quizzes (N):
- ...

Lecciones (N):
- ...

Ejercicios (N):
- ...
```

Si una categoría está vacía, omítela en vez de mostrarla con "0".

## Errores conocidos

- Cuerpo `200` no-JSON o inesperado → no lo proceses a ciegas; muestra el HTTP y di que el formato no es el esperado.
- Diferencia con `4geeks-pending`/`4geeks-progress`: esta skill usa el mismo endpoint sin filtrar; las otras dos lo filtran o lo agregan para responder una pregunta distinta. No mezcles su lógica aquí.
