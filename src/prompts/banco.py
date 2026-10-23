BANCO_DE_PROMPT = [
    {
        "nombre": "estimar_respuesta_y_tiempo",
        "system_instruction": (
            "Responde únicamente con un JSON con las claves 'respuesta' (texto directo), "
            "'tiempo_estimado' (ej. 'Inmediato', '5-10 minutos'), 'nivel_complejidad' "
            "('Bajo', 'Medio' o 'Alto') y 'requiere_soporte_humano' (boolean)."
        ),
        "ejemplo_usuario": "¿Cómo solicito el reembolso de un pedido cancelado?",
        "claves_esperadas": [
            "respuesta",
            "tiempo_estimado",
            "nivel_complejidad",
            "requiere_soporte_humano",
        ],
        "response_schema": {
            "type": "OBJECT",
            "properties": {
                "respuesta": {"type": "STRING"},
                "tiempo_estimado": {"type": "STRING"},
                "nivel_complejidad": {"type": "STRING"},
                "requiere_soporte_humano": {"type": "BOOLEAN"},
            },
            "required": ["respuesta", "tiempo_estimado", "nivel_complejidad", "requiere_soporte_humano"],
        },
    },
    {
        "nombre": "extraer_entidades",
        "system_instruction": (
            "Extrae del texto las personas, los lugares y las organizaciones "
            "que se mencionen. Responde únicamente con un JSON con las claves "
            "'personas', 'lugares' y 'organizaciones', cada una con una lista "
            "de textos (vacía si no hay ninguno)."
        ),
        "ejemplo_usuario": (
            "Elena de Troya y Juana de Arco viajaron de Roma a Grecia para reunirse "
            "con la guerrilla."
        ),
        "claves_esperadas": ["personas", "lugares", "organizaciones"],
        "response_schema": {
            "type": "OBJECT",
            "properties": {
                "personas": {"type": "ARRAY", "items": {"type": "STRING"}},
                "lugares": {"type": "ARRAY", "items": {"type": "STRING"}},
                "organizaciones": {"type": "ARRAY", "items": {"type": "STRING"}},
            },
            "required": ["personas", "lugares", "organizaciones"],
        },
    },
]