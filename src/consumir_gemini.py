import os
import requests
from dotenv import load_dotenv

import time

import json
import re

load_dotenv()

#Constantes
MODELO = "gemini-3.6-flash"
URL_BASE = "https://generativelanguage.googleapis.com/v1beta/models/"
API_KEY = os.getenv("GEMINI_API_KEY")

#función para crear la solicitud
def armar_peticion(modelo, pregunta, system_instruction, response_schema=None): #pregunta = "Confirma la conexion"
    if not pregunta:
        raise ValueError("La pregunta no puede estar vacía")
    url = f"{URL_BASE}{modelo}:generateContent?key={API_KEY}" #url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-3.6-flash:generateContent?key=MI API KEY"
    body = {
            "systemInstruction": {
                "parts": [ {"text": system_instruction} ]
            },
            "contents": 
                [{"parts": [{"text": pregunta}]}]
        }
    
    if response_schema is not None:
        body["generationConfig"] = {
            "responseMimeType": "application/json",
            "responseSchema": response_schema
        }


    return url, body

#armar_peticion_openai -> url, body

#función envía la petición
def enviar_peticion(url, body):
    try:
        respuesta = requests.post(url, json=body, timeout=30)
    except requests.exceptions.ConnectionError:
        raise RuntimeError("No se pudo conectar con el servicio. Intenta de nuevo en unos momentos.")
    except requests.exceptions.Timeout:
        raise RuntimeError("Se agotó el tiempo. Intenta de nuevo en unos momentos.")

    if respuesta.status_code != 200:
        raise RuntimeError(f"Error en la petición. Status Code: {respuesta.status_code}")

    try:
        return respuesta.json()
    except requests.exceptions.JSONDecodeError:
        raise RuntimeError("La respuesta del servicio no llegó en el formato esperado.")

#funcion procesa y extrae dato
def extraer_texto(datos): #Gemini
    try:
        return datos["candidates"][0]["content"]["parts"][0]["text"]
    except (KeyError, IndexError):
        raise RuntimeError("La respuesta no recibe el texto generado en el lugar definido.")

def obtener_dato_de_prueba(pregunta): #pregunta = "Confirma la conexion"

    response_schema = {
        "type": "OBJECT",
        "properties": {
            "categoria": {"type": "STRING"},
            "nivel": {"type": "NUMBER"}
        },
        "required": ["categoria", "nivel"]
    }

    system_instruction = "Eres un asistente amigable y respondes en máximo 2 palabras."
    url, body = armar_peticion("gemini-3.6-flash", pregunta, system_instruction, response_schema) #obtiene url y body

    inicio = time.perf_counter() #Empezar el contador

    #url = resultado de armar_peticion
    #body = resultado de armar_peticion
    datos = enviar_peticion(url, body)

    fin = time.perf_counter() #Termina el contador
    latencia = fin - inicio
    print(f"Latencia: {latencia:.2f} segundos")

    costo = calcular_costo(datos, 0.00000075, 0.00000375)
    print(f"Costo de la petición: ${costo:.6f} USD")
    texto = extraer_texto(datos)
    datos_formateados = parsear_respuesta_json(texto, ["categoria", "nivel"])
    return datos_formateados

#def calcular_costo(datos: dict, precio_entrada: float, precio_salida: float) -> float:
def calcular_costo(datos, precio_entrada, precio_salida):
    #datos = {dict... "usageMetadata"}
    uso = datos["usageMetadata"]
    '''
    uso = {
        "promptTokenCount": 10,
        "candidatesTokenCount": 471,
        "totalTokenCount": 1377,
        "promptTokensDetails": [
            {
                "modality": "TEXT",
                "tokenCount": 10
            }
        ],
        "thoughtsTokenCount": 896,
        "serviceTier": "standard"
    }
    '''
    tokens_entrada = uso["promptTokenCount"]
    tokens_salida = uso["candidatesTokenCount"]
    tokens_razonamiento = uso["thoughtsTokenCount"] #revisar si existe o no, si no existe colocarlo como 0
    costo = (tokens_entrada * precio_entrada) + ( (tokens_salida + tokens_razonamiento) * precio_salida )
    return costo

def parsear_respuesta_json(texto, claves_requeridas=None):
    """
    claves_requeridas = ["categoria", "nivel"]
    """
    texto_limpio = texto.strip()
    texto_limpio = re.sub(r"^```(?:json)?\s*", "", texto_limpio)
    texto_limpio = re.sub(r"\s*```$", "", texto_limpio)
    try:
        datos = json.loads(texto_limpio)
    except json.JSONDecodeError:
        raise ValueError("La respuesta del modelo no es JSON válido")
    
    if claves_requeridas:
        faltantes = [clave for clave in claves_requeridas if clave not in datos]
        if faltantes:
            raise ValueError("La respuesta no tiene la estructura esperada.")
    return datos

if __name__ == "__main__": #Solamente ejecútalo si el archivo en el que estoy está siendo directamente ejecutado. NO LO EJECUTA EN IMPORTS
    try:
        print(obtener_dato_de_prueba("Confirma en una frase corta que esta conexión funciona"))
    except (ValueError, RuntimeError) as error:
        print("No se pudo completar la operación: ", error)

'''
Ejecute 4 veces la MISMA petición con 1 modelo
y ante cada petición se calcule e imprima: Latencia, Costo, Respuesta

Vuelvo a hacer lo mismo con un modelo distinto

3 modelos a comparar

OBJETIVO: Elijas el mejor modelo para tu proyecto

Prompt sea algo relacionado con tu proyecto.
'''

