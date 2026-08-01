#!/usr/bin/env python3
import json, subprocess, sys

# Get stock data
result = subprocess.run(
    ["curl", "-s", "https://query1.finance.yahoo.com/v8/finance/chart/LOG.MC?interval=1d&range=5d",
     "-H", "User-Agent: Mozilla/5.0"],
    capture_output=True, text=True
)
data = json.loads(result.stdout)
r = data['chart']['result'][0]
meta = r['meta']
quotes = r['indicators']['quote'][0]

import datetime
prices = []
for i in range(len(r['timestamp'])):
    d = datetime.datetime.fromtimestamp(r['timestamp'][i]).strftime('%d/%m')
    c = round(quotes['close'][i], 2)
    prices.append(f'{d}: {c}€')

price = round(meta['regularMarketPrice'], 2)
prev_close = round(quotes['close'][-2], 2)
chg = round(price - prev_close, 2)
chg_pct = round((price - prev_close) / prev_close * 100, 2)

week_bullets = "\n".join([f'<p style="margin:0 0 2px 0;padding-left:12px;font-family:monospace;font-size:13px">• {p}</p>' for p in prices])

high = round(meta['regularMarketDayHigh'], 2)
low = round(meta['regularMarketDayLow'], 2)
w52h = round(meta['fiftyTwoWeekHigh'], 2)
w52l = round(meta['fiftyTwoWeekLow'], 2)

body_html = f'''<html><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0"></head><body style="font:16px -apple-system,Helvetica,Arial,sans-serif;color:#111;margin:0;padding:0"><p style="margin:0 0 20px 0">¡Muy buenas, Rubén! ¿Qué tal va ese día? 👋</p><p style="margin:0 0 2px 0;font-weight:bold">📈 LOGISTA INTEGRAL (LOG.MC)</p><p style="margin:0 0 2px 0;padding-left:12px;font-family:monospace;font-size:13px">• Precio: {price}€</p><p style="margin:0 0 2px 0;padding-left:12px;font-family:monospace;font-size:13px">• Variación diaria: {chg}€ ({chg_pct}%)</p><p style="margin:0 0 2px 0;padding-left:12px;font-family:monospace;font-size:13px">• Máximo hoy: {high}€</p><p style="margin:0 0 2px 0;padding-left:12px;font-family:monospace;font-size:13px">• Mínimo hoy: {low}€</p><p style="margin:0 0 2px 0;padding-left:12px;font-family:monospace;font-size:13px">• 52 sem máx: {w52h}€</p><p style="margin:0 0 12px 0;padding-left:12px;font-family:monospace;font-size:13px">• 52 sem mín: {w52l}€</p><p style="margin:0 0 2px 0;font-weight:bold">📆 Evolución semanal</p>{week_bullets}<p style="margin:0 0 14px 0;line-height:1.5;margin-top:14px">Evolución semanal de Logista. El precio ha cerrado a {price}€, con una variación de {chg}€ respecto a ayer. El rango semanal se mueve entre {low}€ y {high}€.</p><p style="margin:0 0 12px 0">¡A seguir dándole!</p><p style="margin:0;color:#888">🐕 Enviado por Rocky</p></body></html>'''

# Call Zapier MCP
cmd = [
    "mcporter", "call", "zapier.execute_zapier_write_action", "--args",
    json.dumps({
        "selected_api": "GoogleMailV2CLIAPI",
        "action": "message",
        "tool_name": "gmail_send_email",
        "instructions": "Enviar email diario precio Logista",
        "params": {
            "to": ["riux@hotmail.es", "rubenlosalo305@gmail.com"],
            "subject": "📈 Precio diario Logista | " + datetime.datetime.now().strftime('%d/%m/%Y'),
            "body": body_html,
            "body_type": "html"
        },
        "output": "Confirmación"
    }),
    "--output", "json"
]
result = subprocess.run(cmd, capture_output=True, text=True)
print(result.stdout[-500:] if len(result.stdout) > 500 else result.stdout)
if result.stderr:
    print("STDERR:", result.stderr[-300:])
print("DONE")