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



#FUNCIONAMIENTO: BaseCallbackHandler -> cuando la cadena comience, cuando retriever comience, cuando retr termine, cuando el  comience, cuando el modelo termine
#Heredo de BaseCallbackHandler, ya tiene definidos mis métodos que detectan una acción/evento de Langchain y sobreescribimos esos eventos para registrar el log de lo que está sucediendo
class HandlerDeTrazabilidad(BaseCallbackHandler):
    #1.- Comienza mi cadena
    def on_chain_start(self, serialized, inputs, *, run_id, parent_run_id=None, **kwargs):
        if parent_run_id is None: #Es la cadena principal
            logger.info(
                "inicio_cadena",
                extra={
                    "extra_data": {
                        "root_run_id": str(run_id)
                    }
                }
            )
    
    #CICLO DE VIDA: retriever
    #on_retriever_start: Se dispara ANTES de que el retriever haga la búsqueda vectorial
    def on_retriever_start(self, serialized, query, *, run_id, parent_run_id=None, metadata=None, **kwargs):
        #query: el texto exacto con el que se está haciendo la búsqueda semántica
        #metadata: diccionario que pasamos en config
        logger.info(
            "retriever_start",
            extra={
                "extra_data": {
                    "run_id": str(run_id),
                    "parent_run_id": str(parent_run_id),
                    "query_len": len(query),
                    "query_hash": generar_huella(query),
                    "meta_trace": (metadata or {}).get("trace_id")
                }
            }
        )

    #on_retriever_end: Se dispara INMEDIATAMENTE DESPUES de recibir los chunks
    def on_retriever_end(self, documents, *, run_id, parent_run_id=None, **kwargs):
        #documents: la lista de objetos Document que recuperamos de la base vectorial. CHUNKS
        docs_huellas = [generar_huella(d.page_content) for d in documents] #Hashea todos los chunks que recibimos
        logger.info(
            "retriever_end",
            extra={
                "extra_data": {
                    "n_documents": len(documents),
                    "huellas_docs": docs_huellas
                }
            }
        )
    
    #CICLO DE VIDA DE MODELO
    #on_chat_model_start: dispara ANTES de enviar los mensajes (System + Human)
    def on_chat_model_start(self, serialized, messages, *, run_id, parent_run_id=None, **kwargs):
        #messages: lista de mensajes formateados que recibe el modelo
        logger.info(
            "llm_start",
            extra={
                "extra_data": {
                    "run_id": str(run_id),
                    "parent_run_id": str(parent_run_id),
                    "n_prompts": len(messages)
                }
            }
        )
    
    #on_llm_end: dispara cuando TERMINA el agente de generar la respuesta
    def on_llm_end(self, response, *, run_id, parent_run_id=None, **kwargs):
        #response: Respuesta/texto generado de mi API
        texto_salida = response.generations[0][0].text #Navegar a la estructura interna para sacar el texto generado
        logger.info(
            "llm_end",
            extra={
                "extra_data": {
                    "chars_respuesta": len(texto_salida),
                    "respuesta_hash": generar_huella(texto_salida)
                }
            }
        )

#Cadena: contexto (retriever + formateo_contexto) | prompt | chat_model | StrOutputParser
def ejecutar_consulta(vectorstore, pregunta: str, k: int=3):
    token = trace_id_var.set(f"trace-{uuid.uuid4().hex[:8]}")
    try:
        retriever = vectorstore.as_retriever(search_kwargs={"k": k})
        prompt = ChatPromptTemplate.from_messages([
            ("system", "Eres un asistente de soporte. Cita la fuente de cada afirmacion con su numero entre corchetes, como [1]. Si el contexto no alcanza para responder, dilo explicitamente en vez de inventar"),
            ("human", "Contexto: \n{contexto}\n\n Pregunta: {pregunta}")
        ])
        modelo = ChatGoogleGenerativeAI(model="gemini-3.5-flash-lite")
        runnable_contexto = RunnableLambda(lambda chunks: formatear_contexto(chunks)[0])

        """
        1.- Toma la pregunta, busca en el vectorstore y pasa el resultado por formatear_contexto (resultado: contexto formateado)
            1.1.- Paso la pregunta original INTACTA
        2.- Inyecta al prompt (resultado: prompt ya con contexto y pregunta)
        3.- Mando el prompt al modelo
        4.- Parseo el texto
        """
        cadena = (
            {
                "contexto": retriever | runnable_contexto,
                "pregunta": RunnablePassthrough()
            }
            | prompt
            | modelo
            | StrOutputParser()
        )

        handler = HandlerDeTrazabilidad() #Invoco a la cadena, PASANDOLE el handler. Detectar los eventos mientras se ejecuta la cadena
        cadena.invoke(
            pregunta,
            config={
                "callbacks": [handler],
                "metadata": {"trace_id": trace_id_var.get()}
            }
        )
    finally:
        trace_id_var.reset(token) #BORRO el trace_id para futuras consultas


if __name__ == "__main__":
    CARPETA_DB = "vectorstore_ejemplo"
    K = 3
    vs = cargar_vectorstore(CARPETA_DB)
    ejecutar_consulta(vs, "¿Cuántos intentos hace el cliente ante un TimeoutError y cuánto espera entre cada uno?", 3)