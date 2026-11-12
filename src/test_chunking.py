from langchain_text_splitters import CharacterTextSplitter, RecursiveCharacterTextSplitter

texto = (
    "El cliente reintenta hasta 3 veces ante un TimeoutError, con espera creciente "
    "entre intento e intento.\n\n"
    "Los errores de autenticacion nunca se reintentan: fallan de inmediato con un "
    "ValueError, sin ninguna espera.\n\n"
    "El costo de cada llamada se acumula en una variable de sesion mientras el "
    "programa sigue corriendo."
)

#Chunking de tamaño fijo (CharacterTextSplitter)
print("****CHUNK FIJO****")
splitter_fijo = CharacterTextSplitter(separator="", chunk_size=110, chunk_overlap=0)
chunks_fijo = splitter_fijo.split_text(texto)

for i, chunk in enumerate(chunks_fijo):
    print(f"*** Chunk {i} ({len(chunk)} caracteres) ***")
    print(chunk)

print("****CHUNK RECURSIVO****")

#Chunking recursivo (RecursiveCharacterTextSplitter)
splitter_recursivo = RecursiveCharacterTextSplitter(chunk_size=400, chunk_overlap=20)
chunks_recursivo = splitter_recursivo.split_text(texto)

for i, chunk in enumerate(chunks_recursivo):
    print(f"*** Chunk {i} ({len(chunk)} caracteres) ***")
    print(chunk)