# Bitácora

## Paso 1 — Esqueleto + modo simulado + pantalla (incluye cimientos de SQLite y seguridad)

**Qué se pidió:** Armar el esqueleto de la app (FastAPI + una sola página HTML + JavaScript simple), el modo simulado sin `GEMINI_API_KEY` y la pantalla con un botón "copiar" por mensaje.

**Qué hizo el agente:** Creó los archivos `requirements.txt`, `.env.example`, `.gitignore`, `models.py` (Pydantic: socio, mensaje, petición y respuesta), `db.py` (SQLite: tabla, guardar y historial), `gemini.py` (modo simulado con 3 tonos, prompt con etiquetas que separan instrucciones de datos, reintento una vez, limpieza de bloques markdown y timeout), `main.py` (rutas `GET /` y `POST /generar`, errores sin detalles internos, validación 400 genérica), y `static/index.html` + `static/app.js` (envío de lista, renderizado como `textContent` para evitar XSS, botón copiar al portapapeles).

Se verificó: `GET /` → 200; `POST` con 2 socios → 3 mensajes cada uno (amable/directo/motivacional); 31 socios → 400 (límite); línea inválida / nombre largo / días negativos → 400; registros guardados en SQLite.

**Qué corregí yo:** Corregí la ruta del script en `static/index.html` de `app.js` a `static/app.js` para que el navegador cargue el archivo JavaScript y el botón "Generar mensajes" funcione.

## Paso 2 — Correcciones y SQLite (historial)

**Qué se pidió:** Reemplazar `@app.on_event("startup")` por un gestor `lifespan`, separar el CSS de `index.html` en su propio archivo, y completar el paso 2 de SQLite con un endpoint de consulta de historial.

**Qué hizo el agente:** Creó `static/style.css` con todos los estilos; quitó el bloque `<style>` de `static/index.html` y lo reemplazó por `<link rel="stylesheet" href="/static/style.css">`; reemplazó `@app.on_event("startup")` en `main.py` por un gestor `lifespan` mediante `@asynccontextmanager` que llama a `db.init_db()` al arranque.

**Qué corregí yo:** 