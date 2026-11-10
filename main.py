import logging
from fastapi import FastAPI, Query, Request, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.exceptions import RequestValidationError
from dotenv import load_dotenv
load_dotenv()

import db
import gemini
from models import PeticionGenerar, RespuestaGenerar
logger = logging.getLogger(__name__)

app = FastAPI(title="Recordatorios de Renovación - Gimnasio")

app.mount("/static", StaticFiles(directory="static"), name="static")


@app.middleware("http")
async def seguridad_headers(request: Request, call_next):
    """Agrega headers de seguridad a todas las respuestas."""
    respuesta = await call_next(request)
    respuesta.headers["X-Content-Type-Options"] = "nosniff"
    respuesta.headers["X-Frame-Options"] = "DENY"
    respuesta.headers["X-XSS-Protection"] = "1; mode=block"
    respuesta.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    return respuesta


@app.on_event("startup")
def startup():
    db.init_db()


@app.exception_handler(RequestValidationError)
async def validacion_error_handler(request: Request, exc: RequestValidationError):
    # Error 400 genérico, sin detalles internos ni datos del socio.
    logger.warning("Validación fallida: %s", exc.errors())
    return JSONResponse(
        status_code=400,
        content={"detail": "Solicitud inválida. Revisa el formato y los límites."},
    )

@app.get("/health")
def health_check():
    return {"status": "ok"}


@app.get("/v1/models")
def listar_modelos():
    return {}


@app.get("/", response_class=HTMLResponse)
def index():
    with open("static/index.html", "r", encoding="utf-8") as f:
        return f.read()


@app.get("/historial")
def historial(
    nombre: str = Query(default=None, description="Filtrar por nombre del socio (insensible a mayúsculas/minúsculas)"),
    limite: int = Query(default=50, ge=1, le=100, description="Cantidad máxima de registros a devolver"),
    orden: str = Query(default="desc", description="Ordenar por días vencidos: 'asc' o 'desc'"),
):
    try:
        registros = db.obtener_historial(nombre=nombre, limite=limite, orden=orden)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    return JSONResponse(
        content=[
            {
                "id": r[0],
                "nombre": r[1],
                "dias_vencidos": r[2],
                "plan": r[3],
                "tono": r[4],
                "mensaje": r[5],
                "fecha_creacion": r[6],
                "enviado": bool(r[7]),
            }
            for r in registros
        ]
    )


@app.patch("/historial/{mensaje_id}/enviado")
def marcar_como_enviado(mensaje_id: int):
    """Marca un mensaje como enviado en el historial."""
    try:
        db.marcar_enviado(mensaje_id)
    except Exception:
        logger.exception("Error al marcar mensaje como enviado")
        raise HTTPException(
            status_code=500,
            detail="Error al actualizar el estado del mensaje.",
        )
    return JSONResponse(content={"ok": True, "id": mensaje_id})


@app.post("/generar")
async def generar(peticion: PeticionGenerar):
    try:
        resultados = gemini.generar_para_socios(peticion.socios)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail="Solicitud inválida. Revisa el formato y los límites.",
        )
    except Exception:
        # Error sin detalles internos.
        logger.exception("Error generando mensajes")
        raise HTTPException(
            status_code=500,
            detail="Error al generar los mensajes. Intenta de nuevo más tarde.",
        )

    # Guardar en el historial (SQLite). No se registra en logs.
    for r in resultados:
        for m in r.mensajes:
            db.guardar(r.nombre, r.dias_vencidos, r.plan, m.tono, m.mensaje)

    return JSONResponse(content=RespuestaGenerar(resultados=resultados).model_dump())
