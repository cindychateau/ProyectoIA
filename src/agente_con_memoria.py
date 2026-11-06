#Herramientas Personalizadas
#Intro a Memoria

from dotenv import load_dotenv
from langchain_core.tools import tool
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables import RunnableLambda
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_classic.agents import (
    AgentExecutor,
    create_tool_calling_agent,
)
from pydantic import BaseModel, Field, ValidationError

#Configuraciones e Inicializaciones
load_dotenv()
modelo = ChatGoogleGenerativeAI(model="gemini-3.6-flash")

class ArgumentosConsultaEnvio(BaseModel): #class ClaseHija(ClasePadre):
    """
    Esquema para documentar y validar argumentos campo por campo ante el LLM.
    """
    numero_seguimiento: str = Field(
        description="Número de seguimiento del envío, por ejemplo 'AR129012'."
    )
    incluir_historial: bool = Field(
        default= False,
        description="Si es True, incluye en historial completo de los estados, no solo el actual."
    )

#Base de Datos
ESTADOS = {
    "AR12345": {
        "actual": "En tránsito, entrega estimada de 2 días",
        "historial": [
            "Recibido en depósito",
            "En tránsito"
        ]
    },
    "AR12346": {
        "actual": "Entregado",
        "historial": [
            "Recibido en depósito",
            "En tránsito"
        ]
    }
}

#Herramientas
#@tool("nuevo_nombre")
@tool(args_schema=ArgumentosConsultaEnvio) #LangChain transforma esta clase en un esquema JSON que se envía al LLM. El modelo lo lee textualmente
def consultar_estado_envio_detallado(numero_seguimiento: str, incluir_historial: bool = False):
    """
    Consulta el estado de un envío, con la opción de incluir el historial completo.
    """
    envio = ESTADOS.get(numero_seguimiento) #AR12346
    #envio = {
    #     "actual": "Entregado",
    #     "historial": [
    #         "Recibido en depósito",
    #         "En tránsito"
    #     ]
    # }
    if envio is None:
        return f"No se encontró un envío con el número {numero_seguimiento}."
    
    #Si no se solicita el historial, retornamos solo el estado actual
    if not incluir_historial:
        return envio["actual"]

    #Si sí se solicita el historial, formatear y retornar la info
    historial = ", ".join(envio["historial"]) # "Recibido en depósito, En tránsito"
    return f"{envio['actual']} (historial: {historial})" #"Entregado" (historial: Recibido en depósito, En tránsito)



#Listado de herramientas
herramientas = [consultar_estado_envio_detallado]

#Construcción del agente
prompt_agente = ChatPromptTemplate.from_messages([
    (
        "system", "Eres un asistente de logística que responde preguntas usando las herramientas disponibles."
    ),
    #Todo: historial de chats
    ("human", "{entrada}"),
    MessagesPlaceholder("agent_scratchpad")
])

agente = create_tool_calling_agent(modelo, herramientas, prompt_agente)

