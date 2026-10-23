import json
import time
from prompts.banco import BANCO_DE_PROMPT
from consumir_gemini import armar_peticion, enviar_peticion, extraer_texto, parsear_respuesta_json

registro = {}

try:
    #leer el archivo y guardarlo en una variable
    for prompt in BANCO_DE_PROMPT:
        exitos = 0
        intentos = 3
        for intento in range(intentos):
            url, body = armar_peticion(
                "gemini-3.5-flash-lite", 
                prompt["ejemplo_usuario"], 
                prompt["system_instruction"], 
                prompt["response_schema"]
            )
            respuesta = enviar_peticion(url, body)
            texto = extraer_texto(respuesta)
            try:
                datos = parsear_respuesta_json(texto, prompt["claves_esperadas"])
                exitos += 1 #exitos++
                print(f"Respuesta: {datos}")
            except ValueError as error:
                print(f" intento {intento + 1} falló: {error}")
            time.sleep(1)
        print(f"{prompt["nombre"]}: {exitos}/{intentos} respuestas válidas")
        registro[prompt["nombre"]] = {"exitos": exitos, "intentos": intentos}
        #with open ("a")
    #Cuando termine de recorrer los prompts quiero guardar esa info en registro_resultados.json
    with open("src/prompts/registro_resultados.json", "w", encoding="utf-8") as archivo:
        json.dump(registro, archivo, indent=2, ensure_ascii=False)

except (ValueError, RuntimeError) as error:
    print("No se pudo completar la operación:", error)
