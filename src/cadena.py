from dotenv import load_dotenv
import os
from langchain_google_genai import ChatGoogleGenerativeAI #Modelo
from langchain_core.prompts import PromptTemplate #Plantilla -> Prompt dinámico
from langchain_core.output_parsers import StrOutputParser #Parsea la respuesta y la transforma en solo textos
from langchain_core.prompts import ChatPromptTemplate #Plantilla que incluye rol del sistema e instrucción

load_dotenv()

#api_key = os.getenv("API_KEY_AI")
#modelo = ChatGoogleGenerativeAI(model="gemini-3.6-flash", api_key=api_key)
modelo = ChatGoogleGenerativeAI(model="gemini-3.6-flash") 
#respuesta = modelo.invoke("¿Qué es un token?")
#print(respuesta.content)

#f-strings
plantilla = PromptTemplate.from_template(
    "Explica el concepto de {tema} en un párrafo, para alguien que recien comienza en {area}."
)

# prompt = plantilla.invoke(
#     {"tema": "tokenización", "area": "procesamiento de texto"}
# )

#print(prompt.text)

cadena_simple = plantilla | modelo | StrOutputParser()

respuesta = cadena_simple.invoke({"tema": "embeddings", "area": "búsqueda semántica"})

print(respuesta)

plantilla_conrol = ChatPromptTemplate.from_messages([
    ("system", "Eres un experto en el área correspondiente, vas a responder siempre con texto simple para el usuario."),
    ("human", "Explica el concepto de {tema} en un párrafo, para alguien que recien comienza en {area}")
])