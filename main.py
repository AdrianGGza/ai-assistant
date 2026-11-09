import logging
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.exceptions import RequestValidationError
from dotenv import load_dotenv

import db
import gemini
from models import PeticionGenerar, RespuestaGenerar

load_dotenv()

logger = logging.getLogger(__name__)

app = FastAPI(title="Recordatorios de Renovación - Gimnasio")

app.mount("/static", StaticFiles(directory="static"), name="static")


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


@app.get("/", response_class=HTMLResponse)
def index():
    with open("static/index.html", "r", encoding="utf-8") as f:
        return f.read()


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
