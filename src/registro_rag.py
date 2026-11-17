import time #Latencia
import json #Registrar en jsonl la info
from contextlib import contextmanager #administrador de contexto: ejecuta antes, durante y después de hacerse una acción
from datetime import datetime, timezone
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI #Modelo para instanciar gemini

from rag_indexer import cargar_vectorstore, formatear_contexto 

load_dotenv()

#Plantilla que me obligue a usar SOLO el contexto recuperado y también a citar [1], [2]
PROMPT_TEMPLATE = """Responde la pregunta usando SOLO el contexto de abajo. Cita la \
fuente de cada afirmacion con su numero entre corchetes, como [1]. Si el contexto no \
alcanza para responder, dilo explicitamente en vez de inventar.

Contexto:
{contexto}

Pregunta: {pregunta}

Respuesta:

""" #contexto = el resultado de la búsqueda de vs, formateado con formatear_contexto, pregunta = la consulta del usuario final

def aprox_tokens(texto: str) -> int:
    return len(texto) // 4


#Latencia

#Calculo de costos (tokens_entrada, tokens_salida, tarifa_entrada, tarifa_salida)


if __name__ == "__main__":
    CARPETA_DB = "vectorstore_ejemplo"
    K = 3
    vs = cargar_vectorstore(CARPETA_DB)

    pregunta = "¿Cuántos intentos hace el cliente ante un TimeoutError y cuánto espera entre cada uno?"

    retriever = vs.as_retriever(search_kwargs={"k": K})
    chunks = retriever.invoke(pregunta)

    contexto, citas = formatear_contexto(chunks)
    prompt_con_rag = PROMPT_TEMPLATE.format(contexto=contexto, pregunta=pregunta) #Prompt con los chunks que recibimos de vs y la pregunta

    print(f"Pregunta sola. Caracteres: {len(pregunta)}. Tokens Aprox: {aprox_tokens(pregunta)}")
    print(f"Prompt con RAG. Caracteres: {len(prompt_con_rag)}. Tokens Aprox: {aprox_tokens(prompt_con_rag)}") #Ya incluye chunks
    print("Factor de crecimiento:", round(len(prompt_con_rag) / len(pregunta), 1), "x")
