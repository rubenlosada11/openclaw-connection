---
name: 4geeks-certificates
description: "Consulta los certificados que el estudiante ha obtenido en 4Geeks/BreatheCode y su estado."
user-invocable: true
metadata:
  {
    "openclaw":
      {
        "emoji": "🎓",
        "requires": { "bins": ["curl"], "env": ["BREATHECODE_STUDENT_TOKEN"] },
        "primaryEnv": "BREATHECODE_STUDENT_TOKEN",
      },
  }
---

# 4Geeks — Mis certificados

Skill adicional (no obligatoria). Lista los certificados emitidos a nombre del estudiante: especialidad, academia, estado de emisión y fecha. Se activa con peticiones tipo "¿qué certificados tengo en 4Geeks?", "¿ya tengo el certificado de X módulo?", "lista mis certificados del bootcamp".

Antes de usarla, si no hay confirmación reciente de que el token funciona, ejecuta primero `4geeks-auth`.

## Por qué esta skill y no `4geeks-activity`

Se evaluó primero `GET /v1/activity/me` (registro de actividad reciente) como segunda skill adicional. **Probado en real contra la API, devuelve `403`**: `"You (user: <id>) don't have this capability: read_activity for academy <id>"` — ese endpoint exige una capacidad de staff de academia (`read_activity`) que un rol `STUDENT` no tiene, así que no es viable como skill para un estudiante por mucho que la URL sugiera "me". Se sustituyó por `GET /v1/certificate/me`, **probado en real y funcionando** (`200`, datos reales) sin ninguna capacidad especial más allá de estar autenticado. Queda documentado como problema real encontrado en `SKILL_LOG.md`, no descartado en silencio.

Criterio de selección: utilidad real (saber si ya tienes un certificado importa para el seguimiento del curso), endpoint disponible y accesible con un token de estudiante normal, responsabilidad única, resultado verificable (el certificado existe o no existe, con su estado).

## Seguridad

Igual que `4geeks-auth`: `BREATHECODE_STUDENT_TOKEN` nunca se imprime ni se cita.

## Endpoint

| Campo          | Valor                                                |
| -------------- | ----------------------------------------------------- |
| Base URL       | `https://breathecode.herokuapp.com`                    |
| Método + ruta  | `GET /v1/certificate/me`                                |
| Auth           | Header `Authorization: Token <BREATHECODE_STUDENT_TOKEN>` |
| Fuente         | Verificado contra `breathecode/certificate/urls.py` del repo oficial `breatheco-de/apiv2` (patrón `"me"`, nombre `me`, vista `CertificateMeView`). Probado en real: `200`, campos confirmados abajo. |

### Campos confirmados en una respuesta real (no inventados)

Cada certificado devuelve, entre otros: `id`, `status` (visto en pruebas: `PERSISTED`), `status_text`, `signed_by`, `signed_by_role`, `specialty` (objeto con `name`, `slug`, `duration_in_hours`, `syllabus`), `academy` (objeto con `name`, `slug`), `issued_at`, `expires_at`, `preview_url`.

## Workflow

### 1. Llamar al endpoint

```bash
http_code=$(curl -s -o /tmp/4geeks_certs.json -w "%{http_code}" \
  -H "Authorization: Token $BREATHECODE_STUDENT_TOKEN" \
  https://breathecode.herokuapp.com/v1/certificate/me)
echo "HTTP $http_code"
```

### 2. Interpretar

| HTTP | Significado | Acción |
| ---- | ------------ | ------ |
| `200` con array vacío | Sin certificados emitidos todavía | Dilo tal cual, no es un error. |
| `200` con array no vacío | Hay certificados | Continúa al paso 3. |
| `401`/`403` | Token inválido/caducado | Repórtalo, sugiere `4geeks-auth`. |
| otro | Error de API/red | Reporta el HTTP/error literal. |

### 3. Presentar

Un certificado por línea, con lo esencial:

```text
Certificados (N):
- <specialty.name> — <status_text> — emitido <issued_at> (<academy.name>)
...
```

Si `status` no es `PERSISTED` (por ejemplo, en cola o con error), dilo explícitamente en vez de darlo por completado.

## Errores conocidos

- No confundas `status` del certificado con `task_status`/`revision_status` de `4geeks-projects` — son conceptos distintos de dos apps distintas de la API; no los mezcles en la misma frase sin aclarar a cuál te refieres.
