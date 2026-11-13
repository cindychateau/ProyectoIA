from dotenv import load_dotenv #importa variables de entorno
from langchain_text_splitters import RecursiveCharacterTextSplitter #función para dividir (chunking)
from langchain_google_genai import GoogleGenerativeAIEmbeddings #embedding de Gemini
from langchain_chroma import Chroma #Chroma = vector store

load_dotenv()
"""
Auditar localmente que no haya chunks vacíos ni duplicados antes de gastar tokens en embeddings
"""
def verificar_integridad(chunks, corpus_original):
    #Recorrer todos los chunks con su indice (i), quitamos espacios/saltos de línea
    #guardo lista de posiciones de cualquier fragmento que haya quedado en blanco
    vacios = [i for i, c in enumerate(chunks) if not c.page_content.strip()]

    #Extraigo el texto plano de cada objeto, lista
    textos = [c.page_content for c in chunks]

    #lista1 = ["manzana", "pera", "manzana", "uvas"]
    #set1 = ["manzana", "pera", "uvas"]

    #Set/Conjunto es una lista de valores únicos
    #Convierto la lista de textos en un set (para eliminar repetidos automáticamente), y si la longitud es distinta a la original significa que tenemos chunks iguales
    hay_duplicados = len(textos) != len(set(textos))

    if vacios:
        raise ValueError(f"Se detectaron chunks vacíos en los índices: {vacios}")
    if hay_duplicados:
        print("Advertencia: Se detectaron chunks duplicados en el corpus.")

    #Sumar el otal de caracteres de todos los chunks generados vs. el total de caracteres del corpus original
    total_chars_chunks = sum(len(c.page_content) for c in chunks)
    total_chars_corpus = sum(len(d) for d in corpus_original)

    print(f"Integridad OK | Chunks: {len(chunks)} | Caracteres (corpus/chunks): {total_chars_corpus}/{total_chars_chunks}")

"""
Recibir un corpus/texto dividirlo, calcular el embedding, y guardar el corpus en mi vector store
"""
def indexar_corpus(corpus, persist_directory, chunk_size=200, chunk_overlap=30):
    #Dividir en fragmentos más pequeños corpus/texto
    splitter = RecursiveCharacterTextSplitter( #Configuración para la división
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap
    )

    #División
    #chunks = splitter.create_documents(texts=corpus, metadatas=[{"origen": "manual.pdf", "pagina": 2}])
    chunks = splitter.create_documents(corpus) #create_documents: me permite agregar metadatos

    #Todo: generar ids y mandarlos

    verificar_integridad(chunks, corpus)

    #Embedding
    embeddings = GoogleGenerativeAIEmbeddings(model="models/gemini-embedding-001")

    #Si esta función recibe ids, actualizar los ids que ya existían y generar un nuevo chunk para aquellos que no
    #Si no envío ids, se generan de manera automática
    vector_store = Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        persist_directory=persist_directory
        #ids=["id1", "id2"]
    )

    return vector_store

"""
Función que abre/carga la carpeta existente del disco para leerla. NO GASTO TOKENS
"""
def cargar_vectorstore(persist_directory):
    embeddings = GoogleGenerativeAIEmbeddings(model="models/gemini-embedding-001")
    return Chroma(persist_directory=persist_directory, embedding_function=embeddings)

def eliminar_por_ids(vectorstore, ids_a_borrar):
    vectorstore.delete(ids=ids_a_borrar)

def agregar_documentos(vectorstore, nuevos_textos, prefijo_id, chunk_size=200, chunk_overlap=30):
    #doc_
    splitter = RecursiveCharacterTextSplitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
    nuevo_chunks = splitter.create_documents(nuevos_textos) #Lista de los fragmentos

    #Crear los ids
    ids_nuevos = [f"{prefijo_id}_{i}" for i in range(len(nuevo_chunks))] #["doc_0", "doc_1", "doc_2"]

    #ids_nuevos = []
    #for i in range(len(nuevo_chunks)):
    #   ids_nuevos.append(f"{prefijo_id}_{i}"")

    verificar_integridad(nuevo_chunks, nuevos_textos)

    try:
        vectorstore.add_documents(ids=ids_nuevos, documents=nuevo_chunks)
        #vectorstore.add_documents(nuevo_chunks, ids_nuevos)
        print(f"Agregados {len(nuevo_chunks)} chunks con el prefijo {prefijo_id}")
    except Exception as error:
        print("Error al agregrar nuevos documentos: ", error)

if __name__ == "__main__":
    #Constante
    CARPETA_DB = "vectorstore_ejemplo"

    corpus = [
        "El cliente reintenta hasta 3 veces ante un TimeoutError, con espera creciente.",
        "El costo de cada llamada se calcula a partir de totalTokenCount.",
        "Las pruebas unitarias del cliente usan mocks y corren en menos de un segundo.",
    ]

    #indexar_corpus(corpus, CARPETA_DB) #Almacenar el texto
    #indexar_corpus(corpus=corpus, persist_directory=CARPETA_DB, chunk_size=250, chunk_overlap=35)

    vs = cargar_vectorstore(CARPETA_DB) #Cargar la carpeta para poder consultarla/actualizarla más adelante
    print("Chunks indexados: ", vs._collection.count()) #Imprime los chunks indexados

    datos = vs.get()
    print("IDs almacenados: ", datos["ids"])
    print("Chunks almacenados: ", datos["documents"])

    #eliminar_por_ids(["579517b3-b962-4d38-aaae-def944b4e486"])

    nueva_politica = ["Los envíos nacionales tardan entre 5 y 10 días hábiles"]
    #agregar_documentos(vs, nueva_politica, "doc_nuevo", 150, 20)
    agregar_documentos(
        vectorstore=vs, 
        nuevos_textos=nueva_politica, 
        prefijo_id="doc_nuevo", 
        chunk_size=150, 
        chunk_overlap=20
    )

    datos = vs.get()
    print("IDs almacenados: ", datos["ids"])
    print("Chunks almacenados: ", datos["documents"])





