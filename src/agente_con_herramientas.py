from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.tools import tool
from langchain_classic.agents import (
    AgentExecutor,
    create_tool_calling_agent,
)
from langchain_core.prompts import (
    ChatPromptTemplate,
    MessagesPlaceholder,
)

load_dotenv()

modelo = ChatGoogleGenerativeAI(model="gemini-3.6-flash")

#Tool/Herramienta es una función común de Python. Descripción en lenguaje natural será lo que el modelo lea (prompt) para decidir si elige o no esa herramienta
@tool
def buscar_en_documentacion(consulta:str) -> str:
    """
    Busca información relevante de la documentación interna del producto.
    Usar cuando la pregunta es sobre cómo funciona algo del sistema.
    """
    documentacion = {
        "reintentos": "El cliente reintenta hasta 3 veces ante un TimeoutError, con espera creciente",
        "costos": "El costo se calcula a patir de totalTokenCount, según la tarifa vigente."
    }

    for clave, texto in documentacion.items():
        if clave in consulta.lower():
            return texto

    return "No se encontró información sobre esa consulta en la documentación."

@tool
def calcular(expresion: str) -> str:
    """
    Evalúa una expresión aritmética simple, como '350 + 250'.
    Usar cuando la pregunta require un cálculo numérico.
    """
    permitido = set("0123456789+-*/().")
    if not set(expresion) <= permitido:
        return "Expresión no permitida."
    try:
        return str(eval(expresion))
    except Exception as e:
        return f"Error al evaluar: {e}"

herramientas = [buscar_en_documentacion, calcular] #Lista de Herramientas

#Plantilla, con system_instructions
prompt_agente = ChatPromptTemplate.from_messages([
    (
        "system", "Eres un asistente que responde preguntas usando las herramientas disponibles cuando las necesites."
    ),
    # (
    #     "system", "Eres un asistente que responde preguntas solamente usando las herramientas disponibles cuando las necesites. No inventes información que no tengas."
    # ),
    (
        "human", "{entrada}"
    ),
    MessagesPlaceholder("agent_scratchpad") #El espacio donde LangChain va anotando, pasos/ciclos razonar-actuar-observar, qué herramientas llamó y qué devolvieron
])

#Agente: modelo, herramientas, prompt, formato
agente = create_tool_calling_agent(
    modelo, herramientas, prompt_agente
)

#Orquestador: es el que controla el ciclo entre razonar-actuar-observar
ejecutor_agente = AgentExecutor(
    agent=agente,
    tools=herramientas,
    verbose=True, #Imprime los pasos que va siguiendo
)

resultado = ejecutor_agente.invoke(
    {"entrada": "¿Qué es LangChain?"}
)

print("Respuesta Final:", resultado["output"][0]["text"])
