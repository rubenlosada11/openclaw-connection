---
name: equation-solver
description: "Resuelve ecuaciones de segundo grado recibidas por correo con asunto \"Ecuaciones\" y envía las soluciones por email a riux@hotmail.es."
user-invocable: true
metadata:
  {
    "openclaw":
      { "emoji": "🧮", "requires": { "bins": ["mcporter"] } },
  }
---

# Equation solver

Gmail (asunto "Ecuaciones") → resolver → responder por Gmail. Se activa bajo demanda: "resuelve las ecuaciones de esta semana", "revisa si hay correo de ecuaciones", o cuando Rubén pide explícitamente comprobar este flujo. **No hay cron ni disparador automático** — se invoca cuando se pide, igual que las otras skills del workspace.

Lee `TOOLS.md` (patrón de llamada de Zapier MCP) antes de empezar si no está ya en contexto.

## Autorización de este flujo (excepción documentada)

Enviar correo es, por regla general, una acción sensible que exige pedir permiso cada vez (`AGENTS.md` → _Acciones sensibles_). **Excepción concreta, confirmada por Rubén el 2026-09-13**: responder automáticamente, sin pedir permiso adicional, a un correo cuyo asunto contenga "Ecuaciones", enviando la respuesta **únicamente** a `riux@hotmail.es` (o como respuesta al hilo, que ya va a ese remitente) con las soluciones calculadas. Esta excepción **no se extiende** a ningún otro asunto, destinatario o tipo de correo — cualquier otro envío sigue exigiendo permiso explícito.

## Límites

- Solo responde a correos cuyo asunto contenga la palabra "Ecuaciones". El remitente puede variar (no filtres por remitente).
- Solo resuelve **ecuaciones de segundo grado** (`ax² + bx + c = 0`). Si el correo trae otra cosa (ejercicios distintos, texto ambiguo), no inventes una ecuación: dilo en el resumen y no respondas con un resultado inventado.
- No reenvíes, archives, ni borres el correo original. Solo léelo y respóndelo.
- No inventes soluciones. Si el discriminante es negativo, dilo explícitamente ("sin soluciones reales"), no des raíces complejas salvo que se pidan.

## Workflow

Todos los comandos se lanzan **desde `/root/.openclaw/workspace`** (ahí vive `config/mcporter.json`).

### 1. Resolver esquemas

```bash
mcporter call zapier.inspect_zapier_actions tool_name=gmail_find_email --output json
mcporter call zapier.inspect_zapier_actions tool_name=gmail_reply_to_email --output json
```

### 2. Buscar el correo de ecuaciones

```bash
mcporter call zapier.execute_zapier_read_action \
  selected_api=GoogleMailV2CLIAPI action=message tool_name=gmail_find_email \
  --args '{"params":{"query":"subject:Ecuaciones newer_than:7d"}}' --output json
```

Si no hay resultados, dilo y para — no hay nada que resolver.

### 3. Extraer las ecuaciones del cuerpo (`body_plain`)

El formato puede venir sin notación de superíndice (p. ej. `X2−5x+6=0` en vez de `x²−5x+6=0`). Interpreta cualquier expresión del tipo `a·x² + b·x + c = 0` (con o sin coeficientes explícitos, con o sin espacios) como una ecuación a resolver. Una ecuación por línea, normalmente.

### 4. Resolver con la fórmula general

Para cada ecuación `ax² + bx + c = 0`:

- Discriminante `Δ = b² − 4ac`.
- Si `Δ > 0`: dos soluciones reales `x = (−b ± √Δ) / 2a`.
- Si `Δ = 0`: una solución doble `x = −b / 2a`.
- Si `Δ < 0`: sin soluciones reales — dilo así, no des un número inventado.

### 5. Responder por correo

Responde en el mismo hilo (`thread_id` del correo encontrado), dirigido a `riux@hotmail.es`, con una línea por ecuación:

```bash
mcporter call zapier.execute_zapier_write_action \
  selected_api=GoogleMailV2CLIAPI action=reply_to_message tool_name=gmail_reply_to_email \
  --args '{"params":{
    "thread_id":"<thread_id del paso 2>",
    "to":"riux@hotmail.es",
    "subject":"Re: Ecuaciones",
    "body":"Hola,\n\nSoluciones de las ecuaciones de segundo grado:\n\n1) <ecuación>  ->  x = ..., x = ...\n2) ...\n\n- Rocky",
    "body_type":"plain"
  }}' --output json
```

### 6. Verificar

Un `success` de la escritura no basta. Vuelve a buscar en Enviados:

```bash
mcporter call zapier.execute_zapier_read_action \
  selected_api=GoogleMailV2CLIAPI action=message tool_name=gmail_find_email \
  --args '{"params":{"query":"in:sent subject:Ecuaciones"}}' --output json
```

Confirma que el correo de respuesta existe con el cuerpo correcto.

### 7. Resumir en el chat

```text
Correo de ecuaciones: <asunto> de <remitente>
Ecuaciones resueltas: N
- <ecuación> -> x = ..., x = ...
Respuesta enviada a riux@hotmail.es ✅ (verificado en Enviados)
```

## Errores conocidos

- `insufficient tasks on account` → cuota de Zapier agotada. Dilo tal cual y para.
- Cuerpo del correo con formato inesperado (sin ecuaciones reconocibles) → no inventes una ecuación; pide aclaración o dilo en el resumen.
