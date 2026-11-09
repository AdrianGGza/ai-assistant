# Bitácora

## Paso 1 — Esqueleto + modo simulado + pantalla (incluye cimientos de SQLite y seguridad)

**Qué se pidió:** Armar el esqueleto de la app (FastAPI + una sola página HTML + JavaScript simple), el modo simulado sin `GEMINI_API_KEY` y la pantalla con un botón "copiar" por mensaje.

**Qué hizo el agente:** Creó los archivos `requirements.txt`, `.env.example`, `.gitignore`, `models.py` (Pydantic: socio, mensaje, petición y respuesta), `db.py` (SQLite: tabla, guardar y historial), `gemini.py` (modo simulado con 3 tonos, prompt con etiquetas que separan instrucciones de datos, reintento una vez, limpieza de bloques markdown y timeout), `main.py` (rutas `GET /` y `POST /generar`, errores sin detalles internos, validación 400 genérica), y `static/index.html` + `static/app.js` (envío de lista, renderizado como `textContent` para evitar XSS, botón copiar al portapapeles).

Se verificó: `GET /` → 200; `POST` con 2 socios → 3 mensajes cada uno (amable/directo/motivacional); 31 socios → 400 (límite); línea inválida / nombre largo / días negativos → 400; registros guardados en SQLite.

**Qué corregí yo:** 
