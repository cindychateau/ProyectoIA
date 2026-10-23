import time
from typing import Callable, Any

from src.consumir_gemini import armar_peticion, extraer_texto, enviar_peticion

def con_reintento(
    funcion: Callable[[], Any],
    intentos: int = 3,
    espera_segundos: int = 2
) -> Any:
    for intento in range(intentos):
        try:
            return funcion()
        except TimeoutError:
            if intento == intentos-1:
                raise
            print(f"Intento {intento+1} de {intentos} falló por límite de uso/servidor. Reintentando...")
            time.sleep(espera_segundos)


#Cómo ejecuto esto?
if __name__ == "__main__":
    url, cuerpo = armar_peticion("gemini-3.5-flash-lite", "Hola", "")
    respuesta = con_reintento(lambda: enviar_peticion(url, cuerpo))
    print(respuesta)