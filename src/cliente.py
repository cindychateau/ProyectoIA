import time
import random
from typing import Callable, Any
from .consumir_gemini import armar_peticion, extraer_texto, enviar_peticion

MODELO = "gemini-3.6-flash"

def con_reintento(
    funcion: Callable[[], Any], 
    intentos: int = 3, 
    espera_base: float = 2, 
    espera_maxima: float = 30,) -> Any:
    
    for intento in range(1, intentos + 1):
        try:
            return funcion()
        except TimeoutError:
            if intento == intentos:
                raise
            espera = min(espera_base * (2 ** (intento - 1)), espera_maxima)
            espera_con_jitter = espera + random.uniform(0, espera * 0.1)
            print(f"Intento {intento} de {intentos} falló. Reintentando en {espera_con_jitter:.1f}s...")
            time.sleep(espera_con_jitter)


COSTO_POR_1000_TOKENS = 0.002  # referencial, ajusta según el modelo que uses
costo_total_sesion = 0.0

def registrar_costo(respuesta: dict) -> float:
    global costo_total_sesion
    uso = respuesta.get("usageMetadata", {})
    total_tokens = uso.get("totalTokenCount", 0)
    costo_estimado = (total_tokens / 1000) * COSTO_POR_1000_TOKENS
    costo_total_sesion += costo_estimado
    print(f"Operación: {total_tokens} tokens, costo estimado: ${costo_estimado:.5f} (acumulado: ${costo_total_sesion:.5f})")
    return costo_estimado
 
 
def consultar_modelo(pregunta: str, system_instruction: str = "") -> str:
    url, cuerpo = armar_peticion(MODELO, pregunta, system_instruction)
    try:
        respuesta = con_reintento(lambda: enviar_peticion(url, cuerpo))
    except TimeoutError as error:
        raise RuntimeError(
            f"Se agotaron los intentos. Causa: {error}"
        ) from error
    registrar_costo(respuesta)
    return extraer_texto(respuesta)