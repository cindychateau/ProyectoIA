from collections import Counter
from .pipeline_limpieza import procesar_texto
from .cliente import consultar_modelo
import json
from pathlib import Path


def contar_coincidencias(
    tokens_referencia: list[str],
    tokens_respuesta: list[str],
) -> int:
    """Cuenta las coincidencias entre referencia y respuesta."""
    conteo_referencia = Counter(tokens_referencia)
    conteo_respuesta = Counter(tokens_respuesta)
    interseccion = conteo_referencia & conteo_respuesta
    return sum(interseccion.values())

def calcular_precision_cobertura_f1(
    tokens_referencia: list[str],
    tokens_respuesta: list[str],
) -> dict[str, float]:
    """Calcula precisión, cobertura y F1 de dos listas de tokens."""
    coincidencias = contar_coincidencias(
        tokens_referencia, tokens_respuesta
    )

    if not tokens_respuesta or not tokens_referencia:
        return {"precision": 0.0, "cobertura": 0.0, "f1": 0.0}

    precision = coincidencias / len(tokens_respuesta)
    cobertura = coincidencias / len(tokens_referencia)

    if precision + cobertura == 0:
        f1 = 0.0
    else:
        f1 = 2 * precision * cobertura / (precision + cobertura)

    resultado = {
        "precision": precision,
        "cobertura": cobertura,
        "f1": f1,
    }

    return resultado

def calcular_metricas(texto_referencia, texto_respuesta):
    tokens_referencia = procesar_texto(texto_referencia)
    tokens_respuesta = procesar_texto(texto_respuesta)
    
    return calcular_precision_cobertura_f1(
        tokens_referencia, tokens_respuesta
    )

casos = [
    (
        "¿Qué es Python?",
        "Python es un lenguaje de programación interpretado.",
    ),
    (
        "¿En qué año fue la primera publicación de Python?",
        "La primera publicación de Python fue en 1991.",
    ),
    (
        "¿Qué es una lista en Python?",
        "Una lista es una colección ordenada y modificable.",
    ),
    (
        "¿Qué devuelve len en Python?",
        "len devuelve la cantidad de elementos de un objeto.",
    ),
    (
        "¿Para qué sirve print en Python?",
        "print muestra una representación de los objetos en la salida de texto.",
    ),
    (
        "¿Qué es un diccionario en Python?",
        "Un diccionario relaciona claves con valores.",
    ),
    (
        "¿Qué es una tupla en Python?",
        "Una tupla es una secuencia inmutable.",
    ),
    (
        "¿Qué es un conjunto en Python?",
        "Un conjunto almacena elementos únicos.",
    ),
    (
        "¿Para qué sirve def en Python?",
        "def define una función.",
    ),
    (
        "¿Qué hace return en una función?",
        "return termina la función y devuelve un valor al llamador.",
    ),
    (
        "¿Para qué sirve try except en Python?",
        "try except permite manejar excepciones.",
    ),
    (
        "¿Qué indica HTTP 429?",
        "HTTP 429 indica demasiadas solicitudes.",
    ),
    (
        "¿Qué indica HTTP 403?",
        "HTTP 403 indica que el servidor rechaza autorizar la solicitud.",
    ),
    (
        "¿Qué significa backoff exponencial?",
        "El backoff exponencial aumenta la espera entre reintentos de forma exponencial.",
    ),
    (
        "¿Para qué sirve jitter en los reintentos?",
        "El jitter añade aleatoriedad a la espera para evitar reintentos simultáneos.",
    ),
    (
        "¿Qué hace lower en una cadena de Python?",
        "lower devuelve una copia de la cadena convertida a minúsculas.",
    ),
    (
        "¿Qué hace split sin argumentos en Python?",
        "split divide una cadena por secuencias de espacios en blanco.",
    ),
    (
        "¿Qué hace Counter en Python?",
        "Counter cuenta las apariciones de cada elemento.",
    ),
    (
        "¿Qué hace el modo a al escribir en un archivo?",
        "El modo a agrega contenido al final sin borrar el contenido existente.",
    ),
    (
        "¿Qué ventaja tiene usar un mock de la API en una prueba?",
        "Permite probar el código sin depender de la red ni consumir la API real.",
    ),
]

raiz = Path(__file__).resolve().parents[1]
ruta_resultados = raiz / "resultados_metricas.json"

# Recupera las respuestas guardadas en una ejecución anterior.
if ruta_resultados.exists():
    with ruta_resultados.open(
        "r",
        encoding="utf-8"
    ) as archivo:
        resultados = json.load(archivo)
else:
    resultados = []

# Identifica los casos ya completados.
completados = {
    (caso["consulta"], caso["referencia"])
    for caso in resultados
}

for numero, (consulta, referencia) in enumerate(
    casos,
    start=1
):
    # Continúa sin repetir las consultas ya guardadas.
    if (consulta, referencia) in completados:
        print("Ya guardada:", consulta)
        continue

    try:
        respuesta = consultar_modelo(
            consulta,
            system_instruction=(
                "Responde en español con una definición breve, "
                "en una sola oración de máximo 15 palabras. "
                "Sin listas, ejemplos ni introducciones."
            )
        )

    except RuntimeError as error:
        print("\nSe detuvo la generación:", error)
        print(f"Respuestas guardadas: {len(resultados)}")
        break

    metricas = calcular_metricas(referencia, respuesta)

    resultados.append({
        "id": numero,
        "consulta": consulta,
        "referencia": referencia,
        "respuesta": respuesta,
        **metricas,
    })

    # Guarda inmediatamente después de cada respuesta.
    with ruta_resultados.open(
        "w",
        encoding="utf-8"
    ) as archivo:
        json.dump(
            resultados,
            archivo,
            indent=2,
            ensure_ascii=False
        )

    completados.add((consulta, referencia))

    print("\nConsulta:", consulta)
    print("Respuesta:", respuesta)
    print("Métricas:", metricas)
    print(f"Guardadas: {len(resultados)}/{len(casos)}")

def resumir_metricas(resultados):
    if not resultados:
        return {
            "precision_promedio": 0,
            "cobertura_promedio": 0,
            "f1_promedio": 0,
        }
    n = len(resultados)
    return {
        "precision_promedio": sum(
            r["precision"] for r in resultados
        ) / n,
        "cobertura_promedio": sum(
            r["cobertura"] for r in resultados
        ) / n,
        "f1_promedio": sum(r["f1"] for r in resultados) / n,
    }
    
print("Promedios")
print(resumir_metricas(resultados))
    
peores_casos = sorted(resultados, key=lambda r: r["f1"])

for caso in peores_casos[:3]:
    print(caso["consulta"], caso["f1"])
    
    
# referencia = procesar_texto(
#     "Python es un lenguaje de programación interpretado."
# )

# texto_respuesta = consultar_modelo("¿Qué es Python?",
#                                    system_instruction="Responde en español con una definición breve, en una sola oración de máximo 15 palabras. Sin listas, ejemplos ni introducciones.")

# respuesta = procesar_texto(texto_respuesta)
# resultado = calcular_precision_cobertura_f1(referencia, respuesta)

# print("Respuesta:", texto_respuesta)
# print("Tokens de referencia:", len(referencia))
# print("Tokens de respuesta:", len(respuesta))
# print(resultado)