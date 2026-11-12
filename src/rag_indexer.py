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

    #Embedding
    embeddings = GoogleGenerativeAIEmbeddings(model="models/gemini-embedding-001")

    vector_store = Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        persist_directory=persist_directory
    )

    return vector_store

"""
Función que abre/carga la carpeta existente del disco para leerla. NO GASTO TOKENS
"""
def cargar_vectorstore(persist_directory):
    embeddings = GoogleGenerativeAIEmbeddings(model="models/gemini-embedding-001")
    return Chroma(persist_directory=persist_directory, embedding_function=embeddings)






# if __name__ == "__main__":
#     indexar_corpus(corpus="asdadasdasd", persist_directory="carpeta_vector", chunk_size=250, chunk_overlap=35)
