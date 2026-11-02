import json
from pathlib import Path


def pedir_valoracion(pregunta, opciones):
    while True:
        valor = input(pregunta).strip().lower()

        if valor in opciones:
            return valor

        print(
            "Escribe una de estas opciones:",
            ", ".join(opciones)
        )


def pedir_nota():
    while True:
        nota = input(
            "Justificación de tus valoraciones: "
        ).strip()

        if nota:
            return nota

        print("Debes escribir una justificación.")


def realizar_revision():
    raiz = Path(__file__).resolve().parents[1]

    ruta_resultados = (
        raiz / "docs" / "resultados_metricas.json"
    )

    ruta_revision = (
        raiz / "docs" / "revision_manual.json"
    )

    if ruta_revision.exists():
        raise FileExistsError(
            "Ya existe docs/revision_manual.json. "
            "Consérvalo o renómbralo antes de iniciar otra revisión."
        )

    with ruta_resultados.open(
        "r",
        encoding="utf-8-sig"
    ) as archivo:
        resultados = json.load(archivo)

    if len(resultados) < 20:
        raise ValueError(
            "La actividad requiere al menos veinte resultados. "
            f"El archivo contiene {len(resultados)}."
        )

    # Selección de la muestra indicada en el bloque 17.
    peores_casos = sorted(
        resultados,
        key=lambda caso: caso["f1"]
    )

    muestra_para_revisar = (
        peores_casos[:5] + peores_casos[-5:]
    )

    revision_manual = []

    for numero, caso in enumerate(
        muestra_para_revisar,
        start=1
    ):
        grupo = (
            "cinco F1 más bajos"
            if numero <= 5
            else "cinco F1 más altos"
        )

        print("\n" + "=" * 70)
        print(f"REVISIÓN {numero}/10")
        print("ID original:", caso["id"])
        print("Grupo:", grupo)
        print("Consulta:", caso["consulta"])
        print("Referencia:", caso["referencia"])
        print("Respuesta:", caso["respuesta"])
        print(f"F1: {caso['f1']:.3f}")

        print("\nLee los textos antes de valorar.")

        correccion_factual = pedir_valoracion(
            "Corrección factual [si/no/parcialmente]: ",
            ("si", "no", "parcialmente")
        )

        completitud = pedir_valoracion(
            "Completitud [si/no/parcialmente]: ",
            ("si", "no", "parcialmente")
        )

        contradiccion = pedir_valoracion(
            "Contradicción [si/no]: ",
            ("si", "no")
        )

        nota = pedir_nota()

        revision_manual.append({
            **caso,
            "correccion_factual": correccion_factual,
            "completitud": completitud,
            "contradiccion": contradiccion,
            "nota": nota,
        })

        # Guarda cada revisión terminada para conservar el avance.
        with ruta_revision.open(
            "w",
            encoding="utf-8"
        ) as archivo:
            json.dump(
                revision_manual,
                archivo,
                indent=2,
                ensure_ascii=False
            )

    print("\nRevisión de diez casos completada.")
    print("Archivo guardado:", ruta_revision)

    print(
        "\nAhora escribe docs/limites_metrica.md "
        "a partir de tus hallazgos."
    )


if __name__ == "__main__":
    realizar_revision()