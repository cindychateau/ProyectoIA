from dotenv import load_dotenv #importa variables de entorno
from langchain_text_splitters import RecursiveCharacterTextSplitter #función para dividir (chunking)
from langchain_google_genai import GoogleGenerativeAIEmbeddings #embedding de Gemini
from langchain_chroma import Chroma #Chroma = vector store

load_dotenv()

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
    #indexar_corpues(corpus=corpus, persist_directory=CARPETA_DB, chunk_size=250, chunk_overlap=35)

    vs = cargar_vectorstore(CARPETA_DB) #Cargar la carpeta para poder consultarla/actualizarla más adelante
    print("Chunks indexados: ", vs._collection.count()) #Imprime los chunks indexados

    datos = vs.get()
    print("IDs almacenados: ", datos["ids"])
    print("Chunks almacenados: ", datos["documents"])

    #eliminar_por_ids(["579517b3-b962-4d38-aaae-def944b4e486"])

    nueva_politica = ["Los envios internacionales tienen un tiempo estimado de entrega de 15 a 20 dias habiles."]
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





