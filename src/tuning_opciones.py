from importlib.metadata import version, PackageNotFoundError
from dotenv import load_dotenv
from google.genai import types
 
try:
    print("Modos de tuning disponibles:")
    for modo in types.TuningMode:
        print(" ", modo)

        #TuningMode.TUNING_MODE_FULL (Fine tuning completo): Toma el modelo entero y lo reentrena todo de sus parámetros originales usando los ejemplo que tú le des
        #TuningMode.TUNING_MODE_PEFT_ADAPTER (PEFT con Adapters): Congela el modelo original (no toca los parámetros) y entrena única un pequeño módulo nuevo (adapter) que se conecta con el modelo base.
 
    print()
    print("Tamaños de adapter disponibles (solo aplica a PEFT):")
    for tamanio in types.AdapterSize:
        print(" ", tamanio)
except AttributeError as e:
    raise SystemExit(f"Tu versión del SDK no expone este tipo: {e}. Actualiza con: pip install -U google-genai")

for campo in ["epoch_count", "learning_rate_multiplier", "batch_size"]:
    try:
        descripcion = types.CreateTuningJobConfig.model_fields[campo].description
        print(campo, "->", descripcion)
    except KeyError:
        print(campo, "-> este campo no existe en tu versión del SDK")

