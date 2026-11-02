# Límites de la métrica de evaluación

## Qué mide

La métrica compara las palabras de una respuesta con una referencia,
contando repeticiones después de limpiar y tokenizar ambos textos.
Reporta precisión, cobertura y F1.

## Modos de falla conocidos

- [Describe un problema encontrado en tu revisión.]
  Caso: [ID y consulta].
  Referencia: "[texto de referencia]".
  Respuesta: "[texto recibido]".
  F1: [valor calculado].
  Hallazgo: [explica qué detectaste al leer y qué no explica
  suficientemente el puntaje].

- [Repite la estructura para otros modos de falla observados.]

## Muestra revisada

Se revisaron [cantidad] casos de un conjunto de [cantidad]
respuestas generadas con consultar_modelo.

La muestra combina los cinco F1 más bajos y los cinco más altos.

Casos revisados: [IDs].
Fecha de revisión: [fecha].

Se aplicó la rúbrica de corrección factual, completitud
y contradicción, con una justificación por caso.

## Recomendación de uso

[Explica para qué comparación resulta útil esta métrica
en tu pipeline.]

[Indica qué respuestas necesitan revisión humana
y relaciona esa recomendación con los casos encontrados.]