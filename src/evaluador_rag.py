from datetime import date
from rag_indexer import cargar_vectorstore


def precision_at_k(ids_recuperados: list[str], ids_relevantes: set[str]) -> float:
    """
    ids_recuperados los que me trajo el retriever
    De los 'k' chunks que me trajo el retriever, ¿qué fracción realmente sirve?
    Devuelve 0.0 si el retriever no devolvió ningún id
    """
    if not ids_recuperados:
        return 0.0
    
    #Recorro uno por uno cada ID que devolvió el retriever, si acaso existe en ids_relevantes lo agrego a la lista de acertados
    acertados = [i for i in ids_recuperados if i in ids_relevantes] 

    return len(acertados) / len(ids_recuperados)

def recall_at_k(ids_recuperados: list[str], ids_relevantes: set[str]) -> float | None:
    """
    Exhaustividad
    De todos los chunks relevantes que existen en mi corpus, ¿qué fracción logré rescatar?
    Devuelve None si la pregunta no tiene respuesta en corpus (ids_relevantes es vacío)
    """
    if not ids_relevantes:
        return None
    
    acertados = [i for i in ids_recuperados if i in ids_relevantes]
    return len(acertados) / len(ids_relevantes)

def f1_score(precision: float, recall: float | None) -> float:
    """
    Media armónica entre precisión y exhaustividad: equilibrio entre ambos para comparar
    configuraciones distintas de k o chunk_size.
    """
    if recall is None or (precision + recall) == 0:
        return 0.0
    
    return 2 * precision * recall / (precision + recall)

def evaluar_recuperacion(retriever, casos: list[dict], k: int = 3):
    """
    Correr cada caso del conjunto de evaluaciones contra el retriever real de Chroma
    y va a calcular precisión, recall y F1
    """
    resultados = []

    for caso in casos:
        #1.- Consultamos al retriever, cuáles son los chunks que me regresa la invocación. SI GASTA TOKENS
        chunks = retriever.invoke(caso["pregunta"])

        #2.- Extraer los IDs
        ids_recuperados = [c.id for c in chunks]

        #3.- Calculamos las métricas
        p = precision_at_k(ids_recuperados, caso["ids_relevantes"])
        r = recall_at_k(ids_recuperados, caso["ids_relevantes"])
        f1 = f1_score(p, r)

        #4.- Agregar esas métricas a los resultados
        resultados.append({
            "pregunta": caso["pregunta"],
            "ids_recuperados": ids_recuperados,
            "precision": p,
            "recall": r,
            "f1": f1
        })
    
    return resultados

def guardar_reporte(ruta_archivo: str, resultados: list[dict], k: int, chunk_size: int = 200, chunk_overlap: int = 30):
    """Guarda el registro en un .txt para compararlo cuando cambies k o chunk_size."""
    with open(ruta_archivo, "w", encoding="utf-8") as archivo:
        archivo.write(f"Fecha: {date.today()}\n")
        archivo.write(f"Configuracion: k={k}, chunk_size={chunk_size}, chunk_overlap={chunk_overlap}\n\n")

        for r in resultados:
            recall_txt = "n/a" if r["recall"] is None else f"{r['recall']:.2f}"
            archivo.write(f"P={r['precision']:.2f} | R={recall_txt} | F1={r['f1']:.2f} | {r['pregunta']}\n")
    print(f"\nReporte guardado en '{ruta_archivo}'")

if __name__ == "__main__":
    CARPETA_DB = "vectorstore_ejemplo"
    K = 3
    vs = cargar_vectorstore(CARPETA_DB)

    pregunta = "Cuáles son los errores de credenciales inválidas?"
    ids_relevantes = {"a4bc644f-ffa9-4219-94b2-5fd7cff518be", "5cf57a48-f1b4-4f6a-b8d3-b5e2760a9e37", "25a1d55b-6bed-4aa2-bc7c-db4e718964ca"}

    retriever = vs.as_retriever(search_kwargs={"k": K})
    chunks = retriever.invoke(pregunta) #Consulta
    print(chunks)
    ids_recuperados = [c.id for c in chunks]

    precision = precision_at_k(ids_recuperados, ids_relevantes)
    print("Precision: ", precision)

    exhaustividad = recall_at_k(ids_recuperados, ids_relevantes)
    print("Exhaustividad: ", exhaustividad)

    f1 = f1_score(precision, exhaustividad)
    print("F1 Score: ", f1)

    casos_evaluacion = [
        # Caso 1: Cubre la Sección 1 del manual (Política de Reintentos ante TimeoutError)
        {
            "pregunta": "¿Cuántos intentos hace el cliente ante un TimeoutError y cuánto espera entre cada uno?",
            "ids_relevantes": {
                "d80b09d0-fa3c-4a81-a5d5-4def5593e9bc", # Explica TimeoutError y códigos 502, 503, 504
                "754a40d8-a796-42d3-bb07-0b60f523e472", # Indica el máximo de 3 intentos y espera exponencial
                "f2024a2e-f59b-4884-93ea-108f9f9318d5", # Detalla los segundos (2s, 4s, 8s)
            }
        },
        # Caso 2: Cubre la Sección 2 del manual (Errores de Autenticación y cómo resolverlos)
        {
            "pregunta": "¿Qué ocurre cuando hay un error 401 o 403 de credenciales inválidas y cómo se soluciona?",
            "ids_relevantes": {
                "a4bc644f-ffa9-4219-94b2-5fd7cff518be", # Indica que 401/403 no reintentan y fallan de inmediato
                "5cf57a48-f1b4-4f6a-b8d3-b5e2760a9e37", # Indica que arroja AuthenticationError
                "25a1d55b-6bed-4aa2-bc7c-db4e718964ca", # Solución: revisar API_KEY y vigencia de 24h
            }
        },
        # Caso 3: Cubre la Sección 3 del manual (Límites de Tasa / Rate Limiting 429)
        {
            "pregunta": "¿Cuál es el límite de peticiones por minuto y qué pasa si se excede?",
            "ids_relevantes": {
                "c3541421-7fb7-42b6-adfa-65807aaa9f2f", # Máximo 60 peticiones por minuto por clave
                "719b5942-1b17-46c8-a798-86adbc9fd1dc", # El servidor responde con HTTP 429 Too Many Requests
                "f5ae78c8-c4f6-49bf-b264-80b13c45d486", # La cabecera Retry-After indica los segundos de pausa
            }
        },
        # Caso 4: Cubre la Sección 4 del manual (Control de Costos y Créditos de Sesión)
        {
            "pregunta": "¿Cuántas unidades de crédito consumen las consultas de lectura y las de escritura?",
            "ids_relevantes": {
                "2a846732-70c2-4c19-9a91-d7f3d6b73a6f", # Solo lectura: 1 unidad por cada 100 registros
                "af3c5063-277a-40f3-84dc-a7af55a38553", # Escritura y actualización: 5 unidades por transacción
            }
        },
    ]

    resultados = evaluar_recuperacion(retriever, casos_evaluacion, 3)
    print(resultados)

    guardar_reporte("resultados_evaluacion_rag.txt", resultados, 3)

    """
    Precisión: Fórmula: Verdaderos Positivos / (Verdaderos Positivos + Falsos Positivos) 

    Exhaustividad (recall ) :
    Fórmula: Verdaderos Positivos / (Verdaderos Positivos + Falsos Negativos)
    """