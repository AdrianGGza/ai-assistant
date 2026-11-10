# Bitácora

## Paso 1 — Esqueleto + modo simulado + pantalla (incluye cimientos de SQLite y seguridad)

**Qué se pidió:** Armar el esqueleto de la app (FastAPI + una sola página HTML + JavaScript simple), el modo simulado sin `GEMINI_API_KEY` y la pantalla con un botón "copiar" por mensaje.

**Qué hizo el agente:** Creó los archivos `requirements.txt`, `.env.example`, `.gitignore`, `models.py` (Pydantic: socio, mensaje, petición y respuesta), `db.py` (SQLite: tabla, guardar y historial), `gemini.py` (modo simulado con 3 tonos, prompt con etiquetas que separan instrucciones de datos, reintento una vez, limpieza de bloques markdown y timeout), `main.py` (rutas `GET /` y `POST /generar`, errores sin detalles internos, validación 400 genérica), y `static/index.html` + `static/app.js` (envío de lista, renderizado como `textContent` para evitar XSS, botón copiar al portapapeles).

Se verificó: `GET /` → 200; `POST` con 2 socios → 3 mensajes cada uno (amable/directo/motivacional); 31 socios → 400 (límite); línea inválida / nombre largo / días negativos → 400; registros guardados en SQLite.

**Qué corregí yo:** Corregí la ruta del script en `static/index.html` de `app.js` a `static/app.js` para que el navegador cargue el archivo JavaScript y el botón "Generar mensajes" funcione.

## Paso 2 — Correcciones y SQLite (historial)

**Qué se pidió:** Reemplazar `@app.on_event("startup")` por un gestor `lifespan`, separar el CSS de `index.html` en su propio archivo, y completar el paso 2 de SQLite con un endpoint de consulta de historial.

**Qué hizo el agente:** Creó `static/style.css` con todos los estilos; quitó el bloque `<style>` de `static/index.html` y lo reemplazó por `<link rel="stylesheet" href="/static/style.css">`; reemplazó `@app.on_event("startup")` en `main.py` por un gestor `lifespan` mediante `@asynccontextmanager` que llama a `db.init_db()` al arranque; modificó `db.obtener_historial` para aceptar `nombre`, `limite` y `orden`; agregó el endpoint `GET /historial` en `main.py`.

**Qué corregí yo:** Implementé el endpoint `GET /historial` en `main.py` con query params `nombre` (filtro insensible a mayúsculas/minúsculas), `limite` (1-100) y `orden` (`asc`/`desc` por días vencidos). Modifiqué `db.obtener_historial` para aceptar esos parámetros y aplicar `LOWER(nombre) = LOWER(?)` y `ORDER BY dias_vencidos ASC/DESC`. Se verificó: filtro por nombre funciona con mayúsculas y minúsculas; ordenamiento ASC y DESC funciona; orden inválido devuelve 400; límite excedido devuelve 400.

## Paso 2b — Silenciar health checks automáticos

**Qué se pidió:** Agregar endpoints `GET /health` y `GET /v1/models` que devuelvan código exitoso (200) para silenciar peticiones automáticas del cliente de `google-genai` y health checks externos, evitando 404 en la consola del servidor.

**Qué hizo el agente:** Agregó `GET /health` que devuelve `{"status": "ok"}` y `GET /v1/models` que devuelve `{}` (JSON vacío), ambos con HTTP 200.

**Qué corregí yo:** 

## Paso 3 — Ajustes de diseño (doble columna + filtros)

**Qué se pidió:** Acomodar las tarjetas de mensajes por usuario en dos columnas (layout horizontal) y agregar funciones de filtro junto al botón "Generar mensajes".

**Qué hizo el agente:** Modificó `static/style.css` para usar CSS Grid con dos columnas (`.resultados-grid`) y responsive a una columna en pantallas < 600px; modificó `static/index.html` para agregar controles de filtro (input nombre, select orden, botón "Aplicar filtro") junto al botón "Generar mensajes"; modificó `static/app.js` para agregar `btnFiltrar` event listener, función `agruparHistorialPorSocio()` que agrupa filas planas del historial por socio, y consume `GET /historial` con parámetros de filtro.

**Qué corregí yo:** 

