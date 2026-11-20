import contextvars #Genera una variable de contexto
import hashlib
import json
import logging
from logging.handlers import RotatingFileHandler #Permite exportar el log a un archivo
import sys
import uuid

from langchain_core.callbacks import BaseCallbackHandler
from langchain_core.output_parsers import StrOutputParser #Extrae el texto, manipula para estandarizarla
from langchain_core.prompts import ChatPromptTemplate #Plantilla que incluía el rol del sistema
from langchain_core.runnables import RunnableLambda, RunnablePassthrough #Pasa un argumento al siguiente paso
from langchain_google_genai import ChatGoogleGenerativeAI #La clase que llama al modelo llm

from rag_indexer import cargar_vectorstore, formatear_contexto

"""
Contextvars: crea una variable de contexto. 
Parecido a una variable global con la diferencia principal 
que aisla el valor de cada hilo/tarea asincrónica
"""
trace_id_var = contextvars.ContextVar("trade_id", default=None)

#Transforma el evento de log en un objeto de JSON de una sola línea
class JsonFormatter(logging.Formatter):
    def format(self, record):
        payload = {
            "ts": self.formatTime(record, "%Y-%m-%dT%H:%M:%S"),
            "level": record.levelname,
            "msg": record.getMessage(),
            "trace_id": trace_id_var.get(), #extrae de manera automática con el hilo/tarea activo
        }
        #Si se envía info adicional (extra_data) la agregamos
        #El tamaño del query, cuantos docs, cantidad de prompt, respuesta, chars respuesta
        if hasattr(record, "extra_data"):
            payload.update(record.extra_data)
        return json.dumps(payload, ensure_ascii=False)

#Configuración de mi logger
logger = logging.getLogger("rag_pipeline")
logger.setLevel(logging.INFO)
handler = logging.StreamHandler(sys.stdout) #Imprima los eventos que se están registrando
handler.setFormatter(JsonFormatter()) #Establezco el formato
archivo_handler = RotatingFileHandler(
    "rag_logs.jsonl",
    encoding="utf-8"
    #maxBytes, #backupCount (rag_logs.jsonl1, rag_logs.jsonl2)
)
archivo_handler.setFormatter(JsonFormatter())
logger.handlers = [handler, archivo_handler]
logger.propage = False #Evita que los logs se dupliquen

#No queremos guardar la información en crudo, sino que buscamos "esconderla"
#Genera una huella (hash sha 256 truncado) para poder detectar duplicados o cambios en mis documentos
def generar_huella(texto: str) -> str:
    return hashlib.sha256(texto.encode("utf-8")).hexdigest()[:12]



#BaseCallbackHandler -> cuando la cadena comience, cuando retriever comience, cuando retr termine, cuando el modelo comience, cuando el modelo termine

#Cadena: contexto (retriever + formateo_contexto) | prompt | chat_model | StrOutputParser
