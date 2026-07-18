# Flujo de Automatización en n8n - SIGPDA

Este documento describe el flujo de trabajo en n8n que SIGPDA invoca a través
de webhooks para enviar alertas y reportes.

---

## Arquitectura general

```
SIGPDA (Streamlit) ──HTTP POST JSON──► n8n Webhook
                                          │
                                          ▼
                                     Switch (tipo)
                                          │
        ┌─────────────────┬───────────────┼───────────────┬─────────────────┐
        ▼                 ▼               ▼               ▼                 ▼
   alerta_vencim.   alerta_desperd.  alerta_sobreprod.  reporte_diario   reporte_semanal
        │                 │               │               │                 │
        ▼                 ▼               ▼               ▼                 ▼
     Email            Email +        Email gerente     Email          Email + Excel
                     WhatsApp                          administrador   adjunto
```

---

## Paso 1 - Crear el Webhook

1. Abrir n8n (por defecto en `http://localhost:5678`).
2. Crear un nuevo workflow llamado **"SIGPDA - Alertas y reportes"**.
3. Agregar el nodo **Webhook**:
   - HTTP Method: `POST`
   - Path: `sigpda`
   - Response Mode: `Last Node`
   - Response Code: `200`
4. Copiar la URL generada (por ejemplo `http://localhost:5678/webhook/sigpda`)
   y configurarla en el archivo `.env` del sistema:
   ```env
   N8N_WEBHOOK_URL=http://localhost:5678/webhook/sigpda
   N8N_HABILITADO=true
   ```

---

## Paso 2 - Nodo Switch por tipo de evento

Agregar un nodo **Switch** después del Webhook, ruteando por el campo
`{{$json.tipo}}` con las salidas:

| Salida | Valor del campo `tipo`     |
|--------|----------------------------|
| 0      | `alerta_vencimiento`       |
| 1      | `alerta_desperdicio`       |
| 2      | `alerta_sobreproduccion`   |
| 3      | `reporte_diario`           |
| 4      | `reporte_semanal`          |
| 5      | `ping` (prueba conexión)   |

---

## Paso 3 - Salidas

### 3.1 Alerta de vencimiento de insumos
- Nodo **Send Email** o **Gmail**:
  - Para: `gerencia@restaurante.com`
  - Asunto: `[SIGPDA] Insumos por vencer / con bajo stock`
  - Cuerpo: HTML con la lista de insumos del payload `{{$json.insumos}}`.
- (Opcional) Nodo **WhatsApp Business Cloud** o **Telegram** con el mensaje.

### 3.2 Alerta de desperdicio crítico
- Nodo **Send Email** prioridad alta:
  - Asunto: `[SIGPDA] ALERTA: Desperdicio en {{$json.porcentaje_desperdicio}}%`
  - Cuerpo: incluir umbral, totales y costo en `{{$json.moneda}}`.
- Nodo **Twilio / WhatsApp** con texto corto.

### 3.3 Alerta de sobreproducción
- Nodo **Send Email** al gerente del restaurante:
  - Asunto: `[SIGPDA] Riesgo de sobreproducción - {{$json.plato}}`
  - Cuerpo: tabla HTML con `{{$json.predicciones}}`.

### 3.4 Reporte diario / semanal
- Nodo **Function** (JavaScript) para formatear el resumen como tabla HTML.
- Nodo **Send Email** al administrador con el HTML como cuerpo y el JSON
  adjunto como `reporte.json`.
- (Opcional) Nodo **Google Sheets** para anexar la fila al historial.

### 3.5 Ping (prueba de conexión)
- Nodo **Set** que devuelve `{ "ok": true, "fecha": "{{$now}}" }`.

---

## Ejemplos de Payload JSON

### Alerta de vencimiento
```json
{
  "tipo": "alerta_vencimiento",
  "sistema": "SIGPDA",
  "fecha": "2026-04-29T14:30:00",
  "severidad": "advertencia",
  "insumos_vencidos": 2,
  "insumos_por_vencer": 5,
  "stock_bajo": 3,
  "detalle": [
    {"nombre": "Tomate", "vence": "2026-05-02", "stock": 4.5},
    {"nombre": "Pollo", "vence": "2026-04-30", "stock": 2.0}
  ]
}
```

### Alerta de desperdicio
```json
{
  "tipo": "alerta_desperdicio",
  "sistema": "SIGPDA",
  "fecha": "2026-04-29T18:00:00",
  "severidad": "critica",
  "porcentaje_desperdicio": 21.45,
  "umbral_permitido": 15,
  "total_desperdicio_costo": 245.80,
  "total_ventas": 1145.50,
  "moneda": "S/",
  "mensaje": "El desperdicio alcanzó 21.45% superando el umbral permitido de 15%."
}
```

### Alerta de sobreproducción
```json
{
  "tipo": "alerta_sobreproduccion",
  "sistema": "SIGPDA",
  "fecha": "2026-04-29T09:00:00",
  "severidad": "advertencia",
  "plato": "Cabrito a la Norteña",
  "predicciones": [
    {"fecha": "2026-04-30", "demanda": 12, "recomendacion": 13, "riesgo": "alto"},
    {"fecha": "2026-05-01", "demanda": 9, "recomendacion": 10, "riesgo": "medio"}
  ],
  "mensaje": "Riesgo de sobreproducción detectado para el plato 'Cabrito a la Norteña'."
}
```

### Reporte diario
```json
{
  "tipo": "reporte_diario",
  "sistema": "SIGPDA",
  "fecha": "2026-04-29T20:00:00",
  "severidad": "info",
  "resumen": {
    "ventas_total": 1450.00,
    "platos_vendidos": 87,
    "desperdicio_total": 12.5,
    "porcentaje_desperdicio": 8.6,
    "top_plato": "Arroz con Pato"
  }
}
```

---

## Paso 4 - Activar el workflow

1. Pulsar **Activate** en la esquina superior derecha del editor de n8n.
2. Probar la conexión desde el módulo de Configuración del SIGPDA con el botón
   "Probar conexión n8n".
3. Verificar la entrega de correos / mensajes.

---

## Paso 5 - Recomendaciones de seguridad

- Usar `n8n` detrás de un proxy con HTTPS en producción.
- Restringir el webhook con autenticación básica o header secreto y agregar
  el mismo header en `webhook_n8n.py`.
- Encriptar credenciales SMTP / Twilio / etc. usando los Secrets de n8n.

---

## Paso 6 - Importar el workflow de ejemplo

Si lo prefiere, puede importar la siguiente plantilla mínima en
**n8n → Workflows → Import from File**:

```json
{
  "name": "SIGPDA - Alertas y reportes",
  "nodes": [
    {
      "parameters": {"httpMethod": "POST", "path": "sigpda", "responseMode": "lastNode"},
      "name": "Webhook",
      "type": "n8n-nodes-base.webhook",
      "position": [240, 300],
      "typeVersion": 1
    },
    {
      "parameters": {"dataType": "string", "value1": "={{$json.tipo}}",
                     "rules": {"rules": [
                       {"value2": "alerta_vencimiento"},
                       {"value2": "alerta_desperdicio"},
                       {"value2": "alerta_sobreproduccion"},
                       {"value2": "reporte_diario"},
                       {"value2": "reporte_semanal"}
                     ]}},
      "name": "Switch",
      "type": "n8n-nodes-base.switch",
      "position": [480, 300],
      "typeVersion": 1
    }
  ],
  "connections": {"Webhook": {"main": [[{"node": "Switch", "type": "main", "index": 0}]]}}
}
```
