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

## Paso 3b — Corrección de agrupación del historial (ROW_NUMBER + clave de socio)

**Qué se pidió:** Corregir `agruparHistorialPorSocio` para que use el mensaje más reciente por tono (sin recalcular en JS), que socios con mismo nombre pero distinto plan queden en tarjetas separadas, y que el campo `id` venga de la base de datos.

**Qué hizo el agente:** Modificó `db.obtener_historial` para incluir `id` en el SELECT y usar `ROW_NUMBER() OVER (PARTITION BY LOWER(nombre), plan, tono ORDER BY fecha_creacion DESC, id DESC) AS rn` con `WHERE rn = 1`, ordenando por `dias_vencidos {direccion}, LOWER(nombre), plan, tono`. Modificó `main.py` para incluir `id` en el JSON de respuesta de `/historial`. Simplificó `agruparHistorialPorSocio` en `static/app.js` para usar como clave `${fila.nombre.toLowerCase()}|${fila.plan}|${fila.dias_vencidos}` sin verificar duplicados ni recalcular fechas.

**Qué corregí yo:** Prueba mínima: (a) SQL con dos generaciones del mismo tono devuelve solo la más reciente. (b) Dos socios con mismo nombre y planes distintos quedan en tarjetas separadas. Ambas verificadas con BD temporal (no la del proyecto) y borrada al terminar.

## Paso 3 — Ajustes de diseño (doble columna + filtros)

**Qué se pidió:** Acomodar las tarjetas de mensajes por usuario en dos columnas (layout horizontal) y agregar funciones de filtro junto al botón "Generar mensajes".

**Qué hizo el agente:** Modificó `static/style.css` para usar CSS Grid con dos columnas (`.resultados-grid`) y responsive a una columna en pantallas < 600px; modificó `static/index.html` para agregar controles de filtro (input nombre, select orden, botón "Aplicar filtro") junto al botón "Generar mensajes"; modificó `static/app.js` para agregar `btnFiltrar` event listener, función `agruparHistorialPorSocio()` que agrupa filas planas del historial por socio, y consume `GET /historial` con parámetros de filtro.

**Qué corregí yo:** 

## Paso 4 — Botón "Enviar" por mensaje con estado verde

**Qué se pidió:** Cada mensaje debe tener un botón "Enviar" que, al presionarlo, marque el mensaje como enviado en la BD, cambie el borde a verde, muestre "Mensaje enviado" y mantenga el mensaje en pantalla (no eliminarlo). Quitar el filtro por nombre del historial.

**Qué hizo el agente:**
- `db.py`: Agregó columna `enviado INTEGER DEFAULT 0` a la tabla (con ALTER TABLE para tablas existentes), función `marcar_enviado(id)`, e incluyó `enviado` en el SELECT de `obtener_historial`.
- `main.py`: Agregó endpoint `PATCH /historial/{mensaje_id}/enviado` y incluyó `"enviado": bool(r[7])` en el JSON de respuesta de `/historial`.
- `static/style.css`: Agregó clases `.mensaje.enviado` (borde verde #2ecc71), `.estado-enviado` (texto verde centrado inferior) y `.btn-enviar` (botón en parte inferior central).
- `static/index.html`: Quitó el input "Filtrar por nombre"; mantuvo solo el select de orden y el botón "Aplicar orden".
- `static/app.js`: Agregó `id` y `enviado` a cada mensaje en `agruparHistorialPorSocio`; en `renderizar`, agregó botón "Enviar" por mensaje en posición inferior central; al hacer clic envía `PATCH /historial/{id}/enviado`, cambia el botón a "Mensaje enviado", deshabilita el botón, agrega texto "Mensaje enviado" y aplica clase `.enviado` al contenedor.

**Qué corregí yo:** 

## Paso 5 — Mejoras de diseño responsivo y visualización de mensajes enviados

**Qué se pidió:** (1) Mostrar todos los mensajes independientemente del orden y del estado enviado, indicando cuáles ya fueron enviados. (2) Mejorar la responsividad y el espaciamiento de botones para que no se empalmen con los textos. (3) Crear una interfaz más amigable.

**Qué hizo el agente:**
- `db.py`: Confirmó que `obtener_historial` no filtra por `enviado`, devuelve todos los registros con el campo `enviado` incluido.
- `static/style.css`: Rediseñó completamente el CSS con mejor espaciado, contenedor `.botones-mensaje` para separar botones de textos, clase `.texto-mensaje` para el cuerpo del mensaje, mejoras de tipografía, bordes más suaves, y media queries para pantallas pequeñas (≤600px) y medianas (601-900px).
- `static/app.js`: Reestructuró `renderizar` para envolver botones "Copiar" y "Enviar" en `.botones-mensaje`, usar `.texto-mensaje` para el cuerpo, y mostrar el estado "Mensaje enviado" después de los botones (no antes). Todos los mensajes se muestran siempre, con indicador visual verde para los enviados.

**Qué corregí yo:** 

## Paso 6 — Grid responsivo 3/2/1 columnas y consistencia de mensajes

**Qué se pidió:** (1) Mostrar exactamente los mismos mensajes con su estado (enviado/no enviado) independientemente del orden ascendente o descendente. (2) Grid responsivo: 3 columnas en laptop/PC (≥900px), 2 columnas en tablets (600-899px), 1 columna en móviles (<600px). (3) Usar estándares de dimensiones de pantalla.

**Qué hizo el agente:**
- `static/style.css`: Cambió `max-width` de 900px a 1200px; cambió el grid por defecto a 3 columnas (`repeat(3, 1fr)`); reemplazó las media queries por: móvil (<600px) = 1 columna, tablet (600-899px) = 2 columnas, desktop (≥900px) = 3 columnas; ajustó gaps y min-height según el breakpoint.
- `static/app.js`: Verificó que `agruparHistorialPorSocio` y `renderizar` no filtran por `enviado`; todos los mensajes se muestran siempre con su estado respectivo, independientemente del orden de consulta.
- `db.py`: Confirmó que `obtener_historial` no filtra por `enviado`, devuelve todos los registros.

**Qué corregí yo:** 
