#pip install fastapi uvicorn pydantic httpx2
#FastAPI: framework que me permite crear una API con endpoints (método, ruta, cuerpo)
#Uvicorn: implementar mi servidor web de manera local
#Para ejecutar mi API: uvicorn main:app --reload, Otro puerto: uvicorn main:app --reload --port 8001

from fastapi import FastAPI, status #importamos FastAPI

#Pydantic: Establecer clases y validar información (importar esquemas)
from esquemas import Consulta, Respuesta

app = FastAPI(title="API de ejemplos en clase", version="0.1.0") #Construye mi aplicación

#@app.metodo("/ruta")
#def funcion(): #Accion y respuesta que quiero entregar al usuario
@app.get("/bienvenido") #PATH
def bienvenido():
    return {"respuesta": "¡Bienvenido a FastAPI!"}

#Parámetro de Consulta
#http://127.0.0.1:8000/search?q=perritos
@app.get("/search", tags=["busquedas"], summary="Búsqueda de término q")
def search(q: str): #q = "perritos"
    """
    Recibe un término de búsqueda, y muestra las fuentes encontradas.
    """
    #Parámetro de consulta para por ejemplo buscar algo en tu RAG
    return {"respuesta": f"Estás buscando: {q}"} #Estás buscando: perritos

#Parámetro de Ruta
#http://127.0.0.1:8000/busqueda/computadora
@app.get("/busqueda/{termino}", tags=["busquedas"])
def busqueda(termino: str): #termino = "computadora"
    return {"respuesta": f"Estás buscando: {termino} a través de la ruta"}

@app.post("/consultas_v1", status_code=201) #status_code=status.HTTP_201_CREATED
def consultar_v1(datos: dict): #datos = {'pregunta': '¿Cuánto tengo para hacer mi devolucion?', 'status': 'False'}
    print(datos)
    pregunta = datos["pregunta"]
    #Consulta a tu RAG
    if "devolucion" in pregunta.lower():
        return {
            "respuesta": "Tienes 30 días para hacer la devolución",
            "fuentes": ["manual.pdf"]
        }
    
    return {
        "respuesta": "No encuentro esa información en el manual",
        "fuentes": []
    }

@app.post(
        "/consultas_v2", 
        summary="Consulta de manual", 
        tags=["consultas"],
        response_model=Respuesta)
def consultar_v2(datos: Consulta):
    if "devolucion" in datos.pregunta.lower():
        return Respuesta(
            respuesta="Tienes 30 días para la devolución.",
            fuentes=["manual.pdf"]
        )
    return Respuesta(
        respuesta="No encuentro esa información en el manual",
        fuentes=["manual.pdf"]
    )
