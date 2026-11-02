from src.pipeline_limpieza import procesar_texto

def test_procesar_texto_normaliza_mayusculas_y_puntuacion():
    resultado = procesar_texto("El Cielo, es AZUL!")
    assert resultado == ["el", "cielo", "es", "azul"]

def test_procesar_texto_solo_puntuacion_devuelve_lista_vacia(): 
    resultado = procesar_texto("¡¡¡...!!!")  
    assert resultado == [] 