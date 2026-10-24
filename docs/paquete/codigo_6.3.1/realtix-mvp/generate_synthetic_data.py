"""
Generación de la base de datos sintética del sistema multiagente de IA
(Fase 3, actividad 6.3.1).

Este script reemplaza, para efectos de desarrollo y evaluación, el acceso a
datos reales de Realtix/RealSit (cubiertos por el acuerdo de confidencialidad
y por RNF-04). Genera contribuyentes, predios, obligaciones tributarias
(IPU e ICA) e historial de pagos con distribuciones realistas para el
municipio piloto (Bogotá D.C.).

Uso:
    python generate_synthetic_data.py [--contribuyentes N] [--seed S]
"""

import argparse
import random
import uuid
from datetime import date, datetime, timedelta

from faker import Faker

from database import reset_database

fake = Faker("es_CO")

# Actividades económicas y tarifa ICA representativa (por mil sobre ingresos
# brutos), a modo de catálogo simplificado para el MVP.
ACTIVIDADES_ICA = [
    ("comercio_al_por_menor", 6.9, "Comercio al por menor"),
    ("servicios_profesionales", 9.6, "Servicios profesionales y consultoría"),
    ("restaurantes_y_bares", 6.9, "Expendio de alimentos y bebidas"),
    ("construccion", 5.5, "Actividades de construcción"),
    ("tecnologia_software", 9.6, "Desarrollo de software y TI"),
    ("industria_manufacturera", 4.14, "Industria manufacturera"),
    ("salud_privada", 6.0, "Servicios de salud privados"),
    ("educacion_privada", 4.14, "Servicios educativos privados"),
]

VIGENCIA_ACTUAL = 2026


def tarifa_ipu_por_mil(avaluo: int) -> float:
    """Tarifa progresiva simplificada, creciente según el avalúo catastral.

    ADVERTENCIA (H-06): el rango general vigente es de 5 a 16 por mil del
    avalúo (artículo 23 de la Ley 1450 de 2011, que modificó el artículo 4 de
    la Ley 44 de 1990). El tramo de 4 por mil queda por debajo de ese rango y
    se corrige en el Paso 2, cuando la tabla de tarifas pase a
    src/services/tarifas.py."""
    if avaluo < 150_000_000:
        return 4.0
    if avaluo < 400_000_000:
        return 6.5
    if avaluo < 900_000_000:
        return 9.0
    return 12.0


def generar_contribuyentes(n: int) -> list[dict]:
    contribuyentes = []
    for _ in range(n):
        es_juridica = random.random() < 0.35
        if es_juridica:
            id_c = f"NIT-{fake.numerify('##########')}"
            nombre = fake.company()
            tipo_doc = "NIT"
            actividad = random.choice(ACTIVIDADES_ICA)[0]
        else:
            id_c = f"CC-{fake.numerify('#########')}"
            nombre = fake.name()
            tipo_doc = "CC"
            # ~20% de las personas naturales también declara ICA (independientes)
            actividad = random.choice(ACTIVIDADES_ICA)[0] if random.random() < 0.2 else None
        contribuyentes.append({
            "id_contribuyente": id_c,
            "tipo_documento": tipo_doc,
            "numero_documento": id_c.split("-")[1],
            "nombre": nombre,
            "actividad_economica": actividad,
        })
    return contribuyentes


def generar_predios(contribuyentes: list[dict]) -> list[dict]:
    predios = []
    for c in contribuyentes:
        num_predios = 1 if random.random() < 0.8 else 2
        for _ in range(num_predios):
            avaluo = random.randint(60, 1_600) * 1_000_000 // 10 * 10
            predios.append({
                "matricula_catastral": f"50C-{fake.numerify('#######')}",
                "id_contribuyente": c["id_contribuyente"],
                "direccion": fake.address().replace("\n", ", "),
                "avaluo_catastral": avaluo,
                "municipio": "Bogotá D.C.",
            })
    return predios


def generar_obligaciones_y_pagos(predios: list[dict], contribuyentes_by_id: dict):
    obligaciones, pagos = [], []
    hoy = date(2026, 9, 12)

    for predio in predios:
        # --- IPU: vigencia actual + una anterior, para tener historial ---
        for vigencia in (VIGENCIA_ACTUAL - 1, VIGENCIA_ACTUAL):
            tarifa = tarifa_ipu_por_mil(predio["avaluo_catastral"])
            valor = round(predio["avaluo_catastral"] * tarifa / 1000)
            fecha_limite = date(vigencia, 6, 30)
            id_obl = f"OBL-{uuid.uuid4().hex[:10].upper()}"

            if vigencia < VIGENCIA_ACTUAL or random.random() < 0.55:
                estado = "AL_DIA"
            elif fecha_limite < hoy:
                estado = "VENCIDO"
            else:
                estado = "PENDIENTE"

            obligaciones.append({
                "id_obligacion": id_obl, "matricula_catastral": predio["matricula_catastral"],
                "tipo_tributo": "IPU", "vigencia_fiscal": vigencia,
                "valor_liquidado": valor, "estado_pago": estado,
                "fecha_limite_pago": fecha_limite.isoformat(),
            })
            if estado == "AL_DIA":
                fecha_pago = fecha_limite - timedelta(days=random.randint(5, 90))
                pagos.append({
                    "id_pago": f"PAG-{uuid.uuid4().hex[:10].upper()}", "id_obligacion": id_obl,
                    "fecha_pago": fecha_pago.isoformat(), "valor_pagado": valor,
                    "medio_pago": random.choice(["PSE", "Corresponsal bancario", "Ventanilla"]),
                })

        # --- ICA: solo si el contribuyente dueño del predio declara actividad ---
        contrib = contribuyentes_by_id[predio["id_contribuyente"]]
        if contrib["actividad_economica"]:
            tarifa_info = next(a for a in ACTIVIDADES_ICA if a[0] == contrib["actividad_economica"])
            ingresos_brutos = random.randint(40, 900) * 1_000_000
            valor = round(ingresos_brutos * tarifa_info[1] / 1000)
            fecha_limite = date(VIGENCIA_ACTUAL, 1, 20)
            id_obl = f"OBL-{uuid.uuid4().hex[:10].upper()}"
            estado = "AL_DIA" if random.random() < 0.6 else ("VENCIDO" if fecha_limite < hoy else "PENDIENTE")
            obligaciones.append({
                "id_obligacion": id_obl, "matricula_catastral": predio["matricula_catastral"],
                "tipo_tributo": "ICA", "vigencia_fiscal": VIGENCIA_ACTUAL,
                "valor_liquidado": valor, "estado_pago": estado,
                "fecha_limite_pago": fecha_limite.isoformat(),
            })
            if estado == "AL_DIA":
                fecha_pago = fecha_limite - timedelta(days=random.randint(1, 15))
                pagos.append({
                    "id_pago": f"PAG-{uuid.uuid4().hex[:10].upper()}", "id_obligacion": id_obl,
                    "fecha_pago": fecha_pago.isoformat(), "valor_pagado": valor,
                    "medio_pago": random.choice(["PSE", "Corresponsal bancario"]),
                })
    return obligaciones, pagos


def poblar_base(n_contribuyentes: int, seed: int | None):
    if seed is not None:
        random.seed(seed)
        Faker.seed(seed)

    conn = reset_database()

    contribuyentes = generar_contribuyentes(n_contribuyentes)
    predios = generar_predios(contribuyentes)
    contribuyentes_by_id = {c["id_contribuyente"]: c for c in contribuyentes}
    obligaciones, pagos = generar_obligaciones_y_pagos(predios, contribuyentes_by_id)

    conn.executemany(
        "INSERT INTO contribuyente VALUES (:id_contribuyente, :tipo_documento, :numero_documento, :nombre, :actividad_economica)",
        contribuyentes,
    )
    conn.executemany(
        "INSERT INTO predio VALUES (:matricula_catastral, :id_contribuyente, :direccion, :avaluo_catastral, :municipio)",
        predios,
    )
    conn.executemany(
        "INSERT INTO obligacion_tributaria VALUES (:id_obligacion, :matricula_catastral, :tipo_tributo, :vigencia_fiscal, :valor_liquidado, :estado_pago, :fecha_limite_pago)",
        obligaciones,
    )
    conn.executemany(
        "INSERT INTO pago VALUES (:id_pago, :id_obligacion, :fecha_pago, :valor_pagado, :medio_pago)",
        pagos,
    )
    conn.executemany(
        "INSERT INTO tarifa_ica VALUES (?, ?, ?)",
        ACTIVIDADES_ICA,
    )
    conn.commit()

    print(f"Contribuyentes: {len(contribuyentes)}")
    print(f"Predios: {len(predios)}")
    print(f"Obligaciones tributarias: {len(obligaciones)}")
    print(f"Pagos registrados: {len(pagos)}")
    print(f"Base de datos: {conn.execute('PRAGMA database_list').fetchone()[2]}")
    conn.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Genera la base de datos sintética del sistema multiagente de IA.")
    parser.add_argument("--contribuyentes", type=int, default=150, help="Número de contribuyentes a generar (default: 150)")
    parser.add_argument("--seed", type=int, default=42, help="Semilla aleatoria para reproducibilidad (default: 42)")
    args = parser.parse_args()
    poblar_base(args.contribuyentes, args.seed)
