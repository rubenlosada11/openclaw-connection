---
name: 4geeks-auth
description: "Verifica que el token de estudiante de 4Geeks/BreatheCode existe, es válido y que la API responde correctamente."
user-invocable: true
metadata:
  {
    "openclaw":
      {
        "emoji": "🔐",
        "requires": { "bins": ["curl"], "env": ["BREATHECODE_STUDENT_TOKEN"] },
        "primaryEnv": "BREATHECODE_STUDENT_TOKEN",
      },
  }
---

# 4Geeks — Autenticar

Comprueba la credencial de estudiante de BreatheCode/4Geeks antes de que cualquier otra skill `4geeks-*` la use. Se activa con peticiones tipo "¿está bien configurado mi token de 4Geeks?", "comprueba mi conexión con BreatheCode", "verifica mi cuenta de 4Geeks".

## Seguridad — leer antes de nada

- El token vive **solo** en la variable de entorno `BREATHECODE_STUDENT_TOKEN`, inyectada por OpenClaw a este proceso a través del `SecretRef` configurado en `skills.entries.4geeks-auth.apiKey` (ver `TOOLS.md`).
- **Nunca** imprimas, cites, ni incluyas el valor de `BREATHECODE_STUDENT_TOKEN` en la respuesta al usuario, en logs, ni en ningún archivo. Ni entero ni parcial.
- No uses `curl -v` ni `-i` de forma que el header `Authorization` pueda acabar en la salida que se muestra al usuario. Usa siempre `-s` (silent) y captura solo el código HTTP y el cuerpo de respuesta.
- Si `BREATHECODE_STUDENT_TOKEN` no existe, dilo tal cual ("token no configurado") y para. No inventes un resultado.

## Endpoint

| Campo          | Valor                                                |
| -------------- | ----------------------------------------------------- |
| Base URL       | `https://breathecode.herokuapp.com`                    |
| Método + ruta  | `GET /v1/auth/user/me`                                 |
| Auth           | Header `Authorization: Token <BREATHECODE_STUDENT_TOKEN>` |
| Fuente         | Verificado contra `breathecode/authenticate/urls/v1.py` del repo oficial `breatheco-de/apiv2` (patrón `"user/me"`, nombre `user_me`). |

`/v1/auth/user/me` devuelve el perfil del usuario autenticado por el token — es a la vez la comprobación de validez y la confirmación de identidad, en una sola llamada.

## Workflow

### 1. Comprobar que la variable existe

```bash
if [ -z "$BREATHECODE_STUDENT_TOKEN" ]; then
  echo "4Geeks token configurado: NO"
  exit 1
fi
echo "4Geeks token configurado: SÍ"
```

### 2. Llamar al endpoint

```bash
http_code=$(curl -s -o /tmp/4geeks_me.json -w "%{http_code}" \
  -H "Authorization: Token $BREATHECODE_STUDENT_TOKEN" \
  https://breathecode.herokuapp.com/v1/auth/user/me)
echo "HTTP $http_code"
```

No uses `-v`; el código HTTP y el cuerpo en `/tmp/4geeks_me.json` son suficientes.

### 3. Interpretar el resultado

| HTTP        | Significado                              | Qué decir                                                         |
| ----------- | ----------------------------------------- | ------------------------------------------------------------------ |
| `200`       | Token válido, API responde                 | Lee `first_name`, `last_name`, `email` de `/tmp/4geeks_me.json` y confírmalo. |
| `401`/`403`  | Token ausente, caducado o inválido         | Dilo literalmente: "el token no autentica (HTTP 401/403)". No reintentes con otro valor. |
| `404`       | Ruta incorrecta o API cambiada             | Reporta el HTTP y para; no asumas causa sin comprobarlo.            |
| timeout / sin respuesta | Problema de red o servicio caído | Reporta el error literal de `curl` (código de salida, mensaje).    |
| otro (`5xx`) | Fallo del lado de BreatheCode              | Reporta el HTTP y el cuerpo (sin datos sensibles) y para.           |

Borra `/tmp/4geeks_me.json` al terminar si contiene datos personales que ya no hacen falta.

### 4. Responder al usuario

Formato corto:

```text
4Geeks token configurado: SÍ
Autenticación: OK (HTTP 200)
Usuario: <first_name> <last_name> <email>
```

O, si falla:

```text
4Geeks token configurado: SÍ
Autenticación: FALLO (HTTP 401) — el token no es válido o ha caducado.
```

## Errores conocidos

- `Environment variable "BREATHECODE_STUDENT_TOKEN" is missing or empty` (visible en `openclaw secrets audit`) → el archivo de entorno del servicio no está cargado o el token no se ha escrito todavía. No es un fallo de la skill: repórtalo y espera a que se configure.
- Un `200` con cuerpo vacío o inesperado → no lo trates como éxito silencioso; muestra qué llegó realmente (sin exponer nada sensible de terceros) y dilo.
