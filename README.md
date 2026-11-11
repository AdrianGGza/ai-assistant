# Recordatorios de Renovación - Gimnasio

App para generar recordatorios de renovación de membresía de gimnasio por WhatsApp, utilizando IA (Gemini) para crear 3 versiones de mensaje por socio (tono amable, directo y motivacional).

---

## 1. ¿Qué problema elegiste y por qué?

El encargado de un gimnasio redacta a mano recordatorios de renovación para socios con membresía vencida (unos 10 por semana, aproximadamente 30 minutos por mensaje). Lo tedioso es personalizar cada mensaje según el nombre, los días vencidos y el plan.

Se eligió este problema porque:
- Es un proceso manual repetitivo que consume tiempo valioso del encargado.
- La personalización es sencilla (nombre, días vencidos, plan), lo que lo hace ideal para automatizar con IA.
- No requiere integración con sistemas externos complejos (no envía WhatsApp, no calcula vencimientos, no guarda teléfonos), por lo que el alcance es manejable para un ejercicio técnico.

---

## 2. ¿Qué le pediste a tu agente para que pudiera hacer la app?

Se le solicitó al agente construir una aplicación con las siguientes características:

**Requisitos funcionales:**
1. Que el encargado pueda pegar una lista de socios, uno por línea, con formato `nombre|días vencidos|plan`.
2. Para cada socio, la app llama a la API de Gemini y obtiene 3 versiones de mensaje de WhatsApp en español: tono amable, directo y motivacional.
3. Muestra los resultados en pantalla, con un botón "copiar" por mensaje.
4. Guarda lo generado en SQLite para consultarlo después.
5. Modo simulado: si no hay `GEMINI_API_KEY`, devuelve mensajes de ejemplo para que la app funcione sin llaves.

**Lo que NO debe hacer (no agregar):**
- No enviar mensajes ni integrarse con WhatsApp.
- No calcular vencimientos.
- No guardar teléfonos.
- Sin login, sin Docker, sin frameworks de frontend, sin dependencias fuera del stack.

**Stack definido:**
- Python, FastAPI, una sola página HTML con JavaScript simple, SQLite (módulo estándar), `google-genai`, Pydantic, `python-dotenv`.
- El nombre del modelo de Gemini debe leerse de una variable de entorno, sin dejarlo fijo.

**Prompt a Gemini:**
- Separar instrucciones de los datos del socio con etiquetas, indicando que lo dentro son datos, no instrucciones.
- Español de México, cordial, sin presión ni culpa, tipo mensaje de WhatsApp (máx. ~280 caracteres).
- Usar solo nombre, días vencidos y plan. No inventar promociones, montos, fechas ni horarios.
- Salida en JSON con exactamente 3 objetos `{tono, mensaje}`, validada con Pydantic. Si falla, reintenta una vez y si vuelve a fallar muestra un error claro.

**Seguridad:**
- La API key solo en `.env`; `.env` en `.gitignore`; incluir `.env.example`.
- Límites: máximo 30 socios por petición, largo máximo de campos, días como entero >= 0.
- Mostrar la salida del modelo como texto, nunca como HTML (evitar XSS).
- No registrar datos de socios en logs. Timeout en la llamada a Gemini. Errores sin detalles internos.

---

## 3. ¿Qué escribieron los agentes y qué corregiste tú?

### Qué escribió el agente (IA)

El agente creó la estructura completa de la aplicación:

**Archivos de backend:**
- `main.py`: FastAPI con rutas `GET /`, `POST /generar`, `GET /historial`, `GET /health`, `GET /v1/models`, `PATCH /historial/{id}/enviado`. Incluye manejo de errores sin detalles internos y validación 400 genérica.
- `models.py`: Esquemas Pydantic para socio, mensaje, petición y respuesta.
- `db.py`: SQLite con tabla `mensajes_generados`, funciones `init_db`, `guardar`, `obtener_historial` (con `ROW_NUMBER` para mensaje más reciente por socio+tono), `marcar_enviado`.
- `gemini.py`: Llamada a Gemini, modo simulado con 3 tonos, prompt con etiquetas que separan instrucciones de datos, reintento una vez, limpieza de bloques markdown, timeout de 30s.
- `requirements.txt`, `.env.example`, `.gitignore`.

**Archivos de frontend:**
- `static/index.html`: Página única con área de texto, botones y zona de resultados.
- `static/style.css`: Estilos con CSS Grid (3 columnas desktop, 2 tablet, 1 móvil), botones separados del texto, estado visual verde para mensajes enviados.
- `static/app.js`: JavaScript simple para enviar la lista, renderizar resultados como `textContent` (evita XSS), botón copiar, botón enviar por mensaje, filtro por orden.

**Bitácora:**
- `BITACORA.md`: Registro de cambios por paso.

### Qué corregiste tú (usuario)

A lo largo del desarrollo, realizaste las siguientes correcciones y ajustes:

1. **Ruta del script:** Corregiste la ruta de `app.js` en `index.html` para que cargue desde `/static/app.js` y el botón "Generar mensajes" funcione.
3. **CSS separado:** Separaste los estilos de `index.html` en `static/style.css`.
4. **Filtro por socio en historial:** Solicitaste que el historial permitiera filtrar por nombre de socio, insensible a mayúsculas/minúsculas, y ordenar por días vencidos (asc/desc).
5. **Silenciar health checks:** Agregaste endpoints `GET /health` y `GET /v1/models` que devuelven 200 para evitar 404 en la consola del servidor.
6. **Corrección de agrupación del historial:** Ajustaste que la clave de agrupación sea `nombre + plan + días vencidos` (insensible a mayúsculas), que se use `ROW_NUMBER()` en SQL para obtener solo el mensaje más reciente por tono, y que JavaScript no recalcule fechas ni elimine mensajes.
7. **Botón "Enviar" por mensaje:** Cambiaste el comportamiento para que al presionar "Enviar" se muestre "Mensaje enviado" con borde verde, en lugar de eliminar el resultado.
8. **Grid responsivo 3/2/1:** Solicitaste 3 columnas para laptop/PC, 2 para tablet y 1 para móvil, usando estándares de dimensiones de pantalla.
9. **Lectura perezosa de API key:** Corregiste que `GEMINI_API_KEY` se lea dentro de la función que llama a Gemini (no al importar el módulo), para que `load_dotenv()` funcione correctamente.
10. **Pruebas con pytest:** Instalaste `pytest` y definiste las 3 pruebas mínimas (modo simulado, validación de entrada, historial SQLite).

---

## 4. ¿Cómo mitigarías un riesgo de seguridad de la app?

### Riesgo: Exposición de la API key de Gemini

La API key de Gemini es un secreto crítico. Si se filtra, un tercero podría usarla para generar mensajes, consumir tu cuota de la API o incluso intentar acceder a otros recursos asociados a tu cuenta de Google Cloud.

### Medidas de mitigación implementadas:

1. **`.env` solo en entorno local:** La clave nunca se escribe en el código fuente. Se lee con `python-dotenv` desde un archivo `.env` que no se sube al repositorio.
2. **`.env` en `.gitignore`:** El archivo `.gitignore` incluye `.env` para evitar commits accidentales.
3. **`.env.example` incluido:** Se proporciona un archivo de ejemplo con variables sin valores reales, para que cualquier persona pueda configurar su propia clave sin exponer la tuya.
4. **Lectura perezosa de la clave:** En `gemini.py`, la API key se lee dentro de la función que llama a Gemini (`os.getenv("GEMINI_API_KEY")`), no como variable global al importar el módulo. Esto evita que la clave quede expuesta en memoria antes de que `load_dotenv()` haya cargado el archivo `.env`.
5. **Sin logs de datos sensibles:** La app no registra nombres de socios, días vencidos ni planes en los logs. Solo se registran conteos y errores genéricos.
6. **Errores sin detalles internos:** Cualquier falla en la llamada a Gemini devuelve al cliente un mensaje genérico ("Error al generar los mensajes") sin exponer stack traces ni detalles de la API.
7. **Validación de entrada estricta:** Pydantic valida que los días sean enteros >= 0, que el nombre y plan tengan largo máximo, y que no haya más de 30 socios por petición, evitando ataques por inyección o desbordamiento.

### Recomendación adicional para producción:

- Rotar la API key periódicamente desde la consola de Google Cloud.
- Usar variables de entorno del servidor (no `.env`) en entornos de producción.
- Restringir la clave de Google Cloud solo a las APIs necesarias (Gemini API).
- Monitorear el uso de la API para detectar consumo anómalo.

---

## Cómo correr la aplicación

```bash
# Clonar el repositorio
git clone <url-del-repositorio>
cd <nombre-del-repositorio>

# Instalar dependencias
pip install -r requirements.txt

# Configurar variables de entorno
cp .env.example .env
# Editar .env y colocar tu GEMINI_API_KEY y GEMINI_MODEL

# Ejecutar la aplicación
python -m uvicorn main:app --port 8000

# Abrir en el navegador
# http://localhost:8000
```

### Ejecutar pruebas

```bash
pip install pytest
python -m pytest test_app.py -v
```

---

## Despliegue en producción

Para correr la aplicación en un entorno de producción, sigue estos pasos:

### 1. Configurar variables de entorno

Copia el archivo de ejemplo y coloca tus valores reales:

```bash
cp .env.production.example .env.production
```

Edita `.env.production` con tu `GEMINI_API_KEY` real y el modelo deseado. Asegúrate de que `ENVIRONMENT=production`.

### 2. Instalar dependencias

```bash
pip install -r requirements.txt
```

### 3. Ejecutar la aplicación

Usa `uvicorn` sin el modo de recarga automática (`--reload`), que solo es para desarrollo:

```bash
python -m uvicorn main:app --host 0.0.0.0 --port 8000
```

Para mayor rendimiento en producción, se recomienda usar múltiples workers:

```bash
python -m uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
```

### 4. Variables de entorno requeridas en producción

| Variable | Descripción | Obligatoria |
|----------|-------------|-------------|
| `GEMINI_API_KEY` | Clave de API de Google Gemini | Sí |
| `GEMINI_MODEL` | Modelo de Gemini a usar (ej. `gemini-2.5-flash`) | Sí |
| `ENVIRONMENT` | Entorno de ejecución (`production`, `development`) | Recomendado |

### 5. Consideraciones de seguridad

- Nunca subas el archivo `.env` ni `.env.production` al repositorio. Ambos están en `.gitignore`.
- La base de datos SQLite (`recordatorios.db`) también está en `.gitignore` y no debe subirse.
- Los headers de seguridad (`X-Content-Type-Options`, `X-Frame-Options`, `X-XSS-Protection`, `Referrer-Policy`) se agregan automáticamente en cada respuesta.
- Los errores no revelan detalles internos ni stack traces al cliente.

### 6. Base de datos

La aplicación usa SQLite con un archivo local (`recordatorios.db`). Es adecuada para el volumen esperado (~10 socios por semana). No requiere configuración adicional; la tabla se crea automáticamente al iniciar la aplicación.

---

## Estructura del repositorio

```
.
├── main.py              # FastAPI, rutas y lógica principal
├── models.py            # Esquemas Pydantic
├── db.py                - SQLite: guardar, obtener, marcar enviado
├── gemini.py            # Llamada a Gemini y modo simulado
├── requirements.txt     # Dependencias de Python
├── .env.example         # Variables de entorno de ejemplo
├── .gitignore           # Archivos ignorados por Git
├── test_app.py          # Pruebas con pytest
├── BITACORA.md          # Registro de cambios
├── README.md            # Este archivo
└── static/
    ├── index.html       # Página única
    ├── style.css        # Estilos CSS
    └── app.js           # JavaScript simple
```

---

*Nota: No se incluye login, Docker, integración con WhatsApp, cálculo automático de vencimientos ni almacenamiento de teléfonos, tal como se definió en el alcance del proyecto.*