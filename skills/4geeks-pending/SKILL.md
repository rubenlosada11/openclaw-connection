---
name: 4geeks-pending
description: "Identifica específicamente qué trabajo del bootcamp de 4Geeks/BreatheCode tiene el estudiante pendiente de completar."
user-invocable: true
metadata:
  {
    "openclaw":
      {
        "emoji": "⏳",
        "requires": { "bins": ["curl"], "env": ["BREATHECODE_STUDENT_TOKEN"] },
        "primaryEnv": "BREATHECODE_STUDENT_TOKEN",
      },
  }
---

# 4Geeks — Trabajo pendiente

Responde a una pregunta concreta: **¿qué me falta por entregar ahora mismo?** Se activa con peticiones tipo "¿qué tengo pendiente en el bootcamp?", "¿qué me falta por entregar?", "dime mis tareas sin hacer de 4Geeks".

Antes de usarla, si no hay confirmación reciente de que el token funciona, ejecuta primero `4geeks-auth`.

## Seguridad

Igual que `4geeks-auth`: `BREATHECODE_STUDENT_TOKEN` nunca se imprime ni se cita.

## Endpoint

| Campo          | Valor                                                |
| -------------- | ----------------------------------------------------- |
| Base URL       | `https://breathecode.herokuapp.com`                    |
| Método + ruta  | `GET /v1/assignment/user/me/task?task_status=PENDING`   |
| Auth           | Header `Authorization: Token <BREATHECODE_STUDENT_TOKEN>` |
| Fuente         | Mismo recurso que `4geeks-projects`. El filtro `task_status` está verificado en `TaskMeView` (`breathecode/assignments/views.py` del repo oficial): `items.filter(task_status__in=task_status.split(","))`. |

**Por qué el filtro va en el servidor y no en el cliente:** BreatheCode ya soporta `task_status` como query param documentado en su propio código; pedir solo lo pendiente es más simple y robusto que traer todo y filtrar a mano, y evita procesar datos que no hacen falta.

## Workflow

### 1. Llamar al endpoint filtrado

```bash
http_code=$(curl -s -o /tmp/4geeks_pending.json -w "%{http_code}" \
  -H "Authorization: Token $BREATHECODE_STUDENT_TOKEN" \
  "https://breathecode.herokuapp.com/v1/assignment/user/me/task?task_status=PENDING")
echo "HTTP $http_code"
```

### 2. Interpretar

| HTTP | Significado | Acción |
| ---- | ------------ | ------ |
| `200` con array vacío `[]` | **No hay nada pendiente** | Dilo así, en positivo: "no tienes tareas pendientes en BreatheCode ahora mismo". |
| `200` con array no vacío | Hay trabajo pendiente | Continúa al paso 3. |
| `401`/`403` | Token inválido/caducado | Repórtalo, sugiere `4geeks-auth`. No sigas. |
| otro | Error de API/red | Reporta el HTTP/error literal. No inventes una lista "por si acaso". |

### 3. Presentar

Agrupa por `task_type` (proyecto, quiz, lección, ejercicio) y ordena dentro de cada grupo por `updated_at` descendente si el campo está presente (lo más reciente primero, suele ser lo más urgente de retomar).

```text
Pendiente (N tareas):

Proyectos:
- <title>

Quizzes:
- <title>
...
```

No inventes fechas límite: esta versión del modelo `Task` no expone un campo de fecha de entrega verificado; si aparece uno en la respuesta real (por ejemplo algo que claramente sea una fecha de vencimiento), repórtalo tal cual llega, sin asumir su nombre de antemano.

## Errores conocidos

- Si `4geeks-projects` devuelve una tarea como pendiente pero esta skill no la lista (o viceversa), es una señal de que el filtro del servidor no se comporta como documentado: repórtalo literalmente, no elijas cuál de las dos "confiar" sin decirlo.
