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
    }
}

#Herramientas
@tool("consultar_estado_envio_detallado", )
def consultar_estado_envio_detallado(numero_seguimiento, incluir_historial: bool):
    #Descripción
    #Consultar BD con el num_seguimiento
    #si no encuentro -> No se encontró
    #Reviso si quiere incluir historial
        #Si no -> envio[actual]
    #generar una variable historial concatenando todos los items de envio[historial]
    #-> envio[actual], envio[historial]