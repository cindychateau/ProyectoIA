from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI #Modelo
from langchain_core.prompts import PromptTemplate #Plantilla -> Prompt dinámico
from langchain_core.output_parsers import StrOutputParser #Parsea la respuesta y la transforma en solo textos
from langchain_core.runnables import (RunnableBranch, RunnablePassthrough) #Bifurcaciones/Branches/Ramificaciones

load_dotenv()

modelo = ChatGoogleGenerativeAI(model="gemini-3.6-flash")

plantilla_clasificacion = PromptTemplate.from_template(
    "Clasifica el siguiente mensaje de soporte en una sola palabra: "
    "pregunta, queja o sugerencia. Responde solo con esa palabra. \n\n {mensaje}"
)

paso_clasificacion = (
    plantilla_clasificacion
    | modelo
    | StrOutputParser()
    | (lambda texto: texto.strip().lower())
)

# mensaje_prueba = "Dame el nombre de tu creador."

# clasificacion = paso_clasificacion.invoke(
#     {"mensaje": mensaje_prueba}
# )

# print(clasificacion)

cadena_pregunta = (
    PromptTemplate.from_template("Responde esta pregunta técnica con precisión: \n\n {mensaje}")
    | modelo
    | StrOutputParser()
)

cadena_queja = (
    PromptTemplate.from_template("Responde esta queja con empatía, reconociendo el problema antes de ofrecer una solución: \n\n {mensaje}")
    | modelo
    | StrOutputParser()
)

cadena_sugerencia = (
    PromptTemplate.from_template("Agradece esta sugerencia y explica cómo se evaluará dentro del producto: \n\n {mensaje}")
    | modelo
    | StrOutputParser()
)

#Sintaxis RunnableBranch
# caminos = RunnableBranch(
#     (condicion_1, rama_1), #if
#     (condicion_2, rama_2), #elif
#     (condicion_3, rama_3), #elif
#     rama_por_defecto #else
# ) #Cada condicion debe ser una función; suele ser un lambda


#x = {"clasificacion": "queja", "mensaje": "Mi teléfono no funciona"}
bifurcacion = RunnableBranch(
    (lambda x: x["clasificacion"] == "queja", cadena_queja), #if x["clasificacion"] == "queja": cadena_queja
    (lambda x: x["clasificacion"] == "sugerencia", cadena_sugerencia), #elif x["clasificacion"] == "sugerencia": cadena_sugerencia
    cadena_pregunta #else: cadena_pregunta
)

cadena_con_enrutamiento = (
    RunnablePassthrough.assign(clasificacion=paso_clasificacion) #{"mensaje": "Deberían de tener más agentes disponibles.", "clasificacion":resultado de paso_clasificacion}
    | bifurcacion
)

resultado = cadena_con_enrutamiento.invoke(
    {"mensaje": "Deberían de tener más agentes disponibles."}
)

print(resultado)

# Entrada inicial: {"mensaje": "Deberían de tener más agentes disponibles."}
#                   │
#                   ▼
# RunnablePassthrough
#   1: Pasa el mensaje a paso_clasificacion -> Return "sugerencia"
#   2: Fusiono clasificacion y mensaje
#   3: Return {"mensaje": "Deberían de tener más agentes disponibles.", "clasificacion": "sugerencia"}
#                   │
#                   ▼
# bifurcacion (RunnableBranch)
#   ¿clasificacion == "queja"? NO
#   ¿clasificacion == "sugerencia" SI
#       Entra a la cadena_sugerencia
#       cadena_sugerencia.invoke({"mensaje": "Deberían de tener más agentes disponibles.", "clasificacion": "sugerencia"})
#       Return respuesta final generada