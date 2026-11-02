from cliente import consultar_modelo
from pipeline_limpieza import procesar_texto


consulta = "¿Qué es Python?"
referencia = "Python es un lenguaje de programación interpretado."
respuesta = consultar_modelo(consulta)

crudo_ref = referencia.split()
crudo_resp = respuesta.split()

comunes_crudo = set(crudo_ref) & set(crudo_resp)
pct_crudo = len(comunes_crudo) / len(set(crudo_ref))

tokens_ref = procesar_texto(referencia)
tokens_resp = procesar_texto(respuesta)

comunes = set(tokens_ref) & set(tokens_resp)
pct_proc = len(comunes) / len(set(tokens_ref))


print(f"[Caso 1] Coincidencia texto crudo: {pct_crudo:.1%}")
print(f"[Caso 1] Coincidencia texto procesado: {pct_proc:.1%}")