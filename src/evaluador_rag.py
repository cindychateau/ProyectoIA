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
        {"pregunta": "", "ids_relavantes": {"ids1", "ids2"}},
        {"pregunta": "", "ids_relavantes": {"ids1", "ids2"}},
        {"pregunta": "", "ids_relavantes": {"ids1", "ids2"}},
        {"pregunta": "", "ids_relavantes": {"ids1", "ids2"}},
    ]

    """
    Precisión: Fórmula: Verdaderos Positivos / (Verdaderos Positivos + Falsos Positivos) 

    Exhaustividad (recall ) :
    Fórmula: Verdaderos Positivos / (Verdaderos Positivos + Falsos Negativos)
    """