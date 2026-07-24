# Despliegue de SIGPDA (100% gratuito)

Arquitectura: **Neon** (Postgres) + **Render** (backend FastAPI) + **Vercel** (frontend React).
Sigue el orden exacto — cada paso depende del anterior.

## 1. Base de datos — Neon

1. Crea una cuenta en https://neon.tech (gratis, sin tarjeta).
2. Crea un proyecto nuevo → copia el **Connection string** (botón "Connect"). Se ve así:
   ```
   postgresql://usuario:password@ep-xxxx.us-east-2.aws.neon.tech/neondb?sslmode=require
   ```
3. Guárdalo, lo necesitas en el paso 2.

## 2. Backend — Render

1. Crea una cuenta en https://render.com con tu GitHub (gratis, sin tarjeta).
2. **New → Blueprint** → selecciona el repositorio de SIGPDA. Render detecta `render.yaml` automáticamente y prepara el servicio `sigpda-backend`.
3. Antes de confirmar el deploy, completa las variables marcadas como manuales (`sync: false` en `render.yaml`):
   - `DATABASE_URL` → pega el connection string de Neon del paso 1.
   - `GEMINI_API_KEY` → tu clave de https://aistudio.google.com/apikey.
   - `CORS_ORIGENES_EXTRA` → déjalo vacío por ahora, lo completas en el paso 4.
4. Deploy. Cuando termine, copia la URL pública, ej: `https://sigpda-backend.onrender.com`.
5. Verifica que responde: abre `https://sigpda-backend.onrender.com/api/health` — debe mostrar `{"status":"ok",...}`.

**Nota:** el plan gratuito de Render "duerme" el servicio tras 15 min sin tráfico. La primera petición después de estar dormido tarda ~30-50s en responder (arranque en frío) — normal, no es un error.

### 2.1 Cargar datos de demo en Neon

Con el backend ya desplegado (lo que crea las tablas automáticamente al iniciar), carga usuarios y datos de prueba corriendo el script de inicialización **desde tu máquina, apuntando a Neon**:

```bash
# En la raíz del proyecto, con el venv activado
DATABASE_URL="postgresql://usuario:password@ep-xxxx...neon.tech/neondb?sslmode=require" TIPO_BD=postgresql python -m scripts.inicializar_bd
```

(En PowerShell: `$env:DATABASE_URL="..."; $env:TIPO_BD="postgresql"; python -m scripts.inicializar_bd`)

Esto crea roles, usuarios de prueba (`admin/admin123`, `gerente/gerente123`, `trabajador/trabajador123`, `analista/analista123`), restaurantes, platos, insumos, recetas y 90 días de ventas históricas para que la IA tenga datos con que entrenar.

## 3. Frontend — Vercel

1. Edita `frontend/vercel.json` en tu repo: reemplaza `REEMPLAZAR-CON-TU-BACKEND.onrender.com` con la URL real de Render del paso 2 (sin `https://` duplicado, mantén el formato del archivo). Haz commit y push.
2. Crea una cuenta en https://vercel.com con tu GitHub (gratis, sin tarjeta).
3. **Add New → Project** → importa el repositorio de SIGPDA.
4. En la configuración del proyecto:
   - **Root Directory** → `frontend` (importante, el proyecto está en un subdirectorio).
   - Framework Preset → Vercel debería detectar "Vite" automáticamente.
5. Deploy. Al terminar obtienes una URL, ej: `https://sigpda.vercel.app`.

## 4. Conectar CORS (último paso)

1. Vuelve a Render → tu servicio → **Environment** → edita `CORS_ORIGENES_EXTRA` con la URL de Vercel del paso 3 (ej. `https://sigpda.vercel.app`). Guarda — Render redesplegará automáticamente.
2. Abre tu URL de Vercel y prueba iniciar sesión con `admin` / `admin123`.

## Notas

- **Prophet en el build de Render**: si el build falla o tarda mucho por la compilación de `prophet`/`cmdstan`, avísame — se puede resolver ajustando el build o usando una imagen Docker con cmdstan precompilado.
- **Secretos**: nunca se suben a GitHub — `SECRET_KEY` la genera Render automáticamente, `DATABASE_URL` y `GEMINI_API_KEY` se pegan manualmente en el dashboard.
- **Actualizar el despliegue**: cada `git push` a la rama principal redespliega automáticamente tanto Render como Vercel.
