from pydantic import BaseModel, Field

class Consulta(BaseModel):
    #pregunta: str
    pregunta: str = Field(
        description="Pregunta del usuario, en lenguaje natural",
        examples=["¿Cuál es el plazo para devolucion?"]
    )

class Respuesta(BaseModel):
    respuesta: str
    fuentes: list[str]