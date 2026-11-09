from typing import List
from pydantic import BaseModel, Field, constr, conint


class SocioEntrada(BaseModel):
    """Un socio a procesar: nombre, días vencidos y plan."""
    nombre: constr(max_length=60) = Field(..., description="Nombre del socio")
    dias_vencidos: conint(ge=0) = Field(..., description="Días de membresía vencida (>= 0)")
    plan: constr(max_length=40) = Field(..., description="Plan de membresía")


class MensajeSalida(BaseModel):
    """Un mensaje generado con su tono."""
    tono: str
    mensaje: constr(max_length=280)


class ResultadoSocio(BaseModel):
    nombre: str
    dias_vencidos: int
    plan: str
    mensajes: List[MensajeSalida]


class PeticionGenerar(BaseModel):
    socios: List[str] = Field(..., max_items=30, description="Líneas 'nombre|días vencidos|plan'")


class RespuestaGenerar(BaseModel):
    resultados: List[ResultadoSocio]
