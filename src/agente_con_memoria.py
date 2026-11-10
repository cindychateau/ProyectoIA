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
from langchain_core.chat_history import InMemoryChatMessageHistory #Crear el historial en base a la sesión
from langchain_core.runnables.history import RunnableWithMessageHistory #Encapsular mi agente para que implemente la memoria

import queue
import threading
import sys
from datetime import datetime

#=== Configuraciones e Inicializaciones===
load_dotenv()
modelo = ChatGoogleGenerativeAI(model="gemini-3.6-flash")

#=== Auditoría/Human in the Loop ===
registro_aprobaciones = []

def esperar_aprobacion(mensaje: str, tiempo_limite_segundos: int = 15) -> bool:
    cola_respuesta = queue.Queue()

    def pedir_entrada():
        try:
            texto = input(mensaje)
            cola_respuesta.put(texto.strip().lower())
        except(EOFError, KeyboardInterrupt):
            cola_respuesta.put("")
    
    hilo = threading.Thread(target=pedir_entrada, daemon=True)
    hilo.start()

    try:
        respuesta = cola_respuesta.get(timeout=tiempo_limite_segundos)
        return respuesta == "s"
    except queue.Empty:
        print("Tiempo de espera agotado. Solicitud denegada por timeout")
        return False

def registrar_aprobacion(herramienta: str, argumentos: dict, aprobado: bool) -> None:
    registro_aprobaciones.append({
        "herramienta": herramienta,
        "argumentos": argumentos,
        "aprobado": aprobado,
        "fecha_hora": datetime.now().isoformat() #2026-11-10T15:56:10
    })


#=== Esquemas de Validación ===
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

#=== Base de Datos ===
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

#=== Herramientas ===
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

@tool
def calcular_costo_envio(peso_kg: float, distancia_km: float) -> str:
    """Calcula el costo estimado de un envío según su peso y la distancia a recorrer.
    Usar cuando el usuario pregunta cuánto va a costar enviar algo."""
    costo = 500 + (peso_kg * 120) + (distancia_km * 3)
    return f"El costo estimado es de ${costo:.2f}"

@tool
def generar_reembolso(numero_pedido: str, monto: float) -> str:
    """
    Generar un reembolso económico para un pedido. Acción irreversible: requiere aprobación humana antes de ejecutarse.
    """
    mensaje = f"[SUPERVISIÓN HUMARA REQUERIDA] El usuario solicita reembolsar ${monto} para el pedido {numero_pedido}. ¿Desea aprobar? (s/n): "

    #Congelar el proceso, hasta que el supervisor de el visto bueno
    aprobado = esperar_aprobacion(mensaje, tiempo_limite_segundos=15)

    #Registrar en la lista si se aprobó o rechazó el reembolso
    registrar_aprobacion(
        herramienta="generar_reembolso",
        argumentos={"numero_pedido": numero_pedido, "monto": monto},
        aprobado=aprobado
    )

    if not aprobado:
        return "Reembolso no aprobado por el supervisor o cancelado por timeout"
    
    #Acciones para regresar el dinero (Ej: llamada a la pasarela de pago)
    return f"Reembolso de {monto} fue generado con éxito para el pedido {numero_pedido}"

#Listado de herramientas
herramientas = [consultar_estado_envio_detallado, calcular_costo_envio, generar_reembolso]

#=== Gestión de historial en memoria ===
historiales = {}
"""
historiales = {
    'cliente_123': {MENSAJES},
    'cliente_345': {MENSAJES},
    'cliente_567': {"Cuánto me cuesta x y y?"}
}
"""
def obtener_historial(session_id: str): #cliente_567
    if session_id not in historiales:
        historiales[session_id] = InMemoryChatMessageHistory()
    return historiales[session_id]


#=== Construcción del agente ===
prompt_agente = ChatPromptTemplate.from_messages([
    (
        "system", "Eres un asistente de logística que responde preguntas usando las herramientas disponibles."
    ),
    MessagesPlaceholder("chat_history"),
    ("human", "{entrada}"),
    MessagesPlaceholder("agent_scratchpad")
])

agente = create_tool_calling_agent(modelo, herramientas, prompt_agente)

ejecutor_agente = AgentExecutor(
    agent=agente,
    tools=herramientas,
    verbose=True
)

limpiar_salida = RunnableLambda(
    lambda d: {**d, "output": d["output"][0]["text"] if isinstance(d.get("output"), list) else d.get("output")}
)

cadena_agente = ejecutor_agente | limpiar_salida

#agente con memoria
agente_con_memoria = RunnableWithMessageHistory(
    cadena_agente,
    obtener_historial,
    input_messages_key="entrada",
    history_messages_key="chat_history",
    output_messages_key="output"
)

#=== Ejecución ===
if __name__ == "__main__":
    # resultado = ejecutor_agente.invoke(
    #     {"entrada": "¿Cuál es el estado del envío AR12345, con su historial?"}
    # )

    #print("Respuesta: ", resultado["output"][0]["text"])
    
    # config1 = {"configurable": {"session_id": "cliente_456"}}
    # resultado1 = agente_con_memoria.invoke(
    #     {"entrada": "¿Cuál es el estado del envío AR12345, con su historial?"},
    #     config1
    # )

    # print("Turno 1: ", resultado1["output"])

    # resultado2 = agente_con_memoria.invoke(
    #     {"entrada": "¿Y ese mismo envío ya fue entregado?"},
    #     config1
    # )

    # print("Turno 2: ", resultado2["output"])

    # config2 = {"configurable": {"session_id": "cliente_567"}}
    # resultado3 = agente_con_memoria.invoke(
    #     {"entrada": "¿Cuánto cuesta enviar un paquete de 3kg a 300km"},
    #     config2
    # )

    # print("Turno 3:", resultado3['output'])

    # resultado4 = agente_con_memoria.invoke(
    #     {"entrada": "¿Y cuánto costaría con el doble de peso?"},
    #     config2
    # )

    # print("Turno 4:", resultado4['output'])

    config_reembolso = {"configurable": {"session_id": "cliente_123"}}
    resultado_reembolso = agente_con_memoria.invoke(
        {"entrada": "Mi pedido PED123 llegó roto. Exijo un reembolso de mis 25000 pesos."},
        config_reembolso
    )

    print("Resultado: ", resultado_reembolso)

    print("Registros de reembolsos:")
    for registro in registro_aprobaciones:
        print(registro)




