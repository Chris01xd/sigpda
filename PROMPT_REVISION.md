# PROMPT POSTERIOR DE REVISIÓN - SIGPDA

Este prompt se utiliza después de haber recibido el sistema SIGPDA completo,
para encargar a una IA (Claude / GPT / Gemini) una revisión exhaustiva y la
implementación de mejoras.

---

## Prompt completo (copiar y pegar)

```
Eres un revisor experto en sistemas web Python con experiencia en
Streamlit, SQLAlchemy, scikit-learn y arquitectura de software. Voy a
proporcionarte el código fuente completo del proyecto SIGPDA — un sistema
web inteligente de gestión y predicción de desperdicio alimentario para
PyMEs gastronómicas del Valle Jequetepeque (Perú), desarrollado como tesis
de Ingeniería de Sistemas.

Tu tarea consiste en realizar una REVISIÓN INTEGRAL en 5 fases.
Para cada fase, entrega los hallazgos en español, ordenados por gravedad
(crítico / alto / medio / bajo) y proponiendo cambios de código concretos
(con bloques diff o snippets completos por archivo).

---------- FASE 1 — Auditoría funcional ----------

Verifica que cada uno de los siguientes módulos cumpla con su propósito:

1.  Autenticación con bcrypt y registro de sesiones.
2.  Gestión de usuarios, roles y permisos (RBAC matricial).
3.  CRUD de restaurantes, platos, insumos y recetas.
4.  Costeo de platos a partir de receta + costo unitario de insumos.
5.  Registro y análisis de ventas con carrito multi-plato.
6.  Producción con cálculo de % eficiencia (preparada / vendida / sobrante).
7.  Desperdicio con motivo, costo estimado y umbral de alerta.
8.  Predicción IA (Random Forest / Lineal / Decision Tree) con MAE, R²,
    confianza y riesgo de desperdicio.
9.  Recomendaciones inteligentes (rotación, sobreproducción, vencimiento).
10. Dashboard BI con KPIs tipo semáforo.
11. Estadísticas descriptivas y comparativas entre restaurantes.
12. Reportes PDF (operacional, semanal, mensual, predicción, gestión,
    auditoría) y exportación a Excel/CSV.
13. Bitácora de eventos con filtros y exportación.
14. Configuración de parámetros (umbrales, moneda, n8n).
15. Webhook n8n para alertas (vencimiento, desperdicio, sobreproducción).
16. Inicialización de BD con datos de prueba (≥90 días históricos).

Para cada uno: indica si funciona, qué falta, qué edge cases no cubre y
proporciona el parche mínimo para arreglarlo.

---------- FASE 2 — Auditoría de seguridad ----------

Revisa específicamente:
- Hash bcrypt: factor de coste apropiado.
- Validación de entrada en todos los formularios (RUC, correo, teléfono,
  longitudes de strings, valores numéricos no negativos).
- Inyección SQL: uso correcto de SQLAlchemy ORM.
- Control de acceso: ¿se valida `usuario_tiene_permiso` en cada vista o
  solo se oculta el menú? Si solo se oculta, hay riesgo de IDOR.
- Manejo de la SECRET_KEY y .env.
- CSRF, sesiones expiradas, fuga de datos en la bitácora.
- Logs que puedan exponer contraseñas.

---------- FASE 3 — Auditoría de calidad de código ----------

- Convenciones PEP 8, type hints faltantes, imports redundantes.
- Funciones largas que deban descomponerse (>50 líneas).
- Acoplamiento: módulos que importan demasiado entre sí.
- Cobertura de excepciones: try/except demasiado amplios.
- Repetición de queries SQL — proponer servicios o repositorios.
- Manejo de transacciones en SQLAlchemy: commit/rollback correctos.
- ¿Faltan __init__.py o referencias circulares?

---------- FASE 4 — Auditoría del modelo IA ----------

- Validación cruzada (k-fold) además del simple train_test_split.
- Selección de features: ¿la variable `clima` es realmente útil siendo
  un valor aleatorio simulado?
- Sobreajuste: profundidades, número de árboles, regularización.
- Métricas: ¿solo MAE/R² o agregar MAPE, RMSE?
- Pipeline de inferencia: ¿el modelo entrenado se persiste con joblib o
  se reentrena cada vez?
- Cold start: comportamiento con platos sin histórico.
- Deriva: ¿se reentrenará periódicamente?
- Lista de mejoras concretas y código.

---------- FASE 5 — Mejoras operativas y de despliegue ----------

- Dockerfile y docker-compose: ¿pueden levantar el sistema desde cero
  con `docker compose up`? Probarlo mentalmente paso a paso.
- Volúmenes y persistencia.
- Healthchecks.
- Variables de entorno faltantes.
- Logs estructurados.
- README: ¿están todos los pasos para una persona que clona el repo
  por primera vez? Indica qué agregar.

---------- ENTREGABLES FINALES ----------

1. Tabla maestra de hallazgos: archivo, línea, severidad, descripción,
   corrección sugerida.
2. Pull request mental: por cada archivo modificado, el diff completo.
3. Lista priorizada de 10 mejoras de mayor impacto.
4. Diagrama actualizado de arquitectura si propones cambios estructurales.
5. Plan de pruebas: qué casos manuales y automatizados deberían existir
   (pytest sugerido) para validar los módulos críticos.

Responde en español, con tono técnico, sin omitir secciones. Si una
respuesta excede el contexto, indícalo y prioriza las observaciones de
severidad CRÍTICA y ALTA.
```

---

## Prompts secundarios (uso opcional)

### Para enriquecer el modelo IA
```
Toma el archivo `ia/predictor.py` del sistema SIGPDA y propón una
implementación que (a) reemplace el clima simulado por una llamada a la
API de Open-Meteo para Pacasmayo, (b) persista los modelos entrenados
con joblib en `ia/modelos/`, (c) agregue MAPE y RMSE a las métricas,
(d) implemente reentrenamiento incremental cada N días.
```

### Para generar pruebas unitarias
```
Genera pruebas pytest para los módulos `autenticacion.py`,
`config/settings.py:usuario_tiene_permiso`, `ia/predictor.py:calcular_riesgo_desperdicio`
y `reportes/exportador.py`. Usa SQLite en memoria para los fixtures de BD
y mockea Streamlit con `streamlit.testing.v1.AppTest`.
```

### Para mejorar UX
```
Revisa la usabilidad de los formularios Streamlit del sistema SIGPDA
(módulo de ventas, producción, desperdicio). Propón mejoras concretas
en términos de validación en tiempo real, mensajes de error, atajos de
teclado y feedback visual sin cambiar el stack.
```

### Para internacionalización
```
Diseña una estrategia para convertir el sistema SIGPDA en multi-idioma
(español por defecto, quechua e inglés como opciones), modificando el
mínimo de archivos posibles y manteniendo compatibilidad hacia atrás.
```
