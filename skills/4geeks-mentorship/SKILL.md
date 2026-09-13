---
name: 4geeks-mentorship
description: "Consulta las sesiones de mentoría (pasadas y próximas) del estudiante en 4Geeks/BreatheCode."
user-invocable: true
metadata:
  {
    "openclaw":
      {
        "emoji": "🧑‍🏫",
        "requires": { "bins": ["curl"], "env": ["BREATHECODE_STUDENT_TOKEN"] },
        "primaryEnv": "BREATHECODE_STUDENT_TOKEN",
      },
  }
---

# 4Geeks — Sesiones de mentoría

Skill adicional (no obligatoria). Lista las sesiones de mentoría 1:1 del estudiante: agendadas, completadas o canceladas. Se activa con peticiones tipo "¿cuándo es mi próxima mentoría?", "¿he tenido sesiones de mentoría en 4Geeks?", "dime mis sesiones con mentores".

Antes de usarla, si no hay confirmación reciente de que el token funciona, ejecuta primero `4geeks-auth`.

## Por qué esta skill y no otra

De los endpoints disponibles en la API de BreatheCode, `user/me/session` de la app `mentorship` es el único que da al propio estudiante (no a un admin de academia) una lista verificable de su relación con mentores: complementa a las tareas (`4geeks-projects`/`4geeks-pending`, que son trabajo asíncrono) con la parte síncrona del bootcamp. Resultado fácil de comprobar: cada sesión existe o no existe, con una hora concreta.

## Seguridad

Igual que `4geeks-auth`: `BREATHECODE_STUDENT_TOKEN` nunca se imprime ni se cita.

## Endpoint

| Campo          | Valor                                                |
| -------------- | ----------------------------------------------------- |
| Base URL       | `https://breathecode.herokuapp.com`                    |
| Método + ruta  | `GET /v1/mentorship/user/me/session`                    |
| Auth           | Header `Authorization: Token <BREATHECODE_STUDENT_TOKEN>` |
| Fuente         | Verificado contra `breathecode/mentorship/urls.py` del repo oficial `breatheco-de/apiv2` (patrón `"user/me/session"`, nombre `user_session`). |

### Campos confirmados en una respuesta real (no inventados)

Probado en real (`200`): cada sesión trae, entre otros, `id`, `status` (valor visto en las sesiones reales de prueba: `FAILED`; otros valores posibles no verificados — trátalos tal cual lleguen, no asumas la lista completa), `status_message`, `mentor`, `mentee`, `started_at`, `ended_at`, `mentor_joined_at`, `mentee_joined`, `summary`, `rating`. `started_at` puede venir `null` si la sesión nunca llegó a empezar.

## Workflow

### 1. Llamar al endpoint

```bash
http_code=$(curl -s -o /tmp/4geeks_sessions.json -w "%{http_code}" \
  -H "Authorization: Token $BREATHECODE_STUDENT_TOKEN" \
  https://breathecode.herokuapp.com/v1/mentorship/user/me/session)
echo "HTTP $http_code"
```

### 2. Interpretar

| HTTP | Significado | Acción |
| ---- | ------------ | ------ |
| `200` con array vacío | Sin sesiones de mentoría registradas | Dilo tal cual, no es un error. |
| `200` con array no vacío | Hay sesiones | Continúa al paso 3. |
| `401`/`403` | Token inválido/caducado | Repórtalo, sugiere `4geeks-auth`. |
| otro | Error de API/red | Reporta el HTTP/error literal. |

### 3. Presentar

Antes de resumir, inspecciona una entrada del array para identificar qué campos trae realmente (por ejemplo un estado tipo `PENDING`/`STARTED`/`COMPLETED`/`CANCELED`, una fecha de inicio, el nombre del mentor). Separa en "próximas/agendadas" vs "pasadas" usando el campo de fecha/estado que la respuesta realmente tenga.

```text
Próximas sesiones de mentoría (N):
- <fecha/hora> con <mentor> — <estado>

Sesiones pasadas recientes (N):
- <fecha/hora> con <mentor> — <estado>
```

Si no hay forma de distinguir pasado/futuro con los campos disponibles, dilo y muestra la lista completa sin esa separación en vez de inventarla.

## Errores conocidos

- No fuerces ningún filtro de fecha vía query string sin haberlo comprobado antes contra la API real: documenta el resultado de la llamada sin parámetros primero.
